import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.payment import Refund, PaymentStatus
from app.repositories.payment_repository import PaymentRepository
from app.services.gateway_service import GatewayService
from app.services.notification_events import notification_events

class RefundService:
    def __init__(self, db: AsyncSession, gateway: GatewayService):
        self.repository = PaymentRepository(db)
        self.gateway = gateway

    async def initiate_refund(self, payment_id: uuid.UUID, amount: float = None, reason: str = "Customer Request") -> Refund:
        payment = await self.repository.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        if payment.status not in [PaymentStatus.SUCCESS, PaymentStatus.PARTIALLY_REFUNDED]:
            raise HTTPException(status_code=400, detail="Payment cannot be refunded")

        # Initiate refund with Gateway
        try:
            refund_response = self.gateway.process_refund(payment.gateway_payment_id, amount)
            
            # Save refund record
            refund_data = {
                "payment_id": payment.id,
                "refund_amount": amount if amount else payment.amount,
                "refund_reason": reason,
                "gateway_refund_id": refund_response.get("id"),
                "status": "COMPLETED"
            }
            
            refund = await self.repository.create_refund(refund_data)
            
            # Update Payment status
            new_status = PaymentStatus.PARTIALLY_REFUNDED if amount and amount < payment.amount else PaymentStatus.REFUNDED
            await self.repository.update_payment(payment.id, {"status": new_status})
            
            # Log Transaction
            await self.repository.create_transaction({
                "payment_id": payment.id,
                "status": "REFUND_COMPLETED",
                "amount": refund_data["refund_amount"],
                "gateway_response": str(refund_response)
            })
            
            # Trigger notification
            try:
                await notification_events.handle_refund_processed(
                    db=self.repository.session,
                    user_id=str(payment.client_id),
                    amount=float(refund_data["refund_amount"])
                )
            except Exception as e:
                import logging
                logging.error(f"Failed to trigger refund notification: {e}")
            
            return refund
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Refund failed: {str(e)}")
