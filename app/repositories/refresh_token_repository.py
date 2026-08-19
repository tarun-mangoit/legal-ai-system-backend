from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository
from pydantic import BaseModel

class RefreshTokenRepository(BaseRepository[RefreshToken, BaseModel, BaseModel]):
    def __init__(self):
        super().__init__(RefreshToken)

    async def get_by_token_hash(self, db: AsyncSession, token_hash: str) -> Optional[RefreshToken]:
        result = await db.execute(select(RefreshToken).filter(RefreshToken.token_hash == token_hash))
        return result.scalars().first()

refresh_token_repository = RefreshTokenRepository()
