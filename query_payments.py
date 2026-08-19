import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.payment import Payment

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(Payment))
        payments = result.scalars().all()
        print(f"Total payments in DB: {len(payments)}")
        for p in payments:
            print(f"Payment ID: {p.id}, Client ID: {p.client_id}, Amount: {p.amount}")

asyncio.run(main())
