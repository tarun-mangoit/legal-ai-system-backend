from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc, asc
from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime

from app.database.session import get_db
from app.dependencies import get_current_user, RequireAdmin
from app.models.user import User
from app.models.role import Role
from app.models.advocate_profile import AdvocateProfile
from app.models.advocate_document import AdvocateDocument
from app.models.audit_log import AuditLog
from app.repositories.notification_repository import NotificationRepository
from app.models.notification import NotificationDeliveryLog

router = APIRouter()

class AdminActionRequest(BaseModel):
    remarks: str

class UserStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None

@router.get("/notifications")
async def get_admin_notifications(
    channel: Optional[str] = Query(None, description="Filter by channel (e.g., EMAIL)"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., FAILED, SENT)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    """Get all notifications across the system for admin audit/outbox."""
    repo = NotificationRepository()
    skip = (page - 1) * page_size
    
    notifications = await repo.get_all_for_admin(db, channel=channel, status=status, skip=skip, limit=page_size)
    total_count = await repo.count_all_for_admin(db, channel=channel, status=status)
    
    items = []
    for n in notifications:
        items.append({
            "id": str(n.id),
            "user_id": str(n.user_id),
            "recipient_name": f"{n.user.first_name} {n.user.last_name}" if n.user else "Unknown",
            "recipient_email": n.user.email if n.user else "Unknown",
            "title": n.title,
            "category": n.category,
            "channel": n.channel,
            "status": n.status,
            "created_at": n.created_at,
            "read_at": n.read_at
        })
        
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }
    }

@router.get("/notifications/{notification_id}")
async def get_admin_notification_detail(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    from sqlalchemy.orm import selectinload
    
    # Query with delivery logs
    query = select(NotificationRepository().get_by_id.__annotations__.get('return')).where(
        NotificationRepository().get_by_id.__annotations__.get('return').__args__[0].id == notification_id
    ) # A bit hacky, let's just use direct import for model
    
    from app.models.notification import Notification
    query = select(Notification).options(
        selectinload(Notification.user),
        selectinload(Notification.delivery_logs)
    ).where(Notification.id == notification_id)
    
    result = await db.execute(query)
    n = result.scalars().first()
    
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    logs = [{"status": l.status, "provider": l.provider, "error_message": l.error_message, "created_at": l.created_at} for l in n.delivery_logs]
    
    return {
        "id": str(n.id),
        "recipient_name": f"{n.user.first_name} {n.user.last_name}" if n.user else "Unknown",
        "recipient_email": n.user.email if n.user else "Unknown",
        "title": n.title,
        "message": n.message,
        "category": n.category,
        "channel": n.channel,
        "status": n.status,
        "created_at": n.created_at,
        "read_at": n.read_at,
        "delivery_logs": logs
    }

@router.get("/advocate-applications")
async def get_advocate_applications(
    search: Optional[str] = None,
    status: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    query = select(User).join(Role, User.role_id == Role.id).outerjoin(AdvocateProfile, User.id == AdvocateProfile.user_id).where(Role.name == "advocate")
    
    if status:
        query = query.where(User.status == status)
        
    if created_from:
        try:
            from_date = datetime.fromisoformat(created_from)
            query = query.where(User.created_at >= from_date)
        except ValueError:
            pass
            
    if created_to:
        try:
            to_date = datetime.fromisoformat(created_to)
            query = query.where(User.created_at <= to_date)
        except ValueError:
            pass
        
    if search:
        search_term = f"%{search}%"
        query = query.where(or_(
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
            User.email.ilike(search_term),
            AdvocateProfile.bar_council_number.ilike(search_term)
        ))
        
    # Count total
    total_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(total_query)
    total_count = total_res.scalar_one()

    # Sorting
    valid_sort_fields = {
        "first_name": User.first_name,
        "last_name": User.last_name,
        "email": User.email,
        "status": User.status,
        "created_at": User.created_at,
    }
    
    sort_column = valid_sort_fields.get(sort_by, User.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
        
    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Load profile manually for the returned page
    apps = []
    for u in users:
        p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == u.id))
        prof = p_res.scalars().first()
        
        apps.append({
            "id": str(u.id),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "status": u.status,
            "bar_council_number": prof.bar_council_number if prof else None,
            "created_at": u.created_at
        })
        
    return {
        "items": apps,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": (page * page_size) < total_count,
            "has_previous": page > 1
        }
    }

@router.post("/advocates", status_code=201)
async def create_advocate_by_admin(
    data: str = Form(...),
    bar_certificate: UploadFile = File(...),
    photo_id: UploadFile = File(...),
    photo: UploadFile = File(...),
    resume: UploadFile = File(None),
    degree: UploadFile = File(None),
    current_admin: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    import json
    from app.services.auth_service import auth_service
    
    parsed_data = json.loads(data)
    files = {
        "BAR_CERTIFICATE": bar_certificate,
        "PHOTO_ID": photo_id,
        "PHOTO": photo,
        "RESUME": resume,
        "DEGREE": degree
    }
    return await auth_service.admin_create_advocate(db, parsed_data, files)

@router.get("/advocate-applications/{user_id}")
async def get_advocate_application_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Application not found")
        
    p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == user.id))
    profile = p_res.scalars().first()
    
    d_res = await db.execute(select(AdvocateDocument).where(AdvocateDocument.user_id == user.id))
    documents = d_res.scalars().all()
    
    return {
        "user": user,
        "profile": profile,
        "documents": documents
    }

