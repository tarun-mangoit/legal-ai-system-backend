import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import (
    Notification, NotificationStatus, NotificationChannel,
    NotificationDeliveryLog, NotificationTemplate, NotificationCategory
)
from app.repositories.notification_repository import (
    NotificationRepository, NotificationPreferenceRepository, NotificationTemplateRepository
)
from app.services.notification_providers import (
    NotificationProvider, EmailProvider, InAppProvider, SMSProvider, WhatsAppProvider, PushProvider, SlackProvider, TeamsProvider
)

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self, template_repo: NotificationTemplateRepository):
        self.template_repo = template_repo

    async def get_rendered_content(self, db: AsyncSession, template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
        """Fetches a template and renders it using the provided context."""
        template = await self.template_repo.get_by_name(db, template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
        
        subject = template.subject_template
        body = template.body_template
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
            
        return subject, body


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        preference_repo: NotificationPreferenceRepository,
        template_service: TemplateService
    ):
        self.notification_repo = notification_repo
        self.preference_repo = preference_repo
        self.template_service = template_service
        self.providers: Dict[NotificationChannel, NotificationProvider] = {
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.IN_APP: InAppProvider(notification_repo),
            NotificationChannel.SMS: SMSProvider(),
            NotificationChannel.WHATSAPP: WhatsAppProvider(),
            NotificationChannel.PUSH: PushProvider(),
        }

    async def _log_delivery(self, db: AsyncSession, notification_id: str, status: NotificationStatus, provider: str, error: str = None):
        log = NotificationDeliveryLog(
            notification_id=notification_id,
            status=status,
            provider=provider,
            error_message=error
        )
        db.add(log)
        await db.commit()

    async def send_notification(
        self, db: AsyncSession, user_id: str, channel: NotificationChannel, 
        title: str, message: str, priority: int = 0,
        category: NotificationCategory = NotificationCategory.NOTIFICATION,
        action_url: str = None, entity_type: str = None, entity_id: str = None
    ) -> Notification:
        # Check user preference
        prefs = await self.preference_repo.get_by_user(db, user_id)
        if prefs and category != NotificationCategory.SECURITY:
            if channel == NotificationChannel.EMAIL and not prefs.email_enabled:
                logger.info(f"User {user_id} has disabled EMAIL notifications globally.")
                return None
            if channel == NotificationChannel.IN_APP and not prefs.in_app_enabled:
                logger.info(f"User {user_id} has disabled IN_APP notifications globally.")
                return None
            if channel == NotificationChannel.PUSH and not prefs.push_enabled:
                return None
                
            # Granular checks
            if category == NotificationCategory.CASE and not prefs.case_updates_enabled:
                return None
            if category == NotificationCategory.DOCUMENT and not prefs.document_updates_enabled:
                return None
            if category == NotificationCategory.AI and not prefs.ai_updates_enabled:
                return None
            if category == NotificationCategory.PAYMENT and not prefs.payment_updates_enabled:
                return None
            if category == NotificationCategory.REPORT and not prefs.report_updates_enabled:
                return None
            if category in (NotificationCategory.ACCOUNT, NotificationCategory.AUTHENTICATION) and not prefs.account_updates_enabled:
                return None
            if category == NotificationCategory.SYSTEM and not prefs.system_updates_enabled:
                return None

        # Create Notification Record
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            channel=channel,
            priority=priority,
            category=category,
            action_url=action_url,
            entity_type=entity_type,
            entity_id=entity_id,
            status=NotificationStatus.PENDING
        )
        notification = await self.notification_repo.create(db, notification)

        # Send via provider
        provider = self.providers.get(channel)
        if not provider:
            logger.error(f"No provider found for channel {channel}")
            notification.status = NotificationStatus.FAILED
            await db.commit()
            await self._log_delivery(db, str(notification.id), NotificationStatus.FAILED, "UNKNOWN", "Provider not configured")
            return notification

        notification.status = NotificationStatus.SENDING
        await db.commit()

        success = await provider.send(notification, db=db)
        
        if success:
            notification.status = NotificationStatus.SENT
            await db.commit()
            await self._log_delivery(db, str(notification.id), NotificationStatus.SENT, provider.__class__.__name__)
        else:
            notification.status = NotificationStatus.FAILED
            await db.commit()
            await self._log_delivery(db, str(notification.id), NotificationStatus.FAILED, provider.__class__.__name__, "Delivery failed")

        return notification

    async def notify_admins(
        self, db: AsyncSession, title: str, message: str, priority: int = 1, 
        channel: NotificationChannel = NotificationChannel.IN_APP,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        action_url: str = None
    ):
        """
        Sends a notification to all users with the role of 'admin'.
        """
        from app.models.user import User
        from app.models.role import Role
        from sqlalchemy import select
        
        try:
            result = await db.execute(select(User).join(Role, User.role_id == Role.id).filter(Role.name == "admin"))
            admins = result.scalars().all()
            
            for admin in admins:
                await self.send_notification(
                    db, str(admin.id), channel, title, message, priority, 
                    category=category, action_url=action_url
                )
                
            logger.info(f"Successfully notified {len(admins)} admins: {title}")
        except Exception as e:
            logger.error(f"Failed to notify admins: {str(e)}")

    async def send_templated_notification(
        self, db: AsyncSession, user_id: str, channel: NotificationChannel, 
        template_name: str, context: Dict[str, Any], priority: int = 0,
        category: NotificationCategory = NotificationCategory.NOTIFICATION
    ) -> Notification:
        try:
            subject, body = await self.template_service.get_rendered_content(db, template_name, context)
            return await self.send_notification(db, user_id, channel, title=subject, message=body, priority=priority, category=category)
        except ValueError as e:
            logger.error(f"Template rendering failed: {e}")
            return None
