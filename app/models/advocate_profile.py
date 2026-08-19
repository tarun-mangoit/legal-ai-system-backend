from sqlalchemy import Column, String, ForeignKey, Integer, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class AdvocateProfile(BaseModel):
    __tablename__ = "advocate_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    bar_council_number = Column(String, nullable=False)
    bar_council_name = Column(String, nullable=False)
    enrollment_date = Column(Date, nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    
    practice_type = Column(String, nullable=False) # Independent, Law Firm, Corporate
    primary_practice_areas = Column(JSON, nullable=False)
    secondary_practice_areas = Column(JSON, nullable=True)
    languages_spoken = Column(JSON, nullable=True)
    professional_summary = Column(String, nullable=True)
    
    law_firm_name = Column(String, nullable=True)
    office_address = Column(String, nullable=True)
    office_phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    designation = Column(String, nullable=True)
