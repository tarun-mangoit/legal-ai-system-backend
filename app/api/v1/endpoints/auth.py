from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
from app.database.session import get_db
from app.schemas.auth import (
    TokenResponse,
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    OTPRequest,
    VerifyOTPRequest
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/request-otp")
async def request_otp(
    otp_data: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    await auth_service.send_otp(db, otp_data.email)
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
async def verify_otp(
    verify_data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    await auth_service.verify_otp(db, verify_data.email, verify_data.otp_code)
    return {"message": "OTP verified successfully"}

@router.post("/advocate/register", status_code=status.HTTP_201_CREATED)
async def advocate_register(
    data: str = Form(...),
    bar_certificate: UploadFile = File(...),
    photo_id: UploadFile = File(...),
    photo: UploadFile = File(...),
    resume: UploadFile = File(None),
    degree: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    # data is a JSON string containing the profile info
    parsed_data = json.loads(data)
    files = {
        "BAR_CERTIFICATE": bar_certificate,
        "PHOTO_ID": photo_id,
        "PHOTO": photo,
        "RESUME": resume,
        "DEGREE": degree
    }
    return await auth_service.register_advocate(db, parsed_data, files)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.register(db, register_data)

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.login(db, login_data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    from app.core.security import create_access_token, create_refresh_token
    from jose import jwt, JWTError
    from app.config import settings

    try:
        payload = jwt.decode(refresh_data.refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
@router.post("/logout")
async def logout(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    await auth_service.logout(db, refresh_data.refresh_token)
    return {"message": "Successfully logged out"}

@router.post("/forgot-password")
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    await auth_service.generate_reset_token(db, forgot_data.email)
    return {"message": "Password reset email sent (mocked)"}

@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    await auth_service.reset_password(db, reset_data.token, reset_data.new_password)
    return {"message": "Password reset successfully"}

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role_id": str(current_user.role_id) if current_user.role_id else None,
        "role": role.name if role else "client"
    }
