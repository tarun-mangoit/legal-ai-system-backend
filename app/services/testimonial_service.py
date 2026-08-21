from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.testimonial import Testimonial
from app.schemas.testimonial import TestimonialCreate, TestimonialUpdate
from app.repositories.testimonial_repository import testimonial_repo

class TestimonialService:
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100,
                      search: Optional[str] = None, status: Optional[str] = None,
                      sort_by: Optional[str] = 'created_at', sort_order: str = 'desc') -> tuple[List[Testimonial], int]:
        return await testimonial_repo.get_all_paginated(
            db, skip=skip, limit=limit, search=search, status=status, sort_by=sort_by, sort_order=sort_order
        )

    async def get_active(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Testimonial]:
        return await testimonial_repo.get_active_testimonials(db, skip=skip, limit=limit)

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[Testimonial]:
        return await testimonial_repo.get(db, id=id)

    async def create(self, db: AsyncSession, obj_in: TestimonialCreate) -> Testimonial:
        return await testimonial_repo.create(db, obj_in=obj_in)

    async def update(self, db: AsyncSession, id: UUID, obj_in: TestimonialUpdate) -> Optional[Testimonial]:
        db_obj = await testimonial_repo.get(db, id=id)
        if not db_obj:
            return None
        return await testimonial_repo.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        db_obj = await testimonial_repo.get(db, id=id)
        if not db_obj:
            return False
        await testimonial_repo.remove(db, id=id)
        return True

testimonial_service = TestimonialService()
