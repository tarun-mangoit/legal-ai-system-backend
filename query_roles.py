import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == 'admin_consultationl@yopmail.com'))
        admin = result.scalars().first()
        if admin:
            role = await db.get(Role, admin.role_id)
            print(f"Admin User Role: {role.name}")
        else:
            print("Admin not found")

asyncio.run(main())
