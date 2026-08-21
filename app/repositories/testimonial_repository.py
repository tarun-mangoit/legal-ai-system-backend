from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.testimonial import Testimonial
from app.schemas.testimonial import TestimonialCreate, TestimonialUpdate
from app.repositories.base import BaseRepository

class TestimonialRepository(BaseRepository[Testimonial, TestimonialCreate, TestimonialUpdate]):
    def __init__(self):
        super().__init__(Testimonial)

    async def get_active_testimonials(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[List[Testimonial], int]:
        from sqlalchemy import func
        result = await db.execute(select(self.model).filter(self.model.is_active == True).offset(skip).limit(limit))
        count = await db.execute(select(func.count(self.model.id)).filter(self.model.is_active == True))
        return list(result.scalars().all()), count.scalar() or 0

    async def get_all_paginated(
        self, db: AsyncSession, skip: int = 0, limit: int = 100,
        search: Optional[str] = None, status: Optional[str] = None,
        sort_by: Optional[str] = 'created_at', sort_order: str = 'desc'
    ) -> tuple[List[Testimonial], int]:
        from sqlalchemy import or_, desc, asc, func
        
        query = select(self.model)
        count_query = select(func.count(self.model.id))
        
        conditions = []
        if search:
            conditions.append(or_(
                self.model.client_name.ilike(f"%{search}%"),
                self.model.company.ilike(f"%{search}%"),
                self.model.content.ilike(f"%{search}%")
            ))
            
        if status == 'active':
            conditions.append(self.model.is_active == True)
        elif status == 'inactive':
            conditions.append(self.model.is_active == False)
            
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)
            
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        if hasattr(self.model, sort_by):
            column = getattr(self.model, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            query = query.order_by(self.model.created_at.desc())
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total_count

testimonial_repo = TestimonialRepository()
