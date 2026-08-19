from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate

class UserService:
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        return await user_repository.get_by_email(db, email=email)
    
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        return await user_repository.get(db, id=user_id)

    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        return await user_repository.create(db, obj_in=user_in)

user_service = UserService()
