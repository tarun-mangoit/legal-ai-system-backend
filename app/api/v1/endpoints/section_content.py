import os
import shutil
import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.section_content import SectionContent
from app.schemas.section_content import SectionContentCreate, SectionContentUpdate, SectionContentResponse
from app.dependencies import get_current_user, RequireAdmin

router = APIRouter()

UPLOAD_DIR = "uploads/sections"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[SectionContentResponse])
async def get_all_sections(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all dynamic sections.
    """
    query = select(SectionContent).order_by(SectionContent.created_at.desc())
    result = await db.execute(query)
    sections = result.scalars().all()
    return sections

@router.get("/{section_key}", response_model=SectionContentResponse)
async def get_section_by_key(
    section_key: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific section by its key (e.g. 'home-about').
    """
    query = select(SectionContent).filter(SectionContent.section_key == section_key)
    result = await db.execute(query)
    section = result.scalars().first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    return section

@router.post("", response_model=SectionContentResponse, dependencies=[RequireAdmin])
async def create_section(
    section_in: SectionContentCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new dynamic section.
    """
    query = select(SectionContent).filter(SectionContent.section_key == section_in.section_key)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Section with this key already exists")
        
    section = SectionContent(
        section_key=section_in.section_key,
        title=section_in.title,
        subtitle=section_in.subtitle,
        content=section_in.content,
        image_url=section_in.image_url
    )
    
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section

@router.put("/{section_key}", response_model=SectionContentResponse, dependencies=[RequireAdmin])
async def update_section(
    section_key: str,
    section_in: SectionContentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update an existing section by key.
    """
    query = select(SectionContent).filter(SectionContent.section_key == section_key)
    result = await db.execute(query)
    section = result.scalars().first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
            
    update_data = section_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)
        
    await db.commit()
    await db.refresh(section)
    return section

@router.post("/admin/upload-image", response_model=dict, dependencies=[RequireAdmin])
async def upload_section_image(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload an image for a dynamic section.
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    ext = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/uploads/sections/{filename}"
    return {"url": image_url}
