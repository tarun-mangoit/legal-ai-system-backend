from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import role_repository
from app.models.role import Role
from pydantic import BaseModel

class RoleCreate(BaseModel):
    name: str
    description: str

class RoleService:
    async def get_by_name(self, db: AsyncSession, name: str):
        return await role_repository.get_by_name(db, name=name)
        
    async def seed_roles(self, db: AsyncSession):
        roles = [
            {"name": "admin", "description": "Administrator with full access"},
            {"name": "advocate", "description": "Legal advocate"},
            {"name": "client", "description": "Regular client user"}
        ]
        
        for role_data in roles:
            existing = await self.get_by_name(db, role_data["name"])
            if not existing:
                await role_repository.create(db, obj_in=RoleCreate(**role_data))

role_service = RoleService()
