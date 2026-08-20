from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.models.seo import PageSEO
from app.schemas.seo import PageSEOCreate, PageSEOUpdate, PageSEOResponse
import os
import shutil
import uuid
import aiofiles

router = APIRouter()

UPLOAD_DIR = "uploads/seo"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/{page_identifier}", response_model=PageSEOResponse)
async def get_page_seo(
    page_identifier: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PageSEO).filter(PageSEO.page_identifier == page_identifier))
    seo = result.scalars().first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO settings not found")
    return seo

@router.post("/", response_model=PageSEOResponse)
async def create_page_seo(
    seo_in: PageSEOCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PageSEO).filter(PageSEO.page_identifier == seo_in.page_identifier))
    seo = result.scalars().first()
    if seo:
        raise HTTPException(status_code=400, detail="SEO settings already exist for this page")
    
    seo = PageSEO(**seo_in.model_dump())
    db.add(seo)
    await db.commit()
    await db.refresh(seo)
    return seo

@router.put("/{page_identifier}", response_model=PageSEOResponse)
async def update_page_seo(
    page_identifier: str,
    seo_in: PageSEOUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PageSEO).filter(PageSEO.page_identifier == page_identifier))
    seo = result.scalars().first()
    if not seo:
        seo = PageSEO(page_identifier=page_identifier, **seo_in.model_dump())
        db.add(seo)
    else:
        update_data = seo_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(seo, field, value)
    
    await db.commit()
    await db.refresh(seo)
    return seo

@router.post("/{page_identifier}/upload-image", response_model=dict)
async def upload_seo_image(
    page_identifier: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PageSEO).filter(PageSEO.page_identifier == page_identifier))
    seo = result.scalars().first()
    if not seo:
        seo = PageSEO(page_identifier=page_identifier)
        db.add(seo)
        await db.commit()
        await db.refresh(seo)
        
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)
        
    url_path = f"/{UPLOAD_DIR}/{filename}"
    seo.og_image_url = url_path
    
    await db.commit()
    await db.refresh(seo)
    
    return {"url": url_path}
