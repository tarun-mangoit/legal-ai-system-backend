from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.role import Role
from app.services.notification_events import notification_events
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.services.user_service import user_service
from app.services.role_service import role_service
from app.repositories import refresh_token_repository, user_repository
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import secrets

class RefreshTokenCreate(BaseModel):
    user_id: str
    token_hash: str
    expires_at: datetime

class AuthService:
    async def send_otp(self, db: AsyncSession, email: str):
        existing_user = await user_service.get_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        import random, datetime, smtplib
        from email.mime.text import MIMEText
        from app.models.otp import OTPVerification
        from sqlalchemy import select
        from app.config import settings
        
        otp = str(random.randint(100000, 999999))
        result = await db.execute(select(OTPVerification).where(OTPVerification.email == email))
        otp_record = result.scalars().first()
        
        if not otp_record:
            otp_record = OTPVerification(email=email)
            db.add(otp_record)
            
        otp_record.otp_code = otp
        otp_record.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=20)
        await db.commit()
        
        # Actually send the email via SMTP
        try:
            msg = MIMEText(f"Your OTP code for Legal AI registration is: {otp}\n\nThis code will expire in 20 minutes.")
            msg['Subject'] = 'Legal AI - Registration OTP'
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            print(f"Real email sent to {email} successfully!")
        except Exception as e:
            print(f"Failed to send real email to {email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
            
        return True

    async def verify_otp(self, db: AsyncSession, email: str, otp_code: str):
        from app.models.otp import OTPVerification
        from sqlalchemy import select
        import datetime
        
        result = await db.execute(select(OTPVerification).where(OTPVerification.email == email))
        otp_record = result.scalars().first()
        
        if not otp_record or otp_record.otp_code != otp_code:
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
        if otp_record.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")
            
        return True

    async def register(self, db: AsyncSession, register_data: RegisterRequest) -> User:
        await self.verify_otp(db, register_data.email, register_data.otp_code)
        
        existing_user = await user_service.get_by_email(db, register_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        client_role = await role_service.get_by_name(db, "client")
        if not client_role:
            await role_service.seed_roles(db)
            client_role = await role_service.get_by_name(db, "client")
            
        user_create = UserCreate(
            email=register_data.email,
            password_hash=get_password_hash(register_data.password),
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            phone=register_data.phone,
            address=register_data.address,
            role_id=client_role.id,
            is_verified=True
        )
        user = await user_service.create(db, user_create)
        
        # Trigger welcome notification
        await notification_events.handle_user_registered(
            db=db,
            user_id=str(user.id),
            email=user.email,
            name=f"{user.first_name} {user.last_name}"
        )
        
        from app.models.otp import OTPVerification
        from sqlalchemy import delete
        await db.execute(delete(OTPVerification).where(OTPVerification.email == register_data.email))
        await db.commit()
        
        return user
        
    async def register_advocate(self, db: AsyncSession, data: dict, files: dict):
        email = data.get("email")
        otp_code = data.get("otp_code")
        
        await self.verify_otp(db, email, otp_code)
        
        existing_user = await user_service.get_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        advocate_role = await role_service.get_by_name(db, "advocate")
        if not advocate_role:
            await role_service.seed_roles(db)
            advocate_role = await role_service.get_by_name(db, "advocate")
            
        user_create = UserCreate(
            email=email,
            password_hash=get_password_hash(data.get("password")),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            address=data.get("address_line_1"),
            role_id=advocate_role.id,
            is_verified=True,
        )
        user = await user_service.create(db, user_create)
        
        # We manually update status since UserCreate schema doesn't expose it yet
        user.status = "UNDER_REVIEW"
        user.city = data.get("city")
        user.state = data.get("state")
        user.country = data.get("country")
        user.postal_code = data.get("postal_code")
        
        from app.models.advocate_profile import AdvocateProfile
        from app.models.advocate_document import AdvocateDocument
        import os, shutil
        
        # Parse Dates
        try:
            enrollment_date = datetime.strptime(data.get("enrollment_date"), "%Y-%m-%d").date()
        except:
            enrollment_date = datetime.now().date()
            
        # Parse practice areas
        ppa_raw = data.get("primary_practice_areas", "")
        ppa_list = [area.strip() for area in ppa_raw.split(",")] if isinstance(ppa_raw, str) and ppa_raw else (ppa_raw if isinstance(ppa_raw, list) else [])

        profile = AdvocateProfile(
            user_id=user.id,
            bar_council_number=data.get("bar_council_number"),
            bar_council_name=data.get("bar_council_name"),
            enrollment_date=enrollment_date,
            years_of_experience=int(data.get("years_of_experience", 0)),
            practice_type=data.get("practice_type"),
            primary_practice_areas=ppa_list,
            secondary_practice_areas=data.get("secondary_practice_areas", []),
            languages_spoken=data.get("languages_spoken", []),
            professional_summary=data.get("professional_summary"),
            law_firm_name=data.get("law_firm_name"),
            office_address=data.get("office_address"),
            office_phone=data.get("office_phone"),
            website=data.get("website"),
            linkedin_url=data.get("linkedin_url"),
            designation=data.get("designation")
        )
        db.add(profile)
        
        # Handle File Uploads
        upload_dir = f"uploads/advocates/{user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        for doc_type, file_obj in files.items():
            if file_obj:
                file_ext = os.path.splitext(file_obj.filename)[1]
                file_path = f"{upload_dir}/{doc_type}{file_ext}"
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file_obj.file, buffer)
                
                doc = AdvocateDocument(
                    user_id=user.id,
                    document_type=doc_type,
                    file_path=file_path,
                    file_name=file_obj.filename,
                    status="PENDING"
                )
                db.add(doc)
                
                if doc_type == "PHOTO":
                    user.profile_photo = file_path
                
        # Clean OTP
        from app.models.otp import OTPVerification
        from sqlalchemy import delete
        await db.execute(delete(OTPVerification).where(OTPVerification.email == email))
        await db.commit()
        
        import smtplib
        from email.mime.text import MIMEText
        from app.config import settings
        
        # Send Welcome Email to Advocate
        try:
            advocate_msg = MIMEText(
                f"Hello {data.get('first_name')},\n\n"
                "Thank you for applying to join the Legal AI System as an Advocate.\n"
                "Your application and documents have been received and are currently UNDER REVIEW by our administrative team.\n\n"
                "We will notify you once your account is approved.\n\n"
                "Best Regards,\nLegal AI Team"
            )
            advocate_msg['Subject'] = 'Application Received - Legal AI System'
            advocate_msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            advocate_msg['To'] = email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(advocate_msg)
            print(f"Welcome email sent to advocate {email} successfully!")
        except Exception as e:
            print(f"Failed to send welcome email to advocate {email}: {e}")

        # Send Notification to Admin
        admin_email = "admin_consultationl@yopmail.com"
        try:
            admin_msg = MIMEText(
                f"Hello Admin,\n\n"
                f"A new advocate has submitted an application.\n"
                f"Name: {data.get('first_name')} {data.get('last_name')}\n"
                f"Email: {email}\n\n"
                f"Please log in to the admin dashboard to review their profile and verification documents.\n"
            )
            admin_msg['Subject'] = 'New Advocate Application - Action Required'
            admin_msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            admin_msg['To'] = admin_email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(admin_msg)
            print(f"Admin notification email sent to {admin_email} successfully!")
        except Exception as e:
            print(f"Failed to send admin notification email: {e}")

        # Send In-App Notification to Admin
        try:
            from sqlalchemy import select
            admin_res = await db.execute(select(User).where(User.email == admin_email))
            admin_user = admin_res.scalars().first()
            if admin_user:
                from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationType
                in_app_notif = Notification(
                    user_id=admin_user.id,
                    title="New Advocate Application",
                    message=f"{data.get('first_name')} {data.get('last_name')} has submitted an application to join.",
                    channel=NotificationChannel.IN_APP,
                    type=NotificationType.INFO,
                    status=NotificationStatus.SENT
                )
                db.add(in_app_notif)
                await db.commit()
        except Exception as e:
            print(f"Failed to create admin in-app notification: {e}")
        
        return {"message": "Application submitted successfully", "application_id": str(user.id)}

    async def admin_create_advocate(self, db: AsyncSession, data: dict, files: dict):
        email = data.get("email")
        
        existing_user = await user_service.get_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        advocate_role = await role_service.get_by_name(db, "advocate")
        if not advocate_role:
            await role_service.seed_roles(db)
            advocate_role = await role_service.get_by_name(db, "advocate")
            
        user_create = UserCreate(
            email=email,
            password_hash=get_password_hash(data.get("password")),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            address=data.get("address_line_1"),
            role_id=advocate_role.id,
            is_verified=True,
        )
        user = await user_service.create(db, user_create)
        
        # Admin creates advocate -> immediately ACTIVE and verified
        user.status = "ACTIVE"
        user.city = data.get("city")
        user.state = data.get("state")
        user.country = data.get("country")
        user.postal_code = data.get("postal_code")
        
        from app.models.advocate_profile import AdvocateProfile
        from app.models.advocate_document import AdvocateDocument
        import os, shutil
        
        # Parse Dates
        try:
            enrollment_date = datetime.strptime(data.get("enrollment_date"), "%Y-%m-%d").date()
        except:
            enrollment_date = datetime.now().date()
            
        # Parse practice areas
        ppa_raw = data.get("primary_practice_areas", "")
        ppa_list = [area.strip() for area in ppa_raw.split(",")] if isinstance(ppa_raw, str) and ppa_raw else (ppa_raw if isinstance(ppa_raw, list) else [])

        profile = AdvocateProfile(
            user_id=user.id,
            bar_council_number=data.get("bar_council_number"),
            bar_council_name=data.get("bar_council_name"),
            enrollment_date=enrollment_date,
            years_of_experience=int(data.get("years_of_experience", 0)),
            practice_type=data.get("practice_type"),
            primary_practice_areas=ppa_list,
            secondary_practice_areas=data.get("secondary_practice_areas", []),
            languages_spoken=data.get("languages_spoken", []),
            professional_summary=data.get("professional_summary"),
            law_firm_name=data.get("law_firm_name"),
            office_address=data.get("office_address"),
            office_phone=data.get("office_phone"),
            website=data.get("website"),
            linkedin_url=data.get("linkedin_url"),
            designation=data.get("designation")
        )
        db.add(profile)
        
        # Handle File Uploads
        upload_dir = f"uploads/advocates/{user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        for doc_type, file_obj in files.items():
            if file_obj:
                file_ext = os.path.splitext(file_obj.filename)[1]
                file_path = f"{upload_dir}/{doc_type}{file_ext}"
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file_obj.file, buffer)
                
                doc = AdvocateDocument(
                    user_id=user.id,
                    document_type=doc_type,
                    file_path=file_path,
                    file_name=file_obj.filename,
                    status="APPROVED"
                )
                db.add(doc)
                
                if doc_type == "PHOTO":
                    user.profile_photo = file_path
                
        await db.commit()
        
        import smtplib
        from email.mime.text import MIMEText
        from app.config import settings
        
        # Send Welcome Email to Advocate
        try:
            raw_password = data.get("password", "")
            advocate_msg = MIMEText(
                f"Hello {data.get('first_name')},\n\n"
                "An administrator has created an Advocate profile for you on the Legal AI System.\n"
                "Your account is fully approved and active. You can log in using the following credentials:\n\n"
                f"Username: {email}\n"
                f"Password: {raw_password}\n\n"
                "For your security, please log in and change your password as soon as possible.\n\n"
                "Best Regards,\nLegal AI Team"
            )
            advocate_msg['Subject'] = 'Welcome to Legal AI System - Account Created'
            advocate_msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            advocate_msg['To'] = email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(advocate_msg)
            print(f"Welcome email sent to advocate {email} successfully!")
        except Exception as e:
            print(f"Failed to send welcome email to advocate {email}: {e}")

        return {"message": "Advocate created successfully", "advocate_id": str(user.id)}

    async def login(self, db: AsyncSession, login_data: LoginRequest):
        user = await user_service.get_by_email(db, login_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if not verify_password(login_data.password, user.password_hash):
            user.failed_login_attempts += 1
            await db.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")
            
        user.last_login = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        await db.commit()
        
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        refresh_token_db = RefreshTokenCreate(
            user_id=str(user.id),
            token_hash=get_password_hash(refresh_token),
            expires_at=datetime.now(timezone.utc)
        ) # This is mocked expires_at because jwt handles expiry, but we might want DB expiry too
        
        # better to decode to get exp
        from jose import jwt
        from app.config import settings
        decoded = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp_timestamp = decoded.get("exp")
        
        refresh_token_db = RefreshTokenCreate(
            user_id=str(user.id),
            token_hash=get_password_hash(refresh_token),
            expires_at=datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        )
        await refresh_token_repository.create(db, refresh_token_db)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def logout(self, db: AsyncSession, refresh_token: str):
        # find token in db and revoke
        pass # To be implemented more thoroughly, simple logout just returns success for now
        
    async def generate_reset_token(self, db: AsyncSession, email: str):
        user = await user_service.get_by_email(db, email)
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = get_password_hash(token)
            # expires in 1 hr
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            await db.commit()
            
            reset_url = f"http://localhost:5173/reset-password?token={token}"
            
            # Trigger notification
            await notification_events.handle_password_reset(
                db=db,
                user_id=str(user.id),
                email=user.email,
                reset_link=reset_url
            )
            
        return True

    async def reset_password(self, db: AsyncSession, token: str, new_password: str):
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.reset_token != None))
        users = result.scalars().all()
        
        target_user = None
        for u in users:
            if verify_password(token, u.reset_token):
                target_user = u
                break
                
        if not target_user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
            
        if target_user.reset_token_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Reset token has expired")
            
        target_user.password_hash = get_password_hash(new_password)
        target_user.reset_token = None
        target_user.reset_token_expires = None
        await db.commit()
        
        return True

auth_service = AuthService()
