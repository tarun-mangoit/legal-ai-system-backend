from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import NotificationPreference
from app.schemas.notification import (
    NotificationResponse, NotificationListResponse, NotificationPreferenceResponse,
    NotificationPreferenceUpdate, MarkAsReadResponse, MarkAllAsReadResponse
)
from app.repositories.notification_repository import NotificationRepository, NotificationPreferenceRepository
from app.models.notification import PushSubscription
from pydantic import BaseModel

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_name: str = "Unknown Device"
    browser: str = "Unknown Browser"

router = APIRouter()

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve notifications for the current user."""
    repo = NotificationRepository()
    notifications = await repo.get_by_user(db, str(current_user.id), unread_only, skip, limit)
    
    # Fast count of unread (if full unread count is needed, a separate query could be optimized)
    unread_count = sum(1 for n in notifications if not n.is_read)
    
    return NotificationListResponse(
        items=notifications,
        total=len(notifications),
        unread_count=unread_count
    )

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve notification preferences for the current user."""
    repo = NotificationPreferenceRepository()
    prefs = await repo.get_by_user(db, str(current_user.id))
    if not prefs:
        # Return default preferences if none exist
        return NotificationPreferenceResponse(
            user_id=current_user.id,
            email_enabled=True,
            in_app_enabled=True,
            sms_enabled=False,
            whatsapp_enabled=False,
            push_enabled=False,
            case_updates_enabled=True,
            document_updates_enabled=True,
            ai_updates_enabled=True,
            report_updates_enabled=True,
            payment_updates_enabled=True,
            account_updates_enabled=True,
            marketing_updates_enabled=False,
            system_updates_enabled=True
        )
    return prefs

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    prefs_in: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update notification preferences for the current user."""
    repo = NotificationPreferenceRepository()
    preference = NotificationPreference(
        user_id=current_user.id,
        email_enabled=prefs_in.email_enabled,
        in_app_enabled=prefs_in.in_app_enabled,
        sms_enabled=prefs_in.sms_enabled,
        whatsapp_enabled=prefs_in.whatsapp_enabled,
        push_enabled=prefs_in.push_enabled,
        case_updates_enabled=prefs_in.case_updates_enabled,
        document_updates_enabled=prefs_in.document_updates_enabled,
        ai_updates_enabled=prefs_in.ai_updates_enabled,
        report_updates_enabled=prefs_in.report_updates_enabled,
        payment_updates_enabled=prefs_in.payment_updates_enabled,
        account_updates_enabled=prefs_in.account_updates_enabled,
        marketing_updates_enabled=prefs_in.marketing_updates_enabled,
        system_updates_enabled=prefs_in.system_updates_enabled
    )
    prefs = await repo.create_or_update(db, preference)
    return prefs

@router.post("/push/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_push_notification(
    sub_data: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Register a new browser push subscription."""
    # Delete existing subscription with same endpoint to avoid duplicates
    from sqlalchemy import delete
    await db.execute(delete(PushSubscription).where(PushSubscription.endpoint == sub_data.endpoint))
    
    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=sub_data.endpoint,
        p256dh_key=sub_data.p256dh,
        auth_key=sub_data.auth,
        device_name=sub_data.device_name,
        browser=sub_data.browser
    )
    db.add(sub)
    await db.commit()
    return {"message": "Subscription registered successfully"}

@router.delete("/push/subscribe")
async def unsubscribe_push_notification(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Remove a browser push subscription."""
    from sqlalchemy import delete
    result = await db.execute(
        delete(PushSubscription)
        .where(PushSubscription.endpoint == endpoint)
        .where(PushSubscription.user_id == current_user.id)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Subscription removed successfully"}

@router.patch("/{id}/read", response_model=MarkAsReadResponse)
async def mark_notification_as_read(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark a specific notification as read."""
    repo = NotificationRepository()
    notification = await repo.get_by_id(db, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(notification.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
        
    await repo.mark_as_read(db, id)
    return MarkAsReadResponse(success=True, notification_id=notification.id)

@router.patch("/read-all", response_model=MarkAllAsReadResponse)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark all notifications as read for the current user."""
    repo = NotificationRepository()
    updated_count = await repo.mark_all_as_read(db, str(current_user.id))
    return MarkAllAsReadResponse(success=True, updated_count=updated_count)

@router.delete("/{id}")
async def delete_notification(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete a specific notification."""
    repo = NotificationRepository()
    notification = await repo.get_by_id(db, id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(notification.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
        
    success = await repo.delete(db, id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete notification")
    return {"success": True}
