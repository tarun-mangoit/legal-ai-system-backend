from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid

from app.database.session import get_db
from app.models.blog import Blog, BlogCategory, BlogTag, BlogComment, BlogStatus, blog_tags
from app.schemas.blog import (
    BlogCreate, BlogUpdate, BlogResponse, BlogDetailResponse,
    SidebarDataResponse, BlogCategoryWithCount, BlogCategoryResponse,
    BlogTagResponse, BlogCommentCreate, BlogCommentResponse,
    BlogCategoryCreate, BlogTagCreate, BlogNavResponse,
    AdminCommentResponse
)
from app.dependencies import get_current_user, RequireAdmin
from app.models.user import User
from app.core.local_storage_provider import LocalStorageProvider

router = APIRouter()

@router.get("", response_model=List[BlogResponse])
async def get_blogs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category_slug: Optional[str] = None,
    tag_slug: Optional[str] = None
) -> Any:
    """
    Retrieve published blogs for public view.
    """
    query = select(Blog).filter(Blog.status == BlogStatus.PUBLISHED).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags)
    )
    
    if search:
        query = query.filter(Blog.title.ilike(f"%{search}%"))
    if category_slug:
        query = query.join(BlogCategory).filter(BlogCategory.slug == category_slug)
    if tag_slug:
        query = query.join(Blog.tags).filter(BlogTag.slug == tag_slug)
        
    query = query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    blogs = result.scalars().unique().all()
    return blogs

@router.get("/sidebar-data", response_model=SidebarDataResponse)
async def get_sidebar_data(db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get categories with counts, recent posts, and all tags for the sidebar.
    """
    # Categories with count of published blogs
    categories_query = select(
        BlogCategory, func.count(Blog.id).label('count')
    ).outerjoin(Blog, (Blog.category_id == BlogCategory.id) & (Blog.status == BlogStatus.PUBLISHED)) \
     .group_by(BlogCategory.id)
     
    cat_result = await db.execute(categories_query)
    
    categories = [
        BlogCategoryWithCount(
            id=cat.id, name=cat.name, slug=cat.slug, created_at=cat.created_at, count=count
        ) for cat, count in cat_result.all()
    ]
    
    # Recent Posts
    rp_query = select(Blog).filter(Blog.status == BlogStatus.PUBLISHED).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags)
    ).order_by(Blog.created_at.desc()).limit(3)
    rp_result = await db.execute(rp_query)
    recent_posts = rp_result.scalars().all()
                     
    # Tags
    tags_query = select(BlogTag)
    tags_result = await db.execute(tags_query)
    tags = tags_result.scalars().all()
    
    return SidebarDataResponse(
        categories=categories,
        recent_posts=recent_posts,
        tags=tags
    )

@router.get("/{slug}", response_model=BlogDetailResponse)
async def get_blog(slug: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get a single published blog by slug.
    """
    query = select(Blog).filter(Blog.slug == slug, Blog.status == BlogStatus.PUBLISHED).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags),
        selectinload(Blog.comments)
    )
    result = await db.execute(query)
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    # Only return approved comments
    blog.comments = [c for c in blog.comments if c.is_approved]
    
    # Fetch previous/next
    prev_query = select(Blog).filter(Blog.status == BlogStatus.PUBLISHED, Blog.created_at < blog.created_at).order_by(Blog.created_at.desc()).limit(1)
    next_query = select(Blog).filter(Blog.status == BlogStatus.PUBLISHED, Blog.created_at > blog.created_at).order_by(Blog.created_at.asc()).limit(1)
    
    prev_res = await db.execute(prev_query)
    next_res = await db.execute(next_query)
    
    prev_blog = prev_res.scalars().first()
    next_blog = next_res.scalars().first()
    
    return BlogDetailResponse(
        **BlogResponse.model_validate(blog).model_dump(),
        comments=[BlogCommentResponse.model_validate(c) for c in blog.comments],
        previous_post=BlogNavResponse(title=prev_blog.title, slug=prev_blog.slug) if prev_blog else None,
        next_post=BlogNavResponse(title=next_blog.title, slug=next_blog.slug) if next_blog else None
    )

