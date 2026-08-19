import asyncio
from app.database.session import AsyncSessionLocal
from app.models.legal_opinion import LegalOpinion
from sqlalchemy.future import select

async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(LegalOpinion))
        opinions = result.scalars().all()
        print("TOTAL OPINIONS:", len(opinions))
        for op in opinions:
            print(op.id, op.case_id)

asyncio.run(test())
