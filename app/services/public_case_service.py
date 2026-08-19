from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.public_case import PublicCase, PublicCaseCategory, PublicCaseTag
from app.schemas.public_case import (
    PublicCaseCreate, PublicCaseUpdate, 
    PublicCaseCategoryCreate, PublicCaseTagCreate
)

class PublicCaseCategoryService:
    async def get_all(self, db: AsyncSession) -> List[PublicCaseCategory]:
        result = await db.execute(select(PublicCaseCategory))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: PublicCaseCategoryCreate) -> PublicCaseCategory:
        db_obj = PublicCaseCategory(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        result = await db.execute(select(PublicCaseCategory).where(PublicCaseCategory.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await db.delete(obj)
        await db.commit()
        return True

class PublicCaseTagService:
    async def get_all(self, db: AsyncSession) -> List[PublicCaseTag]:
        result = await db.execute(select(PublicCaseTag))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: PublicCaseTagCreate) -> PublicCaseTag:
        db_obj = PublicCaseTag(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        result = await db.execute(select(PublicCaseTag).where(PublicCaseTag.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await db.delete(obj)
        await db.commit()
        return True

class PublicCaseService:
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PublicCase]:
        query = select(PublicCase).options(
            selectinload(PublicCase.category),
            selectinload(PublicCase.tags)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PublicCase]:
        query = select(PublicCase).where(PublicCase.is_active == True).options(
            selectinload(PublicCase.category),
            selectinload(PublicCase.tags)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[PublicCase]:
        query = select(PublicCase).where(PublicCase.id == id).options(
            selectinload(PublicCase.category),
            selectinload(PublicCase.tags)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[PublicCase]:
        query = select(PublicCase).where(PublicCase.slug == slug, PublicCase.is_active == True).options(
            selectinload(PublicCase.category),
            selectinload(PublicCase.tags)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: PublicCaseCreate) -> PublicCase:
        obj_data = obj_in.model_dump(exclude={"tag_ids"})
        
        db_obj = PublicCase(**obj_data)
        
        if obj_in.tag_ids:
            tags_result = await db.execute(select(PublicCaseTag).where(PublicCaseTag.id.in_(obj_in.tag_ids)))
            db_obj.tags = tags_result.scalars().all()
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Reload to get relationships
        return await self.get_by_id(db, db_obj.id)

    async def update(self, db: AsyncSession, id: UUID, obj_in: PublicCaseUpdate) -> Optional[PublicCase]:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
            
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"tag_ids"})
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        if obj_in.tag_ids is not None:
            tags_result = await db.execute(select(PublicCaseTag).where(PublicCaseTag.id.in_(obj_in.tag_ids)))
            db_obj.tags = tags_result.scalars().all()
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return await self.get_by_id(db, id)

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
            
        await db.delete(db_obj)
        await db.commit()
        return True

public_case_category_service = PublicCaseCategoryService()
public_case_tag_service = PublicCaseTagService()
public_case_service = PublicCaseService()
