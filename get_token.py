import asyncio
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy.future import select

async def get_token():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        if user:
            token = create_access_token({"sub": str(user.id)})
            print("TOKEN:", token)
        else:
            print("NO USERS FOUND")

asyncio.run(get_token())
