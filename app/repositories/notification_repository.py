from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationPreference, NotificationTemplate, NotificationStatus

class NotificationRepository:
    async def get_by_id(self, db: AsyncSession, id: str) -> Optional[Notification]:
        result = await db.execute(select(Notification).filter(Notification.id == id))
        return result.scalars().first()

    async def get_by_user(self, db: AsyncSession, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 100) -> List[Notification]:
        query = select(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all_for_admin(self, db: AsyncSession, channel: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Notification]:
        from sqlalchemy.orm import joinedload
        query = select(Notification).options(joinedload(Notification.user))
        
        if channel:
            query = query.filter(Notification.channel == channel)
        if status:
            query = query.filter(Notification.status == status)
            
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_all_for_admin(self, db: AsyncSession, channel: Optional[str] = None, status: Optional[str] = None) -> int:
        from sqlalchemy import func
        query = select(func.count()).select_from(Notification)
        
        if channel:
            query = query.filter(Notification.channel == channel)
        if status:
            query = query.filter(Notification.status == status)
            
        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, notification: Notification) -> Notification:
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_as_read(self, db: AsyncSession, id: str) -> Optional[Notification]:
        from datetime import datetime, timezone
        result = await db.execute(
            update(Notification)
            .where(Notification.id == id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
            .returning(Notification)
        )
        await db.commit()
        return result.scalars().first()

    async def mark_all_as_read(self, db: AsyncSession, user_id: str) -> int:
        from datetime import datetime, timezone
        result = await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.commit()
        return result.rowcount

    async def delete(self, db: AsyncSession, id: str) -> bool:
        result = await db.execute(delete(Notification).where(Notification.id == id))
        await db.commit()
        return result.rowcount > 0


class NotificationPreferenceRepository:
    async def get_by_user(self, db: AsyncSession, user_id: str) -> Optional[NotificationPreference]:
        result = await db.execute(select(NotificationPreference).filter(NotificationPreference.user_id == user_id))
        return result.scalars().first()

    async def create_or_update(self, db: AsyncSession, preference: NotificationPreference) -> NotificationPreference:
        existing = await self.get_by_user(db, preference.user_id)
        if existing:
            existing.email_enabled = preference.email_enabled
            existing.in_app_enabled = preference.in_app_enabled
            existing.sms_enabled = preference.sms_enabled
            existing.whatsapp_enabled = preference.whatsapp_enabled
            existing.push_enabled = preference.push_enabled
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            db.add(preference)
            await db.commit()
            await db.refresh(preference)
            return preference


class NotificationTemplateRepository:
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[NotificationTemplate]:
        result = await db.execute(select(NotificationTemplate).filter(NotificationTemplate.name == name))
        return result.scalars().first()

    async def create(self, db: AsyncSession, template: NotificationTemplate) -> NotificationTemplate:
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def get_all(self, db: AsyncSession) -> List[NotificationTemplate]:
        result = await db.execute(select(NotificationTemplate))
        return list(result.scalars().all())
