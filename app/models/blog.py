from sqlalchemy import Column, String, Text, ForeignKey, Table, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel
from app.database.session import Base

class BlogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

blog_tags = Table(
    'blog_tags',
    Base.metadata,
    Column('blog_id', ForeignKey('blogs.id'), primary_key=True),
    Column('tag_id', ForeignKey('blog_tags_table.id'), primary_key=True)
)

class BlogCategory(BaseModel):
    __tablename__ = "blog_categories"
    
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    
    blogs = relationship("Blog", back_populates="category")

class BlogTag(BaseModel):
    __tablename__ = "blog_tags_table"
    
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    
    blogs = relationship("Blog", secondary=blog_tags, back_populates="tags")

class Blog(BaseModel):
    __tablename__ = "blogs"
    
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String, nullable=True)
    author_id = Column(ForeignKey("users.id"), nullable=False)
    category_id = Column(ForeignKey("blog_categories.id"), nullable=True)
    status = Column(Enum(BlogStatus), default=BlogStatus.DRAFT)
    
    author = relationship("User")
    category = relationship("BlogCategory", back_populates="blogs")
    tags = relationship("BlogTag", secondary=blog_tags, back_populates="blogs")
    comments = relationship("BlogComment", back_populates="blog", cascade="all, delete-orphan")

class BlogComment(BaseModel):
    __tablename__ = "blog_comments"
    
    blog_id = Column(ForeignKey("blogs.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    website = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    
    blog = relationship("Blog", back_populates="comments")
