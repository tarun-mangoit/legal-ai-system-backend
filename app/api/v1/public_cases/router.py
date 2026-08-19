from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import os
import aiofiles

from app.dependencies import get_db_session, RequireAdmin
from app.schemas.public_case import (
    PublicCaseCreate, PublicCaseUpdate, PublicCaseResponse,
    PublicCaseCategoryCreate, PublicCaseCategoryResponse,
    PublicCaseTagCreate, PublicCaseTagResponse,
    SidebarDataResponse, PublicCaseCategoryWithCount,
    PublicCaseDetailResponse, PublicCaseNavResponse
)
from app.services.public_case_service import (
    public_case_service, public_case_category_service, public_case_tag_service
)

from app.models.public_case import PublicCase, PublicCaseCategory, PublicCaseTag
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

router = APIRouter()

# --- Public Routes ---

@router.get("/public/sidebar-data", response_model=SidebarDataResponse)
async def get_sidebar_data(db: AsyncSession = Depends(get_db_session)):
    categories_query = select(
        PublicCaseCategory, func.count(PublicCase.id).label('count')
    ).outerjoin(PublicCase, (PublicCase.category_id == PublicCaseCategory.id) & (PublicCase.is_active == True)) \
     .group_by(PublicCaseCategory.id)
     
    cat_result = await db.execute(categories_query)
    
    categories = [
        PublicCaseCategoryWithCount(
            id=cat.id, name=cat.name, slug=cat.slug, created_at=cat.created_at, count=count
        ) for cat, count in cat_result.all()
    ]
    
    rp_query = select(PublicCase).filter(PublicCase.is_active == True).options(
        selectinload(PublicCase.category),
        selectinload(PublicCase.tags)
    ).order_by(PublicCase.created_at.desc()).limit(3)
    rp_result = await db.execute(rp_query)
    recent_cases = rp_result.scalars().all()
                     
    tags_query = select(PublicCaseTag)
    tags_result = await db.execute(tags_query)
    tags = tags_result.scalars().all()
    
    return SidebarDataResponse(
        categories=categories,
        recent_cases=recent_cases,
        tags=tags
    )

@router.get("/public", response_model=List[PublicCaseResponse])
async def get_public_cases(
    skip: int = 0, 
    limit: int = 100, 
    category_slug: str = None, 
    tag_slug: str = None, 
    db: AsyncSession = Depends(get_db_session)
):
    query = select(PublicCase).filter(PublicCase.is_active == True).options(
        selectinload(PublicCase.category),
        selectinload(PublicCase.tags)
    )
    
    if category_slug:
        query = query.join(PublicCaseCategory).filter(PublicCaseCategory.slug == category_slug)
    if tag_slug:
        query = query.join(PublicCase.tags).filter(PublicCaseTag.slug == tag_slug)
        
    query = query.order_by(PublicCase.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().unique().all()

@router.get("/public/{slug}", response_model=PublicCaseDetailResponse)
async def get_public_case_by_slug(slug: str, db: AsyncSession = Depends(get_db_session)):
    query = select(PublicCase).where(PublicCase.slug == slug, PublicCase.is_active == True).options(
        selectinload(PublicCase.category),
        selectinload(PublicCase.tags)
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    prev_query = select(PublicCase).filter(PublicCase.is_active == True, PublicCase.created_at < case.created_at).order_by(PublicCase.created_at.desc()).limit(1)
    next_query = select(PublicCase).filter(PublicCase.is_active == True, PublicCase.created_at > case.created_at).order_by(PublicCase.created_at.asc()).limit(1)
    
    prev_res = await db.execute(prev_query)
    next_res = await db.execute(next_query)
    
    prev_case = prev_res.scalars().first()
    next_case = next_res.scalars().first()
    
    return PublicCaseDetailResponse(
        **PublicCaseResponse.model_validate(case).model_dump(),
        previous_case=PublicCaseNavResponse(title=prev_case.title, slug=prev_case.slug) if prev_case else None,
        next_case=PublicCaseNavResponse(title=next_case.title, slug=next_case.slug) if next_case else None
    )

# --- Admin Routes: Categories ---

@router.get("/categories", response_model=List[PublicCaseCategoryResponse], dependencies=[RequireAdmin])
async def get_categories(db: AsyncSession = Depends(get_db_session)):
    return await public_case_category_service.get_all(db)

@router.post("/categories", response_model=PublicCaseCategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_category(category_in: PublicCaseCategoryCreate, db: AsyncSession = Depends(get_db_session)):
    return await public_case_category_service.create(db, obj_in=category_in)

@router.delete("/categories/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_category(id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await public_case_category_service.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None

# --- Admin Routes: Tags ---

@router.get("/tags", response_model=List[PublicCaseTagResponse], dependencies=[RequireAdmin])
async def get_tags(db: AsyncSession = Depends(get_db_session)):
    return await public_case_tag_service.get_all(db)

@router.post("/tags", response_model=PublicCaseTagResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_tag(tag_in: PublicCaseTagCreate, db: AsyncSession = Depends(get_db_session)):
    return await public_case_tag_service.create(db, obj_in=tag_in)

@router.delete("/tags/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_tag(id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await public_case_tag_service.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None

# --- Admin Routes: Cases ---

@router.post("/upload-image", dependencies=[RequireAdmin])
async def upload_general_case_image(file: UploadFile = File(...)):
    import uuid
    upload_dir = os.path.join("uploads", "public_cases")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)
            
    public_url = f"/uploads/public_cases/{filename}"
    return {"cover_image_url": public_url}

@router.get("/", response_model=List[PublicCaseResponse], dependencies=[RequireAdmin])
async def get_cases(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    return await public_case_service.get_all(db, skip=skip, limit=limit)

@router.post("/", response_model=PublicCaseResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_case(case_in: PublicCaseCreate, db: AsyncSession = Depends(get_db_session)):
    return await public_case_service.create(db, obj_in=case_in)

@router.get("/{id}", response_model=PublicCaseResponse, dependencies=[RequireAdmin])
async def get_case(id: UUID, db: AsyncSession = Depends(get_db_session)):
    case = await public_case_service.get_by_id(db, id=id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/{id}", response_model=PublicCaseResponse, dependencies=[RequireAdmin])
async def update_case(id: UUID, case_in: PublicCaseUpdate, db: AsyncSession = Depends(get_db_session)):
    case = await public_case_service.update(db, id=id, obj_in=case_in)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_case(id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await public_case_service.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Case not found")
    return None

@router.post("/{id}/image", response_model=PublicCaseResponse, dependencies=[RequireAdmin])
async def upload_case_image(id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session)):
    case = await public_case_service.get_by_id(db, id=id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    upload_dir = os.path.join("uploads", "public_cases")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{id}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)
            
    public_url = f"/uploads/public_cases/{filename}"
    
    updated_case = await public_case_service.update(
        db, 
        id=id, 
        obj_in=PublicCaseUpdate(cover_image_url=public_url)
    )
    
    return updated_case
