from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.blog import BlogStatus
from app.schemas.user import UserResponse

# -----------------
# Blog Category
# -----------------
class BlogCategoryBase(BaseModel):
    name: str
    slug: str

class BlogCategoryCreate(BlogCategoryBase):
    pass

class BlogCategoryResponse(BlogCategoryBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class BlogCategoryWithCount(BlogCategoryResponse):
    count: int

# -----------------
# Blog Tag
# -----------------
class BlogTagBase(BaseModel):
    name: str
    slug: str

class BlogTagCreate(BlogTagBase):
    pass

class BlogTagResponse(BlogTagBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# -----------------
# Blog Comment
# -----------------
class BlogCommentBase(BaseModel):
    name: str
    email: str
    website: Optional[str] = None
    content: str

class BlogCommentCreate(BlogCommentBase):
    pass

class BlogCommentResponse(BlogCommentBase):
    id: UUID
    is_approved: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AdminCommentResponse(BlogCommentResponse):
    blog_title: str
    blog_slug: str

# -----------------
# Blog Navigation
# -----------------
class BlogNavResponse(BaseModel):
    title: str
    slug: str

# -----------------
# Blog
# -----------------
class BlogBase(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    cover_image_url: Optional[str] = None
    category_id: Optional[UUID] = None
    status: BlogStatus = BlogStatus.DRAFT

class BlogCreate(BlogBase):
    tag_ids: List[UUID] = []

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[UUID] = None
    status: Optional[BlogStatus] = None
    tag_ids: Optional[List[UUID]] = None

class BlogResponse(BlogBase):
    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested relationships
    author: Optional[UserResponse] = None
    category: Optional[BlogCategoryResponse] = None
    tags: List[BlogTagResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class BlogDetailResponse(BlogResponse):
    comments: List[BlogCommentResponse] = []
    previous_post: Optional[BlogNavResponse] = None
    next_post: Optional[BlogNavResponse] = None

class SidebarDataResponse(BaseModel):
    categories: List[BlogCategoryWithCount]
    recent_posts: List[BlogResponse]
    tags: List[BlogTagResponse]
