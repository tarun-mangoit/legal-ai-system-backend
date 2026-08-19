from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class CaseAssignment(BaseModel):
    __tablename__ = "case_assignments"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
