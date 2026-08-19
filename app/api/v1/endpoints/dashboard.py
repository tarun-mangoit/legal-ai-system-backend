from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.dashboard import ClientDashboardResponse, AdvocateDashboardResponse, AdminDashboardResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter()

@router.get("/client", response_model=ClientDashboardResponse)
async def get_client_dashboard(
    current_user: User = Depends(require_roles(["client"])),
    db: AsyncSession = Depends(get_db)
):
    return await dashboard_service.get_client_dashboard(db, str(current_user.id))

@router.get("/advocate", response_model=AdvocateDashboardResponse)
async def get_advocate_dashboard(
    current_user: User = Depends(require_roles(["advocate"])),
    db: AsyncSession = Depends(get_db)
):
    return await dashboard_service.get_advocate_dashboard(db, str(current_user.id))

@router.get("/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    return await dashboard_service.get_admin_dashboard(db)
