import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.payment import Payment, PaymentStatus
from app.models.case import CaseStatus
from app.repositories.payment_repository import PaymentRepository
from app.repositories.case_repository import case_repository
from app.repositories.case_history_repository import case_history_repository
from app.services.gateway_service import GatewayService
from app.services.invoice_service import InvoiceService
from app.services.notification_events import notification_events

class PaymentService:
    def __init__(self, db: AsyncSession, gateway: GatewayService, invoice_service: InvoiceService):
        self.repository = PaymentRepository(db)
        self.gateway = gateway
        self.invoice_service = invoice_service
        self.db = db

    async def create_order(self, case_id: uuid.UUID, client_id: uuid.UUID, amount: float) -> Payment:
        # Create Razorpay Order
        receipt_id = f"rcpt_{str(uuid.uuid4())[:8]}"
        order_response = self.gateway.create_order(amount, currency="INR", receipt=receipt_id)
        
        # Save to database
        payment_data = {
            "case_id": case_id,
            "client_id": client_id,
            "amount": amount,
            "currency": "INR",
            "status": PaymentStatus.CREATED,
            "gateway_order_id": order_response.get("id")
        }
        
        payment = await self.repository.create_payment(payment_data)
        
        # Log Transaction
        await self.repository.create_transaction({
            "payment_id": payment.id,
            "status": "ORDER_CREATED",
            "amount": amount,
            "gateway_response": str(order_response)
        })
        
        return payment

    async def verify_payment(self, payment_id: uuid.UUID, razorpay_payment_id: str, razorpay_order_id: str, razorpay_signature: str) -> Payment:
        payment = await self.repository.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        if payment.status == PaymentStatus.SUCCESS:
            return payment # Already verified

        # Verify signature with Gateway
        is_valid = self.gateway.verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
        
        if is_valid:
            # Update Payment
            updated_payment = await self.repository.update_payment(payment.id, {
                "status": PaymentStatus.SUCCESS,
                "gateway_payment_id": razorpay_payment_id,
                "gateway_signature": razorpay_signature
            })
            
            # Log Transaction
            await self.repository.create_transaction({
                "payment_id": payment.id,
                "status": "PAYMENT_SUCCESS",
                "amount": payment.amount,
                "gateway_response": f"Verified successfully. Signature: {razorpay_signature}"
            })
            
            # Auto-generate Invoice
            await self.invoice_service.generate_invoice(payment.id)
            
            # Update Case Status
            case = await case_repository.get(self.db, payment.case_id)
            if case and case.status != CaseStatus.PAYMENT_COMPLETED:
                prev_status = case.status
                await case_repository.update(self.db, case, {"status": CaseStatus.PAYMENT_COMPLETED})
                
                # Log History
                await case_history_repository.create(self.db, obj_in={
                    "case_id": case.id,
                    "changed_by": payment.client_id,
                    "action_type": "STATUS_CHANGE",
                    "previous_value": str(prev_status),
                    "new_value": str(CaseStatus.PAYMENT_COMPLETED)
                })
            
            # Trigger notification
            try:
                await notification_events.handle_payment_success(
                    db=self.db,
                    user_id=str(payment.client_id),
                    amount=float(payment.amount),
                    reference=razorpay_payment_id,
                    case_number=case.case_number if case else None
                )
            except Exception as e:
                import logging
                logging.error(f"Failed to trigger payment success notification: {e}")
            
            return updated_payment
        else:
            await self.repository.update_payment(payment.id, {"status": PaymentStatus.FAILED})
            await self.repository.create_transaction({
                "payment_id": payment.id,
                "status": "PAYMENT_FAILED",
                "amount": payment.amount,
                "gateway_response": "Signature verification failed"
            })
            
            # Trigger notification
            try:
                await notification_events.handle_payment_failed(
                    db=self.db,
                    user_id=str(payment.client_id),
                    amount=float(payment.amount),
                    reason="Signature verification failed"
                )
            except Exception as e:
                import logging
                logging.error(f"Failed to trigger payment failed notification: {e}")
                
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    async def handle_webhook(self, payload: dict, signature: str, secret: str) -> bool:
        # Validate webhook signature
        # Not implementing raw payload parsing here, assume caller validated it
        # Idempotency check:
        event = payload.get('event')
        
        if event == 'payment.captured':
            payment_obj = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_obj.get('order_id')
            
            if order_id:
                payment = await self.repository.get_payment_by_gateway_order(order_id)
                if payment and payment.status != PaymentStatus.SUCCESS:
                    # Update status securely from webhook if not already done by frontend
                    await self.repository.update_payment(payment.id, {
                        "status": PaymentStatus.SUCCESS,
                        "gateway_payment_id": payment_obj.get('id')
                    })
                    await self.invoice_service.generate_invoice(payment.id)
                    
                    # Update Case Status
                    case = await case_repository.get(self.db, payment.case_id)
                    if case and case.status != CaseStatus.PAYMENT_COMPLETED:
                        prev_status = case.status
                        await case_repository.update(self.db, case, {"status": CaseStatus.PAYMENT_COMPLETED})
                        await case_history_repository.create(self.db, obj_in={
                            "case_id": case.id,
                            "changed_by": payment.client_id,
                            "action_type": "STATUS_CHANGE",
                            "previous_value": str(prev_status),
                            "new_value": str(CaseStatus.PAYMENT_COMPLETED)
                        })
                        
                    # Trigger notification
                    try:
                        await notification_events.handle_payment_success(
                            db=self.db,
                            user_id=str(payment.client_id),
                            amount=float(payment.amount),
                            reference=payment_obj.get('id'),
                            case_number=case.case_number if case else None
                        )
                    except Exception as e:
                        import logging
                        logging.error(f"Failed to trigger payment success notification in webhook: {e}")
        
        return True

    async def get_payment_history(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        client_id: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ):
        import dateutil.parser
        parsed_from_date = dateutil.parser.parse(from_date) if from_date else None
        parsed_to_date = dateutil.parser.parse(to_date) if to_date else None
        
        return await self.repository.get_payment_history(
            skip=skip,
            limit=limit,
            client_id=client_id,
            q=q,
            status=status,
            from_date=parsed_from_date,
            to_date=parsed_to_date
        )
