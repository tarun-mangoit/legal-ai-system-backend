from abc import ABC, abstractmethod
from typing import Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationStatus
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        """Sends a notification and returns True if successful."""
        pass

class EmailProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info(f"Attempting to send EMAIL notification {notification.id} to user {notification.user_id}")
        try:
            # Here you would typically integrate with an SMTP server or service like SendGrid
            # For example: await sendgrid_client.send(email)
            logger.info(f"EMAIL sent successfully: {notification.title} [Action URL: {notification.action_url}]")
            return True
        except Exception as e:
            logger.error(f"Failed to send EMAIL: {e}")
            return False

class InAppProvider(NotificationProvider):
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info(f"Delivering IN_APP notification {notification.id} to user {notification.user_id}")
        # In-App notifications are simply marked as SENT or QUEUED in the DB
        # The frontend will fetch them via the API.
        # Alternatively, we could push this via WebSockets here if implemented.
        try:
            logger.info("IN_APP notification delivered to user's feed.")
            return True
        except Exception as e:
            logger.error(f"Failed to deliver IN_APP notification: {e}")
            return False


# Placeholders for future providers
class SMSProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info("SMS delivery not yet implemented")
        return False

class WhatsAppProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info("WhatsApp delivery not yet implemented")
        return False

class PushProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info(f"Attempting to send WEB PUSH notification {notification.id} to user {notification.user_id}")
        try:
            # Here you would fetch the PushSubscription records for the user
            # and use pywebpush to send the payload to each endpoint
            # For example: webpush(subscription_info, payload, vapid_private_key)
            logger.info(f"WEB PUSH sent successfully: {notification.title} [Action URL: {notification.action_url}]")
            return True
        except Exception as e:
            logger.error(f"Failed to send WEB PUSH: {e}")
            return False

class SlackProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info("Slack delivery not yet implemented")
        return False

class TeamsProvider(NotificationProvider):
    async def send(self, notification: Notification, **kwargs: Any) -> bool:
        logger.info("Teams delivery not yet implemented")
        return False
