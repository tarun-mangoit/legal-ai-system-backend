from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False

class UserCreate(UserBase):
    password_hash: str
    role_id: Optional[UUID4] = None

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: UUID4
    role_id: Optional[UUID4] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
