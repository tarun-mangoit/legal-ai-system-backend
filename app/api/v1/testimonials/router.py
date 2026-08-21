from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import os
import aiofiles

from app.dependencies import get_db_session, RequireAdmin
from app.schemas.testimonial import TestimonialCreate, TestimonialUpdate, TestimonialResponse
from app.services.testimonial_service import testimonial_service
from app.models.user import User

router = APIRouter()

@router.get("/public", response_model=List[TestimonialResponse])
async def get_public_testimonials(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    """
    Get active testimonials for the public website.
    """
    return await testimonial_service.get_active(db, skip=skip, limit=limit)

@router.get("", dependencies=[RequireAdmin])
async def get_testimonials(
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all testimonials (Admin only).
    """
    skip = (page - 1) * page_size
    items, total_count = await testimonial_service.get_all(
        db, skip=skip, limit=page_size,
        search=search, status=status, sort_by=sort_by, sort_order=sort_order
    )
    
    formatted_items = [TestimonialResponse.model_validate(i).model_dump(mode='json') for i in items]
    
    return {
        "items": formatted_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.post("/", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_testimonial(
    testimonial_in: TestimonialCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new testimonial (Admin only).
    """
    return await testimonial_service.create(db, obj_in=testimonial_in)

@router.get("/{id}", response_model=TestimonialResponse, dependencies=[RequireAdmin])
async def get_testimonial(
    id: UUID, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific testimonial by ID (Admin only).
    """
    testimonial = await testimonial_service.get_by_id(db, id=id)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return testimonial

@router.put("/{id}", response_model=TestimonialResponse, dependencies=[RequireAdmin])
async def update_testimonial(
    id: UUID, 
    testimonial_in: TestimonialUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update a testimonial (Admin only).
    """
    testimonial = await testimonial_service.update(db, id=id, obj_in=testimonial_in)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return testimonial

@router.post("/{id}/image", response_model=TestimonialResponse, dependencies=[RequireAdmin])
async def upload_testimonial_image(
    id: UUID, 
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload an image for a testimonial (Admin only).
    """
    testimonial = await testimonial_service.get_by_id(db, id=id)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")
        
    upload_dir = os.path.join("uploads", "testimonials")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{id}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)
            
    public_url = f"/uploads/testimonials/{filename}"
    
    updated_testimonial = await testimonial_service.update(
        db, 
        id=id, 
        obj_in=TestimonialUpdate(client_image_url=public_url)
    )
    
    return updated_testimonial

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_testimonial(
    id: UUID, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a testimonial (Admin only).
    """
    success = await testimonial_service.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return None
