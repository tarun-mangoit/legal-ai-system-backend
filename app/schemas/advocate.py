from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

class AdvocateProfileUpdate(BaseModel):
    # Personal Info
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Professional Info
    bar_council_number: Optional[str] = None
    bar_council_name: Optional[str] = None
    enrollment_date: Optional[date] = None
    years_of_experience: Optional[int] = Field(None, ge=0)
    practice_type: Optional[str] = None
    primary_practice_areas: Optional[List[str]] = None
    secondary_practice_areas: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    professional_summary: Optional[str] = None
    
    # Law Firm Info
    law_firm_name: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None
    website: Optional[str] = None
    designation: Optional[str] = None

class AdvocateDocumentResponse(BaseModel):
    id: UUID
    document_type: str
    file_name: str
    file_path: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AdvocateProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    bar_council_number: str
    bar_council_name: str
    enrollment_date: date
    years_of_experience: int
    practice_type: str
    primary_practice_areas: List[str]
    secondary_practice_areas: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    professional_summary: Optional[str] = None
    law_firm_name: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None
    website: Optional[str] = None
    designation: Optional[str] = None

    class Config:
        from_attributes = True

class AdvocateUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    status: Optional[str] = None
    profile_photo: Optional[str] = None

    class Config:
        from_attributes = True

class AdvocateFullProfileResponse(BaseModel):
    user: AdvocateUserResponse
    profile: Optional[AdvocateProfileResponse] = None
    documents: List[AdvocateDocumentResponse]

class PublicAdvocateUserResponse(BaseModel):
    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    profile_photo: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class PublicAdvocateProfileResponse(BaseModel):
    user: PublicAdvocateUserResponse
    profile: Optional[AdvocateProfileResponse] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr

class VerifyEmailChangeRequest(BaseModel):
    otp: str

class ChangePhoneRequest(BaseModel):
    new_phone: str
