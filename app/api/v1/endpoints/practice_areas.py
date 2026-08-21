from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_db_session, RequireAdmin
from app.schemas.practice_area import PracticeAreaCreate, PracticeAreaUpdate, PracticeAreaResponse
from app.services.practice_area_manager import practice_area_manager

router = APIRouter()

@router.get("/public", response_model=List[PracticeAreaResponse])
async def get_public_practice_areas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    items, count = await practice_area_manager.get_all(db, skip=skip, limit=limit, public_only=True)
    return items

@router.get("", dependencies=[RequireAdmin])
async def get_practice_areas(
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = 'sort_order',
    sort_order: str = 'asc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    skip = (page - 1) * page_size
    areas, total_count = await practice_area_manager.get_all(
        db, skip=skip, limit=page_size, public_only=False,
        search=search, status=status, sort_by=sort_by, sort_order=sort_order
    )
    
    items = [PracticeAreaResponse.model_validate(a).model_dump(mode='json') for a in areas]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.post("/", response_model=PracticeAreaResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_practice_area(area_in: PracticeAreaCreate, db: AsyncSession = Depends(get_db_session)):
    return await practice_area_manager.create(db, obj_in=area_in)

@router.get("/{id}", response_model=PracticeAreaResponse, dependencies=[RequireAdmin])
async def get_practice_area(id: UUID, db: AsyncSession = Depends(get_db_session)):
    area = await practice_area_manager.get_by_id(db, id=id)
    if not area:
        raise HTTPException(status_code=404, detail="Practice area not found")
    return area

@router.put("/{id}", response_model=PracticeAreaResponse, dependencies=[RequireAdmin])
async def update_practice_area(id: UUID, area_in: PracticeAreaUpdate, db: AsyncSession = Depends(get_db_session)):
    area = await practice_area_manager.update(db, id=id, obj_in=area_in)
    if not area:
        raise HTTPException(status_code=404, detail="Practice area not found")
    return area

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_practice_area(id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await practice_area_manager.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Practice area not found")
    return None
