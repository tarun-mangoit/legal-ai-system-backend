import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.report_service import ReportService
from app.services.pdf_service import PDFService
from app.services.storage.local import LocalStorageProvider
from app.schemas.report import ReportResponse, ReportTemplateResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    storage = LocalStorageProvider()
    pdf_service = PDFService(storage)
    return ReportService(db, pdf_service)

@router.get("/templates", response_model=List[ReportTemplateResponse])
async def get_templates(service: ReportService = Depends(get_report_service)):
    return await service.get_templates()

@router.post("/generate/{case_id}", response_model=ReportResponse)
async def generate_report(
    case_id: uuid.UUID,
    template_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    return await service.generate_report(case_id, template_id, current_user.id)

@router.get("/case/{case_id}", response_model=List[ReportResponse])
async def get_reports_by_case(
    case_id: uuid.UUID,
    service: ReportService = Depends(get_report_service)
):
    return await service.get_reports_by_case(case_id)

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service)
):
    return await service.get_report(report_id)

@router.get("/download/{report_id}")
async def download_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service)
):
    report = await service.get_report(report_id)
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Since LocalStorageProvider saves with the base path included, report.file_path is the exact path
    import os
    full_path = report.file_path
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File missing on disk")
        
    return FileResponse(full_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")
