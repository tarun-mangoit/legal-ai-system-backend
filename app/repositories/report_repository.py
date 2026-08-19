from typing import List, Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportTemplate, ReportVersion, ReportStatus

class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_report(self, report_id: uuid.UUID) -> Optional[Report]:
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalars().first()

    async def get_reports_by_case(self, case_id: uuid.UUID) -> List[Report]:
        result = await self.db.execute(
            select(Report).where(Report.case_id == case_id).order_by(Report.created_at.desc())
        )
        return result.scalars().all()

    async def create_report(self, report_data: dict) -> Report:
        report = Report(**report_data)
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def update_report(self, report_id: uuid.UUID, update_data: dict) -> Optional[Report]:
        report = await self.get_report(report_id)
        if report:
            for key, value in update_data.items():
                setattr(report, key, value)
            await self.db.commit()
            await self.db.refresh(report)
        return report

    async def get_template(self, template_id: uuid.UUID) -> Optional[ReportTemplate]:
        result = await self.db.execute(select(ReportTemplate).where(ReportTemplate.id == template_id))
        return result.scalars().first()

    async def create_report_version(self, version_data: dict) -> ReportVersion:
        version = ReportVersion(**version_data)
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def get_templates(self) -> List[ReportTemplate]:
        result = await self.db.execute(select(ReportTemplate))
        return result.scalars().all()
