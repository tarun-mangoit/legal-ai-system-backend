from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from typing import List, Optional

from app.models.practice_area import PracticeArea
from app.schemas.practice_area import PracticeAreaCreate, PracticeAreaUpdate

class PracticeAreaManager:
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100, public_only: bool = False) -> List[PracticeArea]:
        query = select(PracticeArea)
        if public_only:
            query = query.filter(PracticeArea.is_active == True)
        query = query.order_by(PracticeArea.sort_order.asc(), PracticeArea.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[PracticeArea]:
        query = select(PracticeArea).where(PracticeArea.id == str(id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: PracticeAreaCreate) -> PracticeArea:
        db_obj = PracticeArea(
            id=str(uuid4()),
            **obj_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, id: UUID, obj_in: PracticeAreaUpdate) -> Optional[PracticeArea]:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

practice_area_manager = PracticeAreaManager()
