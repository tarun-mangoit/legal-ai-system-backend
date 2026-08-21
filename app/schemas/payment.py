from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
from app.models.payment import PaymentStatus

class OrderCreateRequest(BaseModel):
    case_id: uuid.UUID
    amount: float

class PaymentVerifyRequest(BaseModel):
    payment_id: uuid.UUID
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

class RefundRequest(BaseModel):
    payment_id: uuid.UUID
    amount: Optional[float] = None
    reason: Optional[str] = "Customer Request"

class PaymentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    client_id: uuid.UUID
    amount: float
    currency: str
    status: PaymentStatus
    gateway_order_id: Optional[str]
    gateway_payment_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    invoice_number: str
    invoice_date: datetime
    subtotal: float
    tax: float
    discount: float
    total: float
    status: str
    pdf_path: Optional[str]

    class Config:
        from_attributes = True

class RefundResponse(BaseModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    refund_amount: float
    refund_reason: Optional[str]
    gateway_refund_id: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedPaymentResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int
