from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PracticeAreaBase(BaseModel):
    title: str
    description: str
    icon_svg: str
    action_text: str = "Read More"
    link: str = "#"
    is_active: bool = True
    sort_order: int = 0

class PracticeAreaCreate(PracticeAreaBase):
    pass

class PracticeAreaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon_svg: Optional[str] = None
    action_text: Optional[str] = None
    link: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class PracticeAreaResponse(PracticeAreaBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
