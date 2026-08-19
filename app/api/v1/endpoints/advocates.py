from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.dependencies import get_current_user, RequireAdvocate
from app.models.user import User
from app.models.advocate_profile import AdvocateProfile
from app.models.advocate_document import AdvocateDocument
from app.models.audit_log import AuditLog
from app.schemas.advocate import AdvocateFullProfileResponse, AdvocateProfileUpdate, ChangePasswordRequest, PublicAdvocateProfileResponse
import os
import shutil
import uuid
from typing import List
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/me", response_model=AdvocateFullProfileResponse)
async def get_current_advocate_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == current_user.id))
    profile = p_res.scalars().first()
    
    d_res = await db.execute(select(AdvocateDocument).where(AdvocateDocument.user_id == current_user.id))
    documents = d_res.scalars().all()
    
    return {
        "user": current_user,
        "profile": profile,
        "documents": documents
    }

@router.put("/me", response_model=AdvocateFullProfileResponse)
async def update_advocate_profile(
    profile_in: AdvocateProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Log old values
    old_user_vals = {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "address": current_user.address,
        "city": current_user.city,
        "state": current_user.state,
        "country": current_user.country,
        "postal_code": current_user.postal_code,
    }
    
    current_user.first_name = profile_in.first_name
    current_user.last_name = profile_in.last_name
    current_user.phone = profile_in.phone
    current_user.address = profile_in.address
    current_user.city = profile_in.city
    current_user.state = profile_in.state
    current_user.country = profile_in.country
    current_user.postal_code = profile_in.postal_code
    
    p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == current_user.id))
    profile = p_res.scalars().first()
    
    old_profile_vals = {}
    
    if profile:
        old_profile_vals = {
            "bar_council_number": profile.bar_council_number,
            "bar_council_name": profile.bar_council_name,
            "enrollment_date": str(profile.enrollment_date) if profile.enrollment_date else None,
            "years_of_experience": profile.years_of_experience,
            "practice_type": profile.practice_type,
            "primary_practice_areas": profile.primary_practice_areas,
            "secondary_practice_areas": profile.secondary_practice_areas,
            "languages_spoken": profile.languages_spoken,
            "professional_summary": profile.professional_summary,
            "law_firm_name": profile.law_firm_name,
            "office_address": profile.office_address,
            "office_phone": profile.office_phone,
            "website": profile.website,
            "designation": profile.designation
        }
        
        if (profile.bar_council_number != profile_in.bar_council_number or 
            profile.bar_council_name != profile_in.bar_council_name or 
            profile.enrollment_date != profile_in.enrollment_date):
            current_user.status = "REVIEW_REQUIRED"
            
        for key, value in profile_in.dict().items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    else:
        profile = AdvocateProfile(
            user_id=current_user.id,
            bar_council_number=profile_in.bar_council_number,
            bar_council_name=profile_in.bar_council_name,
            enrollment_date=profile_in.enrollment_date,
            years_of_experience=profile_in.years_of_experience,
            practice_type=profile_in.practice_type,
            primary_practice_areas=profile_in.primary_practice_areas,
            secondary_practice_areas=profile_in.secondary_practice_areas,
            languages_spoken=profile_in.languages_spoken,
            professional_summary=profile_in.professional_summary,
            law_firm_name=profile_in.law_firm_name,
            office_address=profile_in.office_address,
            office_phone=profile_in.office_phone,
            website=profile_in.website,
            designation=profile_in.designation
        )
        db.add(profile)
        current_user.status = "REVIEW_REQUIRED"

    new_user_vals = {
        "first_name": profile_in.first_name,
        "last_name": profile_in.last_name,
        "phone": profile_in.phone,
        "address": profile_in.address,
        "city": profile_in.city,
        "state": profile_in.state,
        "country": profile_in.country,
        "postal_code": profile_in.postal_code,
    }
    new_profile_vals = profile_in.dict()
    new_profile_vals['enrollment_date'] = str(new_profile_vals['enrollment_date'])
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="PROFILE_UPDATED",
        old_value={"user": old_user_vals, "profile": old_profile_vals},
        new_value={"user": new_user_vals, "profile": new_profile_vals},
        changed_fields=["profile", "personal_info"]
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(current_user)
    await db.refresh(profile)

    d_res = await db.execute(select(AdvocateDocument).where(AdvocateDocument.user_id == current_user.id))
    documents = d_res.scalars().all()
    
    return {
        "user": current_user,
        "profile": profile,
        "documents": documents
    }

