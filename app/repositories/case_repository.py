from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, text
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from app.models.case import Case, CaseStatus
from app.repositories.base import BaseRepository
from datetime import datetime
from pydantic import UUID4

class CaseRepository(BaseRepository[Case, Any, Any]):
    def __init__(self):
        super().__init__(Case)

    async def generate_case_number(self, db: AsyncSession) -> str:
        # Use postgres sequence for thread safety
        result = await db.execute(text("SELECT nextval('case_number_seq')"))
        seq_num = result.scalar()
        year = datetime.now().year
        return f"CASE-{year}-{seq_num:06d}"

    async def get_by_case_number(self, db: AsyncSession, case_number: str) -> Optional[Case]:
        query = select(self.model).options(
            joinedload(self.model.client),
            joinedload(self.model.advocate)
        ).where(self.model.case_number == case_number)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, id: Any) -> Optional[Case]:
        query = select(self.model).options(
            joinedload(self.model.client),
            joinedload(self.model.advocate)
        ).filter(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    def _apply_filters(self, query, filters: Dict[str, Any]):
        if "client_id" in filters:
            query = query.where(self.model.client_id == filters["client_id"])
        
        if "advocate_id" in filters:
            query = query.where(self.model.advocate_id == filters["advocate_id"])
            
        if "status" in filters:
            query = query.where(self.model.status == filters["status"])

        if "priority" in filters:
            query = query.where(self.model.priority == filters["priority"])

        if "category" in filters:
            query = query.where(self.model.category == filters["category"])

        if "start_date" in filters:
            query = query.where(self.model.created_at >= filters["start_date"])

        if "end_date" in filters:
            query = query.where(self.model.created_at <= filters["end_date"])

        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.where(
                (self.model.title.ilike(search_term)) | 
                (self.model.case_number.ilike(search_term))
            )
        return query

    async def search(self, db: AsyncSession, filters: Dict[str, Any], skip: int = 0, limit: int = 100, sort_by: str = "created_at", sort_order: str = "desc") -> List[Case]:
        query = select(self.model).options(
            joinedload(self.model.client),
            joinedload(self.model.advocate)
        )
        
        query = self._apply_filters(query, filters)

        # Handle sorting
        sort_col = getattr(self.model, sort_by, self.model.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count(self, db: AsyncSession, filters: Dict[str, Any]) -> int:
        from sqlalchemy import func
        query = select(func.count()).select_from(self.model)
        query = self._apply_filters(query, filters)

        result = await db.execute(query)
        return result.scalar() or 0

case_repository = CaseRepository()
