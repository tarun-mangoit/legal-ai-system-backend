import uuid
import os
import shutil
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc

from app.database.session import get_db
from app.models.hero_slider import HeroSlider
from app.schemas.hero_slider import HeroSliderCreate, HeroSliderUpdate, HeroSliderResponse
from app.dependencies import get_current_user, RequireAdmin

router = APIRouter()

UPLOAD_DIR = "uploads/hero_sliders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/public", response_model=List[HeroSliderResponse])
async def get_public_hero_sliders(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all active hero sliders ordered by display_order.
    """
    query = select(HeroSlider).filter(HeroSlider.is_active == True).order_by(asc(HeroSlider.display_order), HeroSlider.created_at.desc())
    result = await db.execute(query)
    sliders = result.scalars().all()
    return sliders

@router.get("", response_model=List[HeroSliderResponse], dependencies=[RequireAdmin])
async def get_all_hero_sliders(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all hero sliders for admin.
    """
    query = select(HeroSlider).order_by(asc(HeroSlider.display_order), HeroSlider.created_at.desc())
    result = await db.execute(query)
    sliders = result.scalars().all()
    return sliders

@router.post("", response_model=HeroSliderResponse, dependencies=[RequireAdmin])
async def create_hero_slider(
    title: str = Form(...),
    subtitle: str = Form(None),
    button_text: str = Form("Contact Us"),
    target_url: str = Form(...),
    is_active: bool = Form(True),
    display_order: int = Form(0),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new hero slider.
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
        
    ext = image.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    image_url = f"/uploads/hero_sliders/{filename}"
    
    slider = HeroSlider(
        title=title,
        subtitle=subtitle,
        button_text=button_text,
        target_url=target_url,
        is_active=is_active,
        display_order=display_order,
        image_url=image_url
    )
    
    db.add(slider)
    await db.commit()
    await db.refresh(slider)
    return slider

@router.put("/{id}", response_model=HeroSliderResponse, dependencies=[RequireAdmin])
async def update_hero_slider(
    id: uuid.UUID,
    title: str = Form(None),
    subtitle: str = Form(None),
    button_text: str = Form(None),
    target_url: str = Form(None),
    is_active: bool = Form(None),
    display_order: int = Form(None),
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a hero slider.
    """
    query = select(HeroSlider).filter(HeroSlider.id == id)
    result = await db.execute(query)
    slider = result.scalars().first()
    
    if not slider:
        raise HTTPException(status_code=404, detail="Hero Slider not found")
        
    if title is not None: slider.title = title
    if subtitle is not None: slider.subtitle = subtitle
    if button_text is not None: slider.button_text = button_text
    if target_url is not None: slider.target_url = target_url
    if is_active is not None: slider.is_active = is_active
    if display_order is not None: slider.display_order = display_order
    
    if image is not None:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File provided is not an image.")
            
        ext = image.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Optional: remove old image
        # if slider.image_url:
        #     old_path = slider.image_url.lstrip('/')
        #     if os.path.exists(old_path):
        #         os.remove(old_path)
                
        slider.image_url = f"/uploads/hero_sliders/{filename}"
        
    await db.commit()
    await db.refresh(slider)
    return slider

@router.delete("/{id}", response_model=dict, dependencies=[RequireAdmin])
async def delete_hero_slider(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a hero slider.
    """
    query = select(HeroSlider).filter(HeroSlider.id == id)
    result = await db.execute(query)
    slider = result.scalars().first()
    
    if not slider:
        raise HTTPException(status_code=404, detail="Hero Slider not found")
        
    if slider.image_url:
        old_path = slider.image_url.lstrip('/')
        if os.path.exists(old_path):
            os.remove(old_path)
            
    await db.delete(slider)
    await db.commit()
    return {"message": "Hero Slider deleted successfully"}
