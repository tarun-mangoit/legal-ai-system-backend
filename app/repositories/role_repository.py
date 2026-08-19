from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.role import Role
from app.repositories.base import BaseRepository
from pydantic import BaseModel

class RoleRepository(BaseRepository[Role, BaseModel, BaseModel]):
    def __init__(self):
        super().__init__(Role)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        result = await db.execute(select(Role).filter(func.lower(Role.name) == func.lower(name)))
        return result.scalars().first()

role_repository = RoleRepository()
