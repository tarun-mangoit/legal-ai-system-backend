from typing import List, Optional
import uuid
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.citation import Citation, CitationCategory

class CitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_citation(self, citation_id: uuid.UUID) -> Optional[Citation]:
        result = await self.db.execute(
            select(Citation).where(Citation.id == citation_id)
        )
        return result.scalars().first()

    async def create_citation(self, citation_data: dict) -> Citation:
        citation = Citation(**citation_data)
        self.db.add(citation)
        await self.db.commit()
        await self.db.refresh(citation)
        return citation

    async def update_citation(self, citation_id: uuid.UUID, update_data: dict) -> Optional[Citation]:
        citation = await self.get_citation(citation_id)
        if citation:
            for key, value in update_data.items():
                setattr(citation, key, value)
            await self.db.commit()
            await self.db.refresh(citation)
        return citation

    async def delete_citation(self, citation_id: uuid.UUID) -> bool:
        citation = await self.get_citation(citation_id)
        if citation:
            await self.db.delete(citation)
            await self.db.commit()
            return True
        return False

    async def search_citations(
        self, 
        query: Optional[str] = None, 
        court: Optional[str] = None, 
        jurisdiction: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Citation]:
        
        stmt = select(Citation).where(Citation.is_active == True)
        
        if query:
            stmt = stmt.where(
                or_(
                    Citation.title.ilike(f"%{query}%"),
                    Citation.reference_number.ilike(f"%{query}%"),
                    Citation.summary.ilike(f"%{query}%"),
                    Citation.keywords.any(query)
                )
            )
            
        if court:
            stmt = stmt.where(Citation.court == court)
        if jurisdiction:
            stmt = stmt.where(Citation.jurisdiction == jurisdiction)
        if category_id:
            stmt = stmt.where(Citation.category_id == category_id)
            
        stmt = stmt.limit(limit).offset(offset).order_by(Citation.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_categories(self) -> List[CitationCategory]:
        result = await self.db.execute(select(CitationCategory).order_by(CitationCategory.name))
        return result.scalars().all()
