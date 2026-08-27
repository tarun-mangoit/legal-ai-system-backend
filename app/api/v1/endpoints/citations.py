import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.citation_service import CitationService
from app.schemas.citation import CitationCreate, CitationUpdate, CitationResponse, CitationCategoryResponse

router = APIRouter()

def get_citation_service(db: AsyncSession = Depends(get_db)) -> CitationService:
    return CitationService(db)

@router.get("/categories", response_model=List[CitationCategoryResponse])
async def get_categories(service: CitationService = Depends(get_citation_service)):
    return await service.get_categories()

@router.post("", response_model=CitationResponse)
async def create_citation(
    data: CitationCreate, 
    service: CitationService = Depends(get_citation_service)
):
    return await service.create_citation(data.model_dump())

@router.get("/search", response_model=List[CitationResponse])
async def search_citations(
    q: Optional[str] = None,
    court: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    service: CitationService = Depends(get_citation_service)
):
    return await service.search_citations(q, court, jurisdiction, category_id, limit, offset)

@router.get("/{citation_id}", response_model=CitationResponse)
async def get_citation(
    citation_id: uuid.UUID, 
    service: CitationService = Depends(get_citation_service)
):
    return await service.get_citation(citation_id)

@router.put("/{citation_id}", response_model=CitationResponse)
async def update_citation(
    citation_id: uuid.UUID, 
    data: CitationUpdate, 
    service: CitationService = Depends(get_citation_service)
):
    return await service.update_citation(citation_id, data.model_dump(exclude_unset=True))

@router.delete("/{citation_id}")
async def delete_citation(
    citation_id: uuid.UUID, 
    service: CitationService = Depends(get_citation_service)
):
    await service.delete_citation(citation_id)
    return {"status": "success", "message": "Citation deleted"}

@router.post("/{citation_id}/verify", response_model=CitationResponse)
async def verify_citation(
    citation_id: uuid.UUID, 
    service: CitationService = Depends(get_citation_service)
):
    # Mock verification for Phase 1
    citation = await service.get_citation(citation_id)
    # Return the citation, ideally we would update it to ADVOCATE_VERIFIED here
    return citation
