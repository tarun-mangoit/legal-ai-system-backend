import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.citation_repository import CitationRepository
from app.models.citation import Citation, CitationCategory

class CitationService:
    def __init__(self, db: AsyncSession):
        self.repository = CitationRepository(db)

    async def get_citation(self, citation_id: uuid.UUID) -> Citation:
        citation = await self.repository.get_citation(citation_id)
        if not citation:
            raise HTTPException(status_code=404, detail="Citation not found")
        return citation

    async def create_citation(self, data: dict) -> Citation:
        return await self.repository.create_citation(data)

    async def update_citation(self, citation_id: uuid.UUID, data: dict) -> Citation:
        citation = await self.repository.update_citation(citation_id, data)
        if not citation:
            raise HTTPException(status_code=404, detail="Citation not found")
        return citation

    async def delete_citation(self, citation_id: uuid.UUID) -> bool:
        success = await self.repository.delete_citation(citation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Citation not found")
        return True

    async def search_citations(
        self, 
        query: Optional[str] = None, 
        court: Optional[str] = None, 
        jurisdiction: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Citation]:
        return await self.repository.search_citations(query, court, jurisdiction, category_id, limit, offset)

    async def get_categories(self) -> List[CitationCategory]:
        return await self.repository.get_categories()