@router.post("/advocate-applications/{user_id}/approve")
async def approve_application(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Application not found")
        
    user.status = "ACTIVE"
    await db.commit()
    
    import smtplib
    from email.mime.text import MIMEText
    from app.config import settings
    
    try:
        msg = MIMEText(f"Hello {user.first_name},\n\nYour advocate registration has been approved! You can now log in to the Advocate Dashboard.")
        msg['Subject'] = 'Legal AI - Application Approved'
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = user.email

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        
    return {"message": "Application approved successfully"}

@router.post("/advocate-applications/{user_id}/reject")
async def reject_application(
    user_id: str,
    action: AdminActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Application not found")
        
    user.status = "REJECTED"
    await db.commit()
    
    return {"message": "Application rejected"}

@router.get("/users")
async def get_all_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    # Base query for all users with their roles
    query = select(User, Role).outerjoin(Role, User.role_id == Role.id)

    # Filtering
    if role:
        if role.lower() not in ["client", "advocate", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role filter")
        query = query.where(func.lower(Role.name) == role.lower())
    
    if status:
        query = query.where(func.lower(User.status) == status.lower())
        
    if created_from:
        try:
            from_date = datetime.fromisoformat(created_from)
            query = query.where(User.created_at >= from_date)
        except ValueError:
            pass
            
    if created_to:
        try:
            to_date = datetime.fromisoformat(created_to)
            query = query.where(User.created_at <= to_date)
        except ValueError:
            pass
            
    if search:
        search_term = f"%{search}%"
        search_conditions = or_(
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
            User.email.ilike(search_term),
            User.phone.ilike(search_term),
            User.id.cast(str).ilike(search_term)
        )
        query = query.where(search_conditions)

    # Summary Stats (Total, Clients, Advocates, Admins)
    # Note: For performance on huge datasets, we'd do a separate GROUP BY query.
    # For now, we count total matches.
    total_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(total_query)
    total_count = total_res.scalar_one()
    
    # Detailed summary counts (if no filters are applied, or we can just count overall)
    # We will do a separate count for summary cards to always show total platform stats
    summary_query = select(Role.name, func.count(User.id)).outerjoin(Role, User.role_id == Role.id).group_by(Role.name)
    summary_res = await db.execute(summary_query)
    summary_data = summary_res.all()
    
    summary = {
        "total": 0,
        "client": 0,
        "advocate": 0,
        "admin": 0
    }
    for r_name, count in summary_data:
        summary["total"] += count
        if r_name and r_name.lower() in summary:
            summary[r_name.lower()] = count

    # Sorting
    valid_sort_fields = {
        "name": User.first_name,
        "email": User.email,
        "role": Role.name,
        "status": User.status,
        "created_at": User.created_at,
        "last_login_at": User.last_login
    }
    
    sort_column = valid_sort_fields.get(sort_by, User.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.all()
    
    items = []
    for u, r in users:
        items.append({
            "id": str(u.id),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "phone": u.phone,
            "role": r.name if r else "client",
            "status": u.status,
            "created_at": u.created_at,
            "last_login_at": u.last_login,
            "profile_photo": u.profile_photo
        })
        
    return {
        "items": items,
        "summary": summary,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": (page * page_size) < total_count,
            "has_previous": page > 1
        }
    }

@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    result = await db.execute(select(User, Role).outerjoin(Role, User.role_id == Role.id).where(User.id == user_id))
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    u, r = row
    return {
        "id": str(u.id),
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "phone": u.phone,
        "role": r.name if r else "client",
        "status": u.status,
        "created_at": u.created_at,
        "last_login_at": u.last_login,
        "profile_photo": u.profile_photo,
        "address": getattr(u, 'address', None),
        "city": getattr(u, 'city', None),
        "state": getattr(u, 'state', None),
        "country": getattr(u, 'country', None),
        "postal_code": getattr(u, 'postal_code', None)
    }

@router.post("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    action: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_status = target_user.status
    target_user.status = action.status.upper()
    
    # Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_USER_STATUS",
        changed_fields={"status": True},
        old_value={"status": old_status},
        new_value={"status": target_user.status, "reason": action.reason},
        metadata={"target_user_id": str(target_user.id)}
    )
    db.add(audit)
    
    await db.commit()
    return {"message": f"User status updated to {target_user.status}"}

class AdminProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

@router.get("/me")
async def get_current_admin_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    return {
        "user": current_user
    }

@router.put("/me")
async def update_admin_profile(
    profile_in: AdminProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    current_user.first_name = profile_in.first_name
    current_user.last_name = profile_in.last_name
    current_user.phone = profile_in.phone
    current_user.address = profile_in.address
    current_user.city = profile_in.city
    current_user.state = profile_in.state
    current_user.country = profile_in.country
    current_user.postal_code = profile_in.postal_code
    
    await db.commit()
    await db.refresh(current_user)
    return {"user": current_user}

from app.schemas.advocate import ChangePasswordRequest

@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = RequireAdmin
):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    if not pwd_context.verify(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    if data.new_password != data.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    current_user.password_hash = pwd_context.hash(data.new_password)
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="ADMIN_PASSWORD_CHANGED",
        changed_fields=["password_hash"]
    )
    db.add(audit_log)
    await db.commit()
    return {"message": "Password updated successfully"}
