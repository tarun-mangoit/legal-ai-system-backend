import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.services.role_service import role_service
from app.services.user_service import user_service
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.models.role import Role

async def main():
    async with AsyncSessionLocal() as db:
        # Seed roles if they don't exist
        await role_service.seed_roles(db)
        
        # Get roles
        admin_role = await role_service.get_by_name(db, "admin")
        advocate_role = await role_service.get_by_name(db, "advocate")
        
        # Create Admin
        admin_email = "admin_consultationl@yopmail.com"
        admin_user = await user_service.get_by_email(db, admin_email)
        if not admin_user:
            user_create = UserCreate(
                email=admin_email,
                password_hash=get_password_hash("password123"),
                first_name="System",
                last_name="Admin",
                role_id=admin_role.id
            )
            await user_service.create(db, user_create)
            print("Created Admin User: admin_consultationl@yopmail.com / password123")
        else:
            print("Admin User already exists.")
            
        # Create Advocate
        advocate_email = "advocate_consultationl@yopmail.com"
        advocate_user = await user_service.get_by_email(db, advocate_email)
        if not advocate_user:
            user_create = UserCreate(
                email=advocate_email,
                password_hash=get_password_hash("password123"),
                first_name="Expert",
                last_name="Advocate",
                role_id=advocate_role.id
            )
            await user_service.create(db, user_create)
            print("Created Advocate User: advocate_consultationl@yopmail.com / password123")
        else:
            print("Advocate User already exists.")

if __name__ == "__main__":
    asyncio.run(main())
