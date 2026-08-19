import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies import RequireAdmin
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.services.contact_service import contact_service
from app.services.notification_events import notification_service
from app.models.notification import NotificationChannel, NotificationCategory
from app.utils.email import send_email_async

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    contact_in: ContactCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to submit a contact us form.
    """
    # 1. Save submission to database
    submission = await contact_service.create(db, obj_in=contact_in)
    
    # 2. Send real acknowledgment email to the sender
    sender_subject = "Thank you for contacting Legal AI System"
    sender_content = f"Hi {contact_in.name},\n\nThank you for reaching out to us. We have received your message and will get back to you shortly.\n\nBest regards,\nLegal AI System Team"
    await send_email_async(contact_in.email, sender_subject, sender_content)
    
    # 3. Send notification email to all admins
    from app.models.user import User
    from app.models.role import Role
    from sqlalchemy import select
    
    try:
        result = await db.execute(select(User).join(Role, User.role_id == Role.id).filter(Role.name == "admin"))
        admins = result.scalars().all()
        admin_subject = f"New Contact Submission from {contact_in.name}"
        admin_content = f"You have received a new contact submission.\n\nName: {contact_in.name}\nEmail: {contact_in.email}\nPhone: {contact_in.phone}\n\nMessage:\n{contact_in.message}"
        
        for admin in admins:
            if admin.email:
                await send_email_async(admin.email, admin_subject, admin_content)
    except Exception as e:
        logger.error(f"Failed to fetch admins or send admin email: {e}")
    
    # 4. Trigger in-app notification to all admins
    await notification_service.notify_admins(
        db=db,
        title="New Contact Submission",
        message=f"Received a new inquiry from {contact_in.name} ({contact_in.email}).",
        priority=1,
        channel=NotificationChannel.IN_APP,
        category=NotificationCategory.SYSTEM,
        action_url="/admin/contact-submissions"
    )
    
    return submission

@router.get("/admin", response_model=List[ContactResponse], dependencies=[RequireAdmin])
async def get_all_submissions(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to view all contact submissions.
    """
    return await contact_service.get_all(db, skip=skip, limit=limit)

@router.put("/admin/{id}/resolve", response_model=ContactResponse, dependencies=[RequireAdmin])
async def toggle_submission_resolution(
    id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to toggle the resolved status of a submission.
    """
    submission = await contact_service.get_by_id(db, id=id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    updated_submission = await contact_service.update(
        db, 
        id=id, 
        obj_in=ContactUpdate(is_resolved=not submission.is_resolved)
    )
    return updated_submission
