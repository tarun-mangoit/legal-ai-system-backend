from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.config import settings
from app.models.user import User
from app.services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db_session(session: AsyncSession = Depends(get_db)):
    return session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await user_service.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

def require_roles(required_roles: List[str]) -> Callable:
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
    ):
        from app.services.role_service import role_service
        # Assuming role relationship is eager loaded, if not we need to fetch the role
        # We'll just fetch it here for simplicity
        from app.models.role import Role
        role = await db.get(Role, current_user.role_id)
        if not role or role.name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker

RequireAdmin = Depends(require_roles(["admin"]))
RequireAdvocate = Depends(require_roles(["admin", "advocate"]))
RequireClient = Depends(require_roles(["admin", "client"]))
