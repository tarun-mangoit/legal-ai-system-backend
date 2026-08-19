import asyncio
from app.database.session import AsyncSessionLocal
from app.models.job_tracking import OCRJob
from app.models.case_document import CaseDocument
from app.tasks.document_tasks import process_document_pipeline
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OCRJob).where(OCRJob.status == 'PENDING'))
        jobs = result.scalars().all()
        
        for job in jobs:
            doc_result = await session.execute(select(CaseDocument).where(CaseDocument.id == job.document_id))
            doc = doc_result.scalars().first()
            if doc:
                print(f"Retriggering task for Document ID: {job.document_id}")
                process_document_pipeline.delay(str(job.document_id), str(doc.case_id))

if __name__ == "__main__":
    asyncio.run(main())
