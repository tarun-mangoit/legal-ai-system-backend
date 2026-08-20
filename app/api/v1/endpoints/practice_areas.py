from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.dependencies import get_db_session, RequireAdmin
from app.schemas.practice_area import PracticeAreaCreate, PracticeAreaUpdate, PracticeAreaResponse
from app.services.practice_area_manager import practice_area_manager

router = APIRouter()

@router.get("/public", response_model=List[PracticeAreaResponse])
async def get_public_practice_areas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    return await practice_area_manager.get_all(db, skip=skip, limit=limit, public_only=True)

@router.get("/", response_model=List[PracticeAreaResponse], dependencies=[RequireAdmin])
async def get_practice_areas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    return await practice_area_manager.get_all(db, skip=skip, limit=limit, public_only=False)

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
