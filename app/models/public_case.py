from sqlalchemy import Column, String, Text, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from app.database.session import Base

public_case_tags = Table(
    'public_case_tags',
    Base.metadata,
    Column('public_case_id', ForeignKey('public_cases.id'), primary_key=True),
    Column('tag_id', ForeignKey('public_case_tags_table.id'), primary_key=True)
)

class PublicCaseCategory(BaseModel):
    __tablename__ = "public_case_categories"
    
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    
    cases = relationship("PublicCase", back_populates="category")

class PublicCaseTag(BaseModel):
    __tablename__ = "public_case_tags_table"
    
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    
    cases = relationship("PublicCase", secondary=public_case_tags, back_populates="tags")

class PublicCase(BaseModel):
    __tablename__ = "public_cases"
    
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String, nullable=True)
    category_id = Column(ForeignKey("public_case_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    category = relationship("PublicCaseCategory", back_populates="cases")
    tags = relationship("PublicCaseTag", secondary=public_case_tags, back_populates="cases")
