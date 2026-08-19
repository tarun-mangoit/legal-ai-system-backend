from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from typing import List, Optional

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class ServiceManager:
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100, public_only: bool = False) -> List[Service]:
        query = select(Service)
        if public_only:
            query = query.filter(Service.is_active == True)
        query = query.order_by(Service.sort_order.asc(), Service.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[Service]:
        query = select(Service).where(Service.id == str(id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: ServiceCreate) -> Service:
        db_obj = Service(
            id=str(uuid4()),
            **obj_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, id: UUID, obj_in: ServiceUpdate) -> Optional[Service]:
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

service_manager = ServiceManager()