@router.post("/me/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/avif"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Allowed formats: JPG, JPEG, PNG, AVIF")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 5MB")
        
    os.makedirs("uploads/profiles", exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = f"uploads/profiles/{filename}"
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    old_photo = current_user.profile_photo
    current_user.profile_photo = filepath
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="PROFILE_PHOTO_UPDATED",
        old_value={"profile_photo": old_photo},
        new_value={"profile_photo": filepath},
        changed_fields=["profile_photo"]
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Profile photo updated", "profile_photo": filepath}

@router.delete("/me/photo")
async def delete_profile_photo(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.profile_photo and os.path.exists(current_user.profile_photo):
        os.remove(current_user.profile_photo)
        
    current_user.profile_photo = None
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="PROFILE_PHOTO_REMOVED",
        changed_fields=["profile_photo"]
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Profile photo removed"}

@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not pwd_context.verify(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    if data.new_password != data.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    current_user.password_hash = pwd_context.hash(data.new_password)
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        changed_fields=["password_hash"]
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/me/documents")
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    os.makedirs("uploads/documents", exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = f"uploads/documents/{filename}"
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_doc = AdvocateDocument(
        user_id=current_user.id,
        document_type=document_type,
        file_path=filepath,
        file_name=file.filename,
        status="PENDING"
    )
    db.add(new_doc)
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_UPLOADED",
        new_value={"document_type": document_type, "file_name": file.filename},
        changed_fields=["documents"]
    )
    db.add(audit_log)
    
    current_user.status = "REVIEW_REQUIRED"
    
    await db.commit()
    await db.refresh(new_doc)
    
    return {"message": "Document uploaded successfully", "document": new_doc}

@router.put("/me/documents/{document_id}")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_res = await db.execute(select(AdvocateDocument).where(AdvocateDocument.id == document_id, AdvocateDocument.user_id == current_user.id))
    doc = d_res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = f"uploads/documents/{filename}"
    
    os.makedirs("uploads/documents", exist_ok=True)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    old_status = doc.status
    doc.file_path = filepath
    doc.file_name = file.filename
    doc.status = "PENDING"
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_REPLACED",
        old_value={"status": old_status},
        new_value={"file_name": file.filename},
        changed_fields=["document"]
    )
    db.add(audit_log)
    
    if old_status == "VERIFIED":
        current_user.status = "REVIEW_REQUIRED"
        
    await db.commit()
    await db.refresh(doc)
    
    return {"message": "Document replaced successfully", "document": doc}

@router.delete("/me/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_res = await db.execute(select(AdvocateDocument).where(AdvocateDocument.id == document_id, AdvocateDocument.user_id == current_user.id))
    doc = d_res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    await db.delete(doc)
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_DELETED",
        old_value={"document_type": doc.document_type},
        changed_fields=["documents"]
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/{advocate_id}/public", response_model=PublicAdvocateProfileResponse)
async def get_public_advocate_profile(
    advocate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the public profile of an advocate (clients can use this)."""
    # Fetch User
    u_res = await db.execute(select(User).where(User.id == advocate_id))
    user = u_res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Advocate not found")

    # Fetch Profile
    p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == advocate_id))
    profile = p_res.scalars().first()
    
    return {
        "user": user,
        "profile": profile
    }

@router.get("/public/top", response_model=List[PublicAdvocateProfileResponse])
async def get_top_public_advocates(
    db: AsyncSession = Depends(get_db)
):
    from app.models.role import Role
    r_res = await db.execute(select(Role).where(Role.name == 'advocate'))
    advocate_role = r_res.scalars().first()
    
    if not advocate_role:
        return []
        
    u_res = await db.execute(
        select(User)
        .where(User.role_id == advocate_role.id, User.status == 'ACTIVE')
        .order_by(User.created_at.desc())
        .limit(6)
    )
    users = u_res.scalars().all()
    
    result = []
    for user in users:
        p_res = await db.execute(select(AdvocateProfile).where(AdvocateProfile.user_id == user.id))
        profile = p_res.scalars().first()
        result.append({
            "user": user,
            "profile": profile
        })
        
    return result
