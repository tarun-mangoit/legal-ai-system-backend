import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from typing import List, Optional
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService
from app.services.invoice_service import InvoiceService
from app.services.refund_service import RefundService
from app.services.gateway_service import GatewayService
from app.services.pdf_service import PDFService
from app.services.storage.local import LocalStorageProvider
from app.schemas.payment import (
    OrderCreateRequest, PaymentVerifyRequest, RefundRequest, 
    PaymentResponse, InvoiceResponse, RefundResponse
)
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

def get_services(db: AsyncSession = Depends(get_db)):
    gateway = GatewayService()
    storage = LocalStorageProvider()
    pdf_service = PDFService(storage)
    invoice_service = InvoiceService(db, pdf_service)
    payment_service = PaymentService(db, gateway, invoice_service)
    refund_service = RefundService(db, gateway)
    return {
        "payment": payment_service,
        "invoice": invoice_service,
        "refund": refund_service,
        "gateway": gateway
    }

@router.post("/create-order", response_model=PaymentResponse)
async def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services)
):
    return await services["payment"].create_order(
        case_id=request.case_id,
        client_id=current_user.id,
        amount=request.amount
    )

@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    request: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services)
):
    return await services["payment"].verify_payment(
        payment_id=request.payment_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_order_id=request.razorpay_order_id,
        razorpay_signature=request.razorpay_signature
    )

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    services: dict = Depends(get_services)
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    body = await request.body()
    payload = await request.json()
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "dummy_webhook_secret")
    
    is_valid = services["gateway"].verify_webhook_signature(body.decode('utf-8'), x_razorpay_signature, secret)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
    await services["payment"].handle_webhook(payload, x_razorpay_signature, secret)
    return {"status": "ok"}

@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    client_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services),
    db: AsyncSession = Depends(get_db)
):
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    
    target_id: Optional[str] = str(current_user.id)
    if role and role.name.lower() == "admin":
        target_id = client_id # Can be None, which fetches all payments
    
    print(f"DEBUG payments/history: role={role.name if role else None}, current_user={current_user.id}, client_id={client_id}, target_id={target_id}")
        
    import uuid
    parsed_target_id = uuid.UUID(target_id) if target_id else None
    return await services["payment"].get_payment_history(parsed_target_id)

@router.post("/refund", response_model=RefundResponse)
async def request_refund(
    request: RefundRequest,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services)
):
    return await services["refund"].initiate_refund(
        payment_id=request.payment_id,
        amount=request.amount,
        reason=request.reason
    )

@router.get("/invoice/{payment_id}", response_model=InvoiceResponse)
async def get_invoice(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services)
):
    invoice = await services["payment"].repository.get_invoice_by_payment(payment_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/invoice/download/{payment_id}")
async def download_invoice(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    services: dict = Depends(get_services)
):
    invoice = await services["payment"].repository.get_invoice_by_payment(payment_id)
    if not invoice or not invoice.pdf_path:
        raise HTTPException(status_code=404, detail="Invoice PDF not found")
        
    full_path = invoice.pdf_path
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File missing on disk")
        
    return FileResponse(full_path, media_type="application/pdf", filename=f"invoice_{invoice.invoice_number}.pdf")
