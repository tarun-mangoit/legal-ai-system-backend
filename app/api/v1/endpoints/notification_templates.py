from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel, UUID4
from sqlalchemy import select

from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.notification import NotificationTemplate
from app.repositories.notification_repository import NotificationTemplateRepository

router = APIRouter()
template_repo = NotificationTemplateRepository()

# Require Admin for all endpoints
RequireAdmin = Depends(require_roles(["admin"]))

class TemplateUpdate(BaseModel):
    subject_template: str
    body_template: str

class TemplateResponse(BaseModel):
    id: UUID4
    name: str
    subject_template: str
    body_template: str
    channel: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[TemplateResponse])
async def get_templates(
    current_user: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    templates = await template_repo.get_all(db)
    return templates

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID4,
    current_user: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID4,
    update_data: TemplateUpdate,
    current_user: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    template.subject_template = update_data.subject_template
    template.body_template = update_data.body_template
    
    await db.commit()
    await db.refresh(template)
    
    return template
