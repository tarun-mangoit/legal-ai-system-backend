from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.user import User
from app.repositories.base import BaseRepository
from pydantic import BaseModel

class UserRepository(BaseRepository[User, BaseModel, BaseModel]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(func.lower(User.email) == func.lower(email)))
        return result.scalars().first()

user_repository = UserRepository()
