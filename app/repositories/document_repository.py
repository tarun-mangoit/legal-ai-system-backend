from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from ..models.case_document import CaseDocument
import uuid

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document_data: dict) -> CaseDocument:
        document = CaseDocument(**document_data)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[CaseDocument]:
        result = await self.session.execute(
            select(CaseDocument)
            .options(selectinload(CaseDocument.case))
            .where(CaseDocument.id == document_id)
        )
        return result.scalars().first()

    async def list_by_case(self, case_id: uuid.UUID, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[CaseDocument]:
        query = select(CaseDocument).where(CaseDocument.case_id == case_id)
        if not include_deleted:
            query = query.where(CaseDocument.is_deleted == False)
            
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete(self, document_id: uuid.UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document and not document.is_deleted:
            document.is_deleted = True
            await self.session.commit()
            return True
        return False

    async def restore(self, document_id: uuid.UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document and document.is_deleted:
            document.is_deleted = False
            await self.session.commit()
            return True
        return False
        
    async def find_by_hash(self, case_id: uuid.UUID, sha256_hash: str) -> Optional[CaseDocument]:
        result = await self.session.execute(
            select(CaseDocument).where(
                and_(
                    CaseDocument.case_id == case_id,
                    CaseDocument.sha256_hash == sha256_hash,
                    CaseDocument.is_deleted == False
                )
            )
        )
        return result.scalars().first()

    async def get_all_documents_with_status(self, skip: int = 0, limit: int = 100, advocate_id: Optional[uuid.UUID] = None, client_id: Optional[uuid.UUID] = None) -> List[tuple]:
        from ..models.job_tracking import AIJob
        from ..models.case import Case
        from sqlalchemy.orm import joinedload
        query = (
            select(CaseDocument, AIJob.status)
            .outerjoin(AIJob, CaseDocument.id == AIJob.document_id)
            .join(Case, CaseDocument.case_id == Case.id)
            .options(
                joinedload(CaseDocument.case).joinedload(Case.client),
                joinedload(CaseDocument.case).joinedload(Case.advocate)
            )
            .where(CaseDocument.is_deleted == False)
        )
        
        if advocate_id:
            query = query.where(Case.advocate_id == advocate_id)
        if client_id:
            query = query.where(Case.client_id == client_id)
            
        query = query.order_by(CaseDocument.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.all()
