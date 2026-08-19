from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.dashboard_repository import dashboard_repository
from app.schemas.dashboard import ClientDashboardResponse, AdvocateDashboardResponse, AdminDashboardResponse

class DashboardService:
    async def get_client_dashboard(self, db: AsyncSession, user_id: str) -> ClientDashboardResponse:
        data = await dashboard_repository.get_client_stats(db, user_id)
        return ClientDashboardResponse(**data)

    async def get_advocate_dashboard(self, db: AsyncSession, user_id: str) -> AdvocateDashboardResponse:
        data = await dashboard_repository.get_advocate_stats(db, user_id)
        return AdvocateDashboardResponse(**data)

    async def get_admin_dashboard(self, db: AsyncSession) -> AdminDashboardResponse:
        data = await dashboard_repository.get_admin_stats(db)
        return AdminDashboardResponse(**data)

dashboard_service = DashboardService()
