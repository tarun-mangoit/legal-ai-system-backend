import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate, PageResponse
from app.dependencies import get_current_user, RequireAdmin

router = APIRouter()

@router.get("", response_model=List[PageResponse])
async def get_all_pages(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all pages.
    """
    query = select(Page).order_by(Page.created_at.desc())
    result = await db.execute(query)
    pages = result.scalars().all()
    return pages

@router.get("/{slug}", response_model=PageResponse)
async def get_page_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific page by slug.
    """
    query = select(Page).filter(Page.slug == slug)
    result = await db.execute(query)
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    return page

@router.post("", response_model=PageResponse, dependencies=[RequireAdmin])
async def create_page(
    page_in: PageCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new page.
    """
    query = select(Page).filter(Page.slug == page_in.slug)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Page with this slug already exists")
        
    page = Page(
        title=page_in.title,
        slug=page_in.slug,
        content=page_in.content,
        meta_title=page_in.meta_title,
        meta_description=page_in.meta_description,
        featured_image_url=page_in.featured_image_url,
        is_published=page_in.is_published
    )
    
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page

import os
import shutil
from fastapi import UploadFile, File

UPLOAD_DIR = "uploads/pages"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/admin/upload-image", response_model=dict, dependencies=[RequireAdmin])
async def upload_page_image(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload an image for a page (featured or inline).
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    ext = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/uploads/pages/{filename}"
    return {"url": image_url}

@router.put("/{id}", response_model=PageResponse, dependencies=[RequireAdmin])
async def update_page(
    id: uuid.UUID,
    page_in: PageUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a page.
    """
    query = select(Page).filter(Page.id == id)
    result = await db.execute(query)
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    if page_in.slug and page_in.slug != page.slug:
        check_query = select(Page).filter(Page.slug == page_in.slug)
        check_result = await db.execute(check_query)
        if check_result.scalars().first():
            raise HTTPException(status_code=400, detail="Page with this slug already exists")
            
    update_data = page_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(page, field, value)
        
    await db.commit()
    await db.refresh(page)
    return page

@router.delete("/{id}", response_model=dict, dependencies=[RequireAdmin])
async def delete_page(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a page.
    """
    query = select(Page).filter(Page.id == id)
    result = await db.execute(query)
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    await db.delete(page)
    await db.commit()
    return {"message": "Page deleted successfully"}
