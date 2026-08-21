import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc, asc, func

from app.database.session import get_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate, PageResponse
from app.dependencies import get_current_user, RequireAdmin

router = APIRouter()

@router.get("")
async def get_all_pages(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all pages (paginated).
    """
    conditions = []
    if search:
        conditions.append(or_(Page.title.ilike(f"%{search}%"), Page.slug.ilike(f"%{search}%")))
        
    if status == 'published':
        conditions.append(Page.is_published == True)
    elif status == 'draft':
        conditions.append(Page.is_published == False)
        
    query = select(Page)
    count_query = select(func.count(Page.id))
    
    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)
        
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    if hasattr(Page, sort_by):
        column = getattr(Page, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
    else:
        query = query.order_by(Page.created_at.desc())
        
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    pages = result.scalars().all()
    
    items = [PageResponse.model_validate(p).model_dump(mode='json') for p in pages]
    
    return {
        "items": items,
        "summary": { # Optional summary if needed
            "total": total_count
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

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
