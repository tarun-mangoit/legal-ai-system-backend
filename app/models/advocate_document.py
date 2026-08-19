from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class AdvocateDocument(BaseModel):
    __tablename__ = "advocate_documents"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False) # e.g. BAR_CERTIFICATE, PHOTO_ID, RESUME
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    remarks = Column(String, nullable=True)
