from typing import Any
import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.settings import SiteSettings
from app.schemas.settings import SiteSettingsResponse, SiteSettingsUpdate
from app.dependencies import RequireAdmin

router = APIRouter()

@router.get("", response_model=SiteSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get site settings. Creates default settings if none exist.
    """
    result = await db.execute(select(SiteSettings))
    settings = result.scalars().first()
    if not settings:
        settings = SiteSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@router.put("", response_model=SiteSettingsResponse, dependencies=[RequireAdmin])
async def update_settings(
    *,
    db: AsyncSession = Depends(get_db),
    settings_in: SiteSettingsUpdate
) -> Any:
    """
    Update site settings. Admin only.
    """
    result = await db.execute(select(SiteSettings))
    settings = result.scalars().first()
    if not settings:
        settings = SiteSettings()
        db.add(settings)
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, list):
            setattr(settings, field, [item for item in value])
        else:
            setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings

UPLOAD_DIR = "uploads/settings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/statistics-image", response_model=SiteSettingsResponse, dependencies=[RequireAdmin])
async def upload_statistics_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a background image for the statistics section. Admin only.
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    ext = file.filename.split('.')[-1]
    filename = f"statistics_bg_{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/uploads/settings/{filename}"
    
    result = await db.execute(select(SiteSettings))
    settings = result.scalars().first()
    if not settings:
        settings = SiteSettings()
        db.add(settings)
        
    settings.statistics_image_url = image_url
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.post("/default-hero-image", response_model=SiteSettingsResponse, dependencies=[RequireAdmin])
async def upload_default_hero_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a background image for the default hero section. Admin only.
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    ext = file.filename.split('.')[-1]
    filename = f"default_hero_bg_{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/uploads/settings/{filename}"
    
    result = await db.execute(select(SiteSettings))
    settings = result.scalars().first()
    if not settings:
        settings = SiteSettings()
        db.add(settings)
        
    settings.default_hero_image_url = image_url
    
    await db.commit()
    await db.refresh(settings)
    return settings
