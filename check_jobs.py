import asyncio
from app.database.session import AsyncSessionLocal
from app.models.job_tracking import OCRJob, AIJob
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        ocr = await session.execute(select(OCRJob).order_by(OCRJob.created_at.desc()).limit(1))
        ai = await session.execute(select(AIJob).order_by(AIJob.created_at.desc()).limit(1))
        
        ocr_job = ocr.scalars().first()
        ai_job = ai.scalars().first()
        
        print(f"Latest OCR Job: {ocr_job.status if ocr_job else 'None'} | Error: {ocr_job.error_message if ocr_job else 'None'}")
        print(f"Latest AI Job:  {ai_job.status if ai_job else 'None'} | Error: {ai_job.error_message if ai_job else 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
