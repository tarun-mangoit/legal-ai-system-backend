from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Any
from app.models.case_history import CaseHistory
from app.repositories.base import BaseRepository
from pydantic import UUID4

class CaseHistoryRepository(BaseRepository[CaseHistory, Any, Any]):
    def __init__(self):
        super().__init__(CaseHistory)

    async def get_by_case(self, db: AsyncSession, case_id: UUID4) -> List[CaseHistory]:
        query = select(self.model).where(self.model.case_id == case_id).order_by(desc(self.model.created_at))
        result = await db.execute(query)
        return result.scalars().all()

case_history_repository = CaseHistoryRepository()
