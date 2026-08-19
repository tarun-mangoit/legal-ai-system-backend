from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.database.session import get_db
from app.dependencies import RequireClient
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.advocate import ChangePasswordRequest

router = APIRouter()

class ClientProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

@router.get("/me")
async def get_current_client_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireClient
):
    return {
        "user": current_user
    }

@router.put("/me")
async def update_client_profile(
    profile_in: ClientProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireClient
):
    current_user.first_name = profile_in.first_name
    current_user.last_name = profile_in.last_name
    current_user.phone = profile_in.phone
    current_user.address = profile_in.address
    current_user.city = profile_in.city
    current_user.state = profile_in.state
    current_user.country = profile_in.country
    current_user.postal_code = profile_in.postal_code
    
    await db.commit()
    await db.refresh(current_user)
    return {"user": current_user}

@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireClient
):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    if not pwd_context.verify(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    if data.new_password != data.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    current_user.password_hash = pwd_context.hash(data.new_password)
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="CLIENT_PASSWORD_CHANGED",
        changed_fields=["password_hash"]
    )
    db.add(audit_log)
    await db.commit()
    return {"message": "Password updated successfully"}
