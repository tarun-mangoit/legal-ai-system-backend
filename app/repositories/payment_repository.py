import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from datetime import datetime
from app.models.payment import Payment, PaymentTransaction, Invoice, Refund

class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Payment Operations
    async def create_payment(self, data: dict) -> Payment:
        payment = Payment(**data)
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_payment(self, payment_id: uuid.UUID) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalars().first()

    async def get_payment_by_gateway_order(self, gateway_order_id: str) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.gateway_order_id == gateway_order_id))
        return result.scalars().first()

    async def get_payments_by_client(self, client_id: uuid.UUID) -> List[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.client_id == client_id))
        return list(result.scalars().all())

    async def get_payments_by_case(self, case_id: uuid.UUID) -> List[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.case_id == case_id))
        return list(result.scalars().all())
        
    async def get_all_payments(self) -> List[Payment]:
        result = await self.db.execute(select(Payment))
        return list(result.scalars().all())

    async def get_payment_history(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        client_id: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ):
        query = select(Payment)
        
        if client_id:
            query = query.where(Payment.client_id == client_id)
            
        if status:
            query = query.where(Payment.status == status)
            
        if from_date:
            query = query.where(Payment.created_at >= from_date)
            
        if to_date:
            query = query.where(Payment.created_at <= to_date)
            
        if q:
            query = query.where(
                or_(
                    Payment.gateway_order_id.ilike(f"%{q}%"),
                    Payment.gateway_payment_id.ilike(f"%{q}%")
                )
            )
            
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total

    async def update_payment(self, payment_id: uuid.UUID, data: dict) -> Optional[Payment]:
        await self.db.execute(
            update(Payment).where(Payment.id == payment_id).values(**data)
        )
        await self.db.commit()
        return await self.get_payment(payment_id)

    # Transaction Operations
    async def create_transaction(self, data: dict) -> PaymentTransaction:
        transaction = PaymentTransaction(**data)
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    # Invoice Operations
    async def create_invoice(self, data: dict) -> Invoice:
        invoice = Invoice(**data)
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice
        
    async def get_invoice(self, invoice_id: uuid.UUID) -> Optional[Invoice]:
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        return result.scalars().first()
        
    async def get_invoice_by_payment(self, payment_id: uuid.UUID) -> Optional[Invoice]:
        result = await self.db.execute(select(Invoice).where(Invoice.payment_id == payment_id))
        return result.scalars().first()
        
    async def get_all_invoices(self) -> List[Invoice]:
        result = await self.db.execute(select(Invoice))
        return list(result.scalars().all())
        
    async def update_invoice(self, invoice_id: uuid.UUID, data: dict) -> Optional[Invoice]:
        await self.db.execute(
            update(Invoice).where(Invoice.id == invoice_id).values(**data)
        )
        await self.db.commit()
        return await self.get_invoice(invoice_id)

    # Refund Operations
    async def create_refund(self, data: dict) -> Refund:
        refund = Refund(**data)
        self.db.add(refund)
        await self.db.commit()
        await self.db.refresh(refund)
        return refund
        
    async def get_refunds_by_payment(self, payment_id: uuid.UUID) -> List[Refund]:
        result = await self.db.execute(select(Refund).where(Refund.payment_id == payment_id))
        return list(result.scalars().all())
        
    async def update_refund(self, refund_id: uuid.UUID, data: dict) -> Optional[Refund]:
        await self.db.execute(
            update(Refund).where(Refund.id == refund_id).values(**data)
        )
        await self.db.commit()
        result = await self.db.execute(select(Refund).where(Refund.id == refund_id))
        return result.scalars().first()
