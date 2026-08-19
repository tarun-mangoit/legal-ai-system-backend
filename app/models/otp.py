from sqlalchemy import Column, String, DateTime
from app.models.base import BaseModel

class OTPVerification(BaseModel):
    __tablename__ = "otp_verifications"

    email = Column(String, unique=True, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
