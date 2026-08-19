from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, JSON, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
from app.models.base import BaseModel

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    READ = "READ"

class NotificationType(str, enum.Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"

class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"

class NotificationCategory(str, enum.Enum):
    AUTHENTICATION = "AUTHENTICATION"
    ACCOUNT = "ACCOUNT"
    ADVOCATE = "ADVOCATE"
    CASE = "CASE"
    DOCUMENT = "DOCUMENT"
    AI = "AI"
    LEGAL_OPINION = "LEGAL_OPINION"
    REPORT = "REPORT"
    PAYMENT = "PAYMENT"
    NOTIFICATION = "NOTIFICATION"
    SUPPORT = "SUPPORT"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"

class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    priority = Column(Integer, default=0) # Higher means more priority
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    category = Column(Enum(NotificationCategory), nullable=True)
    entity_type = Column(String(100), nullable=True) # e.g., 'CASE', 'DOCUMENT'
    entity_id = Column(String(255), nullable=True) # ID of the related entity
    action_url = Column(String(500), nullable=True) # Deep link
    meta_data = Column(JSON, nullable=True) # Extra info
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="notifications")
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification", cascade="all, delete-orphan")

class NotificationTemplate(BaseModel):
    __tablename__ = "notification_templates"

    name = Column(String(100), unique=True, index=True, nullable=False)
    subject_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)

class NotificationPreference(BaseModel):
    __tablename__ = "notification_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=False)
    
    # Granular category preferences
    case_updates_enabled = Column(Boolean, default=True)
    document_updates_enabled = Column(Boolean, default=True)
    ai_updates_enabled = Column(Boolean, default=True)
    report_updates_enabled = Column(Boolean, default=True)
    payment_updates_enabled = Column(Boolean, default=True)
    account_updates_enabled = Column(Boolean, default=True)
    marketing_updates_enabled = Column(Boolean, default=False)
    system_updates_enabled = Column(Boolean, default=True)

    user = relationship("User", backref="notification_preference")

class NotificationDeliveryLog(BaseModel):
    __tablename__ = "notification_delivery_logs"

    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(NotificationStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False) # e.g., 'SMTP', 'Twilio'
    
    notification = relationship("Notification", back_populates="delivery_logs")

class NotificationQueue(BaseModel):
    __tablename__ = "notification_queue"

    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

class PushSubscription(BaseModel):
    __tablename__ = "push_subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)
    device_name = Column(String(255), nullable=True)
    browser = Column(String(100), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", backref="push_subscriptions")