@router.post("/{blog_id}/comments", response_model=BlogCommentResponse)
async def add_comment(
    blog_id: uuid.UUID,
    comment_in: BlogCommentCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add a new comment to a blog post.
    """
    query = select(Blog).filter(Blog.id == blog_id, Blog.status == BlogStatus.PUBLISHED)
    result = await db.execute(query)
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    comment = BlogComment(
        blog_id=blog_id,
        **comment_in.model_dump()
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment

# Admin Routes below

@router.get("/admin/categories", dependencies=[RequireAdmin])
async def get_admin_categories(
    search: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    from sqlalchemy import or_, desc, asc
    skip = (page - 1) * page_size
    
    query = select(BlogCategory)
    count_query = select(func.count(BlogCategory.id))
    
    if search:
        condition = or_(BlogCategory.name.ilike(f"%{search}%"), BlogCategory.slug.ilike(f"%{search}%"))
        query = query.where(condition)
        count_query = count_query.where(condition)
        
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    if hasattr(BlogCategory, sort_by):
        column = getattr(BlogCategory, sort_by)
        query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
    else:
        query = query.order_by(BlogCategory.created_at.desc())
        
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [BlogCategoryResponse.model_validate(i).model_dump(mode='json') for i in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.post("/admin/categories", response_model=BlogCategoryResponse, dependencies=[RequireAdmin])
async def create_category(
    category_in: BlogCategoryCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new blog category (Admin only).
    """
    # Generate slug if empty
    slug = category_in.slug or category_in.name.lower().replace(" ", "-")
    db_obj = BlogCategory(
        name=category_in.name,
        slug=slug
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/admin/tags", dependencies=[RequireAdmin])
async def get_admin_tags(
    search: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    from sqlalchemy import or_, desc, asc
    skip = (page - 1) * page_size
    
    query = select(BlogTag)
    count_query = select(func.count(BlogTag.id))
    
    if search:
        condition = or_(BlogTag.name.ilike(f"%{search}%"), BlogTag.slug.ilike(f"%{search}%"))
        query = query.where(condition)
        count_query = count_query.where(condition)
        
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    if hasattr(BlogTag, sort_by):
        column = getattr(BlogTag, sort_by)
        query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
    else:
        query = query.order_by(BlogTag.created_at.desc())
        
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [BlogTagResponse.model_validate(i).model_dump(mode='json') for i in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.post("/admin/tags", response_model=BlogTagResponse, dependencies=[RequireAdmin])
async def create_tag(
    tag_in: BlogTagCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new blog tag (Admin only).
    """
    slug = tag_in.slug or tag_in.name.lower().replace(" ", "-")
    db_obj = BlogTag(
        name=tag_in.name,
        slug=slug
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/admin/posts", dependencies=[RequireAdmin])
async def get_admin_blogs(
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all blogs for admin review (including drafts).
    """
    from sqlalchemy import or_, desc, asc
    skip = (page - 1) * page_size
    
    query = select(Blog).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags)
    )
    count_query = select(func.count(Blog.id))
    
    conditions = []
    if search:
        conditions.append(Blog.title.ilike(f"%{search}%"))
        
    if status == 'published':
        conditions.append(Blog.status == BlogStatus.PUBLISHED)
    elif status == 'draft':
        conditions.append(Blog.status == BlogStatus.DRAFT)
        
    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)
        
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    if hasattr(Blog, sort_by):
        column = getattr(Blog, sort_by)
        query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
    else:
        query = query.order_by(Blog.created_at.desc())
        
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [BlogResponse.model_validate(i).model_dump(mode='json') for i in items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.get("/admin/comments", dependencies=[RequireAdmin])
async def get_all_comments(
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = 'created_at',
    sort_order: str = 'desc',
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all comments for admin review with pagination.
    """
    from sqlalchemy import or_, desc, asc
    skip = (page - 1) * page_size
    
    query = select(BlogComment).options(selectinload(BlogComment.blog))
    count_query = select(func.count(BlogComment.id))
    
    conditions = []
    if search:
        conditions.append(or_(BlogComment.name.ilike(f"%{search}%"), BlogComment.content.ilike(f"%{search}%")))
        
    if status == 'approved':
        conditions.append(BlogComment.is_approved == True)
    elif status == 'pending':
        conditions.append(BlogComment.is_approved == False)
        
    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)
        
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    if hasattr(BlogComment, sort_by):
        column = getattr(BlogComment, sort_by)
        query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
    else:
        query = query.order_by(BlogComment.created_at.desc())
        
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    formatted_items = [
        AdminCommentResponse(
            **{k: getattr(c, k) for k in BlogCommentResponse.model_fields.keys()},
            blog_title=c.blog.title if c.blog else "Unknown",
            blog_slug=c.blog.slug if c.blog else ""
        ).model_dump(mode='json') for c in items
    ]
    
    return {
        "items": formatted_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

@router.put("/admin/comments/{id}/toggle-approval", response_model=BlogCommentResponse, dependencies=[RequireAdmin])
async def toggle_comment_approval(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Toggle a comment's approval status.
    """
    query = select(BlogComment).filter(BlogComment.id == id)
    result = await db.execute(query)
    comment = result.scalars().first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    comment.is_approved = not comment.is_approved
    await db.commit()
    await db.refresh(comment)
    return comment

@router.delete("/admin/comments/{id}", response_model=dict, dependencies=[RequireAdmin])
async def delete_comment(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a comment.
    """
    query = select(BlogComment).filter(BlogComment.id == id)
    result = await db.execute(query)
    comment = result.scalars().first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    await db.delete(comment)
    await db.commit()
    return {"message": "Comment deleted successfully"}

@router.post("/admin/upload-image", response_model=dict, dependencies=[RequireAdmin])
async def upload_blog_image(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload a cover image for a blog post (Admin only).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"blogs/{filename}"
    
    storage = LocalStorageProvider()
    await storage.save_file(file, path)
    
    return {"url": f"/uploads/{path}"}

@router.post("/admin", response_model=BlogResponse, dependencies=[RequireAdmin])
async def create_blog(
    blog_in: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new blog post (Admin only).
    """
    tags = []
    if blog_in.tag_ids:
        query = select(BlogTag).filter(BlogTag.id.in_(blog_in.tag_ids))
        result = await db.execute(query)
        tags = result.scalars().all()
    
    db_obj = Blog(
        title=blog_in.title,
        slug=blog_in.slug,
        excerpt=blog_in.excerpt,
        content=blog_in.content,
        cover_image_url=blog_in.cover_image_url,
        category_id=blog_in.category_id,
        status=blog_in.status,
        author_id=current_user.id
    )
    db_obj.tags = list(tags)
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    # Eager load relationships for response
    refresh_query = select(Blog).filter(Blog.id == db_obj.id).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags)
    )
    result = await db.execute(refresh_query)
    db_obj = result.scalars().first()
    
    return db_obj

@router.put("/admin/{id}", response_model=BlogResponse, dependencies=[RequireAdmin])
async def update_blog(
    id: uuid.UUID,
    blog_in: BlogUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a blog post (Admin only).
    """
    query = select(Blog).filter(Blog.id == id).options(
        selectinload(Blog.tags)
    )
    result = await db.execute(query)
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    update_data = blog_in.model_dump(exclude_unset=True)
    
    if 'tag_ids' in update_data:
        tag_ids = update_data.pop('tag_ids')
        tags_query = select(BlogTag).filter(BlogTag.id.in_(tag_ids))
        tags_result = await db.execute(tags_query)
        blog.tags = list(tags_result.scalars().all())
        
    for field, value in update_data.items():
        setattr(blog, field, value)
        
    await db.commit()
    await db.refresh(blog)
    
    refresh_query = select(Blog).filter(Blog.id == id).options(
        selectinload(Blog.author),
        selectinload(Blog.category),
        selectinload(Blog.tags)
    )
    res = await db.execute(refresh_query)
    blog = res.scalars().first()
    
    return blog

@router.delete("/admin/{id}", response_model=dict, dependencies=[RequireAdmin])
async def delete_blog(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a blog post (Admin only).
    """
    query = select(Blog).filter(Blog.id == id)
    result = await db.execute(query)
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    await db.delete(blog)
    await db.commit()
    return {"message": "Blog deleted successfully"}
