from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, UUID4, ConfigDict
from app.models.notification import NotificationStatus, NotificationType, NotificationChannel, NotificationCategory

class NotificationPreferenceBase(BaseModel):
    email_enabled: bool = True
    in_app_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    push_enabled: bool = False
    case_updates_enabled: bool = True
    document_updates_enabled: bool = True
    ai_updates_enabled: bool = True
    report_updates_enabled: bool = True
    payment_updates_enabled: bool = True
    account_updates_enabled: bool = True
    marketing_updates_enabled: bool = False
    system_updates_enabled: bool = True

class NotificationPreferenceResponse(NotificationPreferenceBase):
    user_id: UUID4

    model_config = ConfigDict(from_attributes=True)

class NotificationPreferenceUpdate(NotificationPreferenceBase):
    pass

class NotificationBase(BaseModel):
    title: str
    message: str
    channel: NotificationChannel
    priority: int = 0
    type: NotificationType = NotificationType.INFO
    category: Optional[NotificationCategory] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action_url: Optional[str] = None
    meta_data: Optional[Any] = None
    status: NotificationStatus = NotificationStatus.PENDING
    is_read: bool = False
    read_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int

class MarkAsReadResponse(BaseModel):
    success: bool
    notification_id: UUID4

class MarkAllAsReadResponse(BaseModel):
    success: bool
    updated_count: int
