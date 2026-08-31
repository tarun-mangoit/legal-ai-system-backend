import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/legal_ai"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, case_number FROM cases LIMIT 5"))
        cases = result.fetchall()
        print("Cases:")
        for c in cases:
            print(f"  {c.id} - {c.case_number}")
            docs_res = await session.execute(text("SELECT id, original_filename, is_deleted FROM case_documents WHERE case_id = :case_id"), {"case_id": c.id})
            docs = docs_res.fetchall()
            print(f"    Documents ({len(docs)}):")
            for d in docs:
                print(f"      {d.id} - {d.original_filename} (deleted: {d.is_deleted})")
                summ_res = await session.execute(text("SELECT id, summary FROM document_summaries WHERE document_id = :doc_id"), {"doc_id": d.id})
                summs = summ_res.fetchall()
                print(f"        Summaries: {len(summs)}")

if __name__ == "__main__":
    asyncio.run(main())
