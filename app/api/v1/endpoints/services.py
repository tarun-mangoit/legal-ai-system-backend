from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.dependencies import get_db_session, RequireAdmin
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.service_manager import service_manager

router = APIRouter()

@router.get("/public", response_model=List[ServiceResponse])
async def get_public_services(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    return await service_manager.get_all(db, skip=skip, limit=limit, public_only=True)

@router.get("/", response_model=List[ServiceResponse], dependencies=[RequireAdmin])
async def get_services(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    return await service_manager.get_all(db, skip=skip, limit=limit, public_only=False)

@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequireAdmin])
async def create_service(service_in: ServiceCreate, db: AsyncSession = Depends(get_db_session)):
    return await service_manager.create(db, obj_in=service_in)

@router.get("/{id}", response_model=ServiceResponse, dependencies=[RequireAdmin])
async def get_service(id: UUID, db: AsyncSession = Depends(get_db_session)):
    service = await service_manager.get_by_id(db, id=id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/{id}", response_model=ServiceResponse, dependencies=[RequireAdmin])
async def update_service(id: UUID, service_in: ServiceUpdate, db: AsyncSession = Depends(get_db_session)):
    service = await service_manager.update(db, id=id, obj_in=service_in)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequireAdmin])
async def delete_service(id: UUID, db: AsyncSession = Depends(get_db_session)):
    success = await service_manager.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return None
