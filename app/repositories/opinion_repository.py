import uuid
from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models.legal_opinion import LegalOpinion, OpinionRevision, OpinionComment, OpinionStatus

class LegalOpinionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, opinion_id: uuid.UUID) -> Optional[LegalOpinion]:
        stmt = select(LegalOpinion).options(
            joinedload(LegalOpinion.revisions),
            joinedload(LegalOpinion.comments)
        ).where(LegalOpinion.id == opinion_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_case_id(self, case_id: uuid.UUID) -> Optional[LegalOpinion]:
        stmt = select(LegalOpinion).options(
            joinedload(LegalOpinion.revisions),
            joinedload(LegalOpinion.comments)
        ).where(LegalOpinion.case_id == case_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[LegalOpinion]:
        stmt = select(LegalOpinion).options(
            joinedload(LegalOpinion.case),
            joinedload(LegalOpinion.advocate),
            joinedload(LegalOpinion.revisions),
            joinedload(LegalOpinion.comments)
        ).order_by(desc(LegalOpinion.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def create(self, opinion: LegalOpinion) -> LegalOpinion:
        self.db.add(opinion)
        await self.db.commit()
        await self.db.refresh(opinion)
        return opinion

    async def update(self, opinion_id: uuid.UUID, update_data: dict) -> Optional[LegalOpinion]:
        stmt = update(LegalOpinion).where(LegalOpinion.id == opinion_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_by_id(opinion_id)

    async def delete(self, opinion_id: uuid.UUID):
        opinion = await self.get_by_id(opinion_id)
        if opinion:
            await self.db.delete(opinion)
            await self.db.commit()

class OpinionRevisionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, revision: OpinionRevision) -> OpinionRevision:
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision

    async def get_by_opinion_id(self, opinion_id: uuid.UUID) -> List[OpinionRevision]:
        stmt = select(OpinionRevision).where(OpinionRevision.opinion_id == opinion_id).order_by(desc(OpinionRevision.revision_number))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_revision_number(self, opinion_id: uuid.UUID) -> int:
        stmt = select(OpinionRevision.revision_number).where(OpinionRevision.opinion_id == opinion_id).order_by(desc(OpinionRevision.revision_number)).limit(1)
        result = await self.db.execute(stmt)
        rev = result.scalar_one_or_none()
        return rev if rev is not None else 0

class OpinionCommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, comment: OpinionComment) -> OpinionComment:
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_by_opinion_id(self, opinion_id: uuid.UUID) -> List[OpinionComment]:
        stmt = select(OpinionComment).where(OpinionComment.opinion_id == opinion_id).order_by(desc(OpinionComment.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
