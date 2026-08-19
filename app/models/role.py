from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel

class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    permissions = Column(JSONB)
