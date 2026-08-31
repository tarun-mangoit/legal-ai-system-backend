import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.config import settings
from app.models.job_tracking import OCRJob, AIJob
from app.models.ai_summary import AISummary

async def fix():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all summaries
        result = await session.execute(select(AISummary))
        summaries = result.scalars().all()
        
        for summary in summaries:
            doc_id = summary.document_id
            
            # Update OCR job
            await session.execute(update(OCRJob).where(OCRJob.document_id == doc_id).values(status='COMPLETED'))
            
            # Update AI job
            await session.execute(update(AIJob).where(AIJob.document_id == doc_id).values(status='COMPLETED'))
            
        await session.commit()
        print(f"Fixed {len(summaries)} stuck documents!")

asyncio.run(fix())
