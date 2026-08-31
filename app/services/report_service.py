import uuid
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.report_repository import ReportRepository
from app.models.report import Report, ReportTemplate, ReportStatus, ReportVersion
from app.models.case import Case
from app.models.legal_opinion import LegalOpinion
from app.services.pdf_service import PDFService
import traceback

class ReportService:
    def __init__(self, db: AsyncSession, pdf_service: PDFService):
        self.repository = ReportRepository(db)
        self.pdf_service = pdf_service
        self.db = db

    async def generate_report(self, case_id: uuid.UUID, template_id: uuid.UUID, user_id: uuid.UUID) -> Report:
        # 1. Validate case and opinion
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        case_result = await self.db.execute(select(Case).options(selectinload(Case.client)).where(Case.id == case_id))
        case = case_result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Get finalized opinion
        # In a real app we'd query by case_id, for now we assume there's an opinion relationship or repository method
        # Here we do a simple query
        from sqlalchemy import select
        opinion_result = await self.db.execute(select(LegalOpinion).where(LegalOpinion.case_id == case_id))
        opinion = opinion_result.scalars().first()
        
        from app.models.legal_opinion import OpinionStatus
        if not opinion or opinion.status not in [OpinionStatus.APPROVED, OpinionStatus.DRAFT, OpinionStatus.UNDER_REVIEW, OpinionStatus.REVISED]:
            raise HTTPException(status_code=400, detail="Cannot generate report: No valid opinion exists for this case")

        template = await self.repository.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Report Template not found")

        # 2. Check if report already exists for this case/template
        existing_reports = await self.repository.get_reports_by_case(case_id)
        report = next((r for r in existing_reports if r.template_id == template_id), None)
        
        version = 1
        if report:
            version = report.version + 1
        else:
            # Create base report entry
            report_data = {
                "case_id": case_id,
                "opinion_id": opinion.id,
                "template_id": template_id,
                "generated_by": user_id,
                "version": version,
                "status": ReportStatus.GENERATING
            }
            report = await self.repository.create_report(report_data)

        # Update to generating if it existed
        if report.id:
            await self.repository.update_report(report.id, {"status": ReportStatus.GENERATING, "version": version})

        # 3. Build Context
        context = {
            "case": case,
            "opinion": opinion,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 4. Generate PDF
        try:
            file_name = f"report_{case_id}_{version}.pdf"
            file_path = await self.pdf_service.generate_pdf(template.html_content, context, file_name)
            
            # 5. Save Version and update report
            await self.repository.create_report_version({
                "report_id": report.id,
                "version_number": version,
                "generated_by": user_id,
                "file_path": file_path,
                "storage_key": file_path
            })
            
            await self.repository.update_report(report.id, {
                "status": ReportStatus.COMPLETED,
                "file_path": file_path,
                "storage_key": file_path,
                "generated_at": datetime.utcnow()
            })
            return report
            
        except Exception as e:
            traceback.print_exc()
            await self.repository.update_report(report.id, {"status": ReportStatus.FAILED})
            raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")

    async def get_report(self, report_id: uuid.UUID) -> Report:
        report = await self.repository.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    async def get_reports_by_case(self, case_id: uuid.UUID) -> List[Report]:
        return await self.repository.get_reports_by_case(case_id)

    async def get_templates(self) -> List[ReportTemplate]:
        return await self.repository.get_templates()
