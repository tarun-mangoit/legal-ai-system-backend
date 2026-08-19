from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.testimonial import Testimonial
from app.schemas.testimonial import TestimonialCreate, TestimonialUpdate
from app.repositories.base import BaseRepository

class TestimonialRepository(BaseRepository[Testimonial, TestimonialCreate, TestimonialUpdate]):
    def __init__(self):
        super().__init__(Testimonial)

    async def get_active_testimonials(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Testimonial]:
        result = await db.execute(select(self.model).filter(self.model.is_active == True).offset(skip).limit(limit))
        return list(result.scalars().all())

testimonial_repo = TestimonialRepository()
