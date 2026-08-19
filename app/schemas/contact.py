from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str

class ContactUpdate(BaseModel):
    is_resolved: Optional[bool] = None

class ContactResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
