from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Any
from app.models.case_assignment import CaseAssignment
from app.repositories.base import BaseRepository
from pydantic import UUID4

class CaseAssignmentRepository(BaseRepository[CaseAssignment, Any, Any]):
    def __init__(self):
        super().__init__(CaseAssignment)

    async def get_by_case(self, db: AsyncSession, case_id: UUID4) -> List[CaseAssignment]:
        query = select(self.model).where(self.model.case_id == case_id).order_by(desc(self.model.created_at))
        result = await db.execute(query)
        return result.scalars().all()

case_assignment_repository = CaseAssignmentRepository()
