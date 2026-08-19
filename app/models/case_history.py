from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class CaseHistory(BaseModel):
    __tablename__ = "case_history"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    action_type = Column(String, nullable=False) # e.g., STATUS_CHANGE, ADVOCATE_ASSIGNED, INFO_UPDATED
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="history")
    user = relationship("User", foreign_keys=[changed_by])
