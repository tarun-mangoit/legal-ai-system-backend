from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.contact import ContactSubmission
from app.schemas.contact import ContactCreate, ContactUpdate

class ContactService:
    async def create(self, db: AsyncSession, obj_in: ContactCreate) -> ContactSubmission:
        db_obj = ContactSubmission(
            name=obj_in.name,
            email=obj_in.email,
            phone=obj_in.phone,
            message=obj_in.message
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ContactSubmission]:
        query = select(ContactSubmission).order_by(ContactSubmission.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[ContactSubmission]:
        query = select(ContactSubmission).filter(ContactSubmission.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def update(self, db: AsyncSession, id: UUID, obj_in: ContactUpdate) -> Optional[ContactSubmission]:
        db_obj = await self.get_by_id(db, id=id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        db_obj = await self.get_by_id(db, id=id)
        if not db_obj:
            return False
            
        await db.delete(db_obj)
        await db.commit()
        return True

contact_service = ContactService()
