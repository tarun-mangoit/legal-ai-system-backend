from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class ServiceBase(BaseModel):
    title: str
    description: str
    icon_svg: str
    action_text: str
    link: str
    is_active: bool = True
    sort_order: int = 0

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon_svg: Optional[str] = None
    action_text: Optional[str] = None
    link: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class ServiceResponse(ServiceBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
