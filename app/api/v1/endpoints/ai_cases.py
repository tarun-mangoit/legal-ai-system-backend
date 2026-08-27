import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.ai_legal import CaseAnalysisResponse, CaseAnalysisUpdate
from app.models.case_analysis import CaseAnalysis, CaseAnalysisStatus
from app.tasks.ai_tasks import generate_case_analysis_task
from datetime import datetime
from sqlalchemy import select

router = APIRouter()

@router.post("/{case_id}/analysis", response_model=CaseAnalysisResponse)
async def generate_case_analysis(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Check if analysis exists
    result = await db.execute(select(CaseAnalysis).where(CaseAnalysis.case_id == case_id))
    analysis = result.scalars().first()
    
    if analysis:
        # Clear existing data and set to generating
        analysis.status = CaseAnalysisStatus.GENERATING
        analysis.executive_summary = "Generating case analysis in background..."
        analysis.material_facts = None
        analysis.chronology = None
        analysis.legal_issues = None
        analysis.applicable_laws = None
        analysis.evidence_assessment = None
        analysis.strengths = None
        analysis.weaknesses = None
        analysis.risks = None
        analysis.missing_information = None
        analysis.recommendations = None
        analysis.suggested_precedents = None
    else:
        # Create new record
        analysis = CaseAnalysis(
            case_id=case_id,
            status=CaseAnalysisStatus.GENERATING,
            executive_summary="Generating case analysis in background..."
        )
        db.add(analysis)
    
    await db.commit()
    await db.refresh(analysis)
    
    # Dispatch background task
    generate_case_analysis_task.delay(str(case_id), [])
    
    return analysis

@router.get("/{case_id}/analysis", response_model=CaseAnalysisResponse)
async def get_case_analysis(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseAnalysis).where(CaseAnalysis.case_id == case_id))
    analysis = result.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Case analysis not found")
        
    return analysis

@router.put("/{case_id}/analysis", response_model=CaseAnalysisResponse)
async def update_case_analysis(case_id: uuid.UUID, data: CaseAnalysisUpdate, db: AsyncSession = Depends(get_db)):
    # Mock update
    return CaseAnalysisResponse(
        id=uuid.uuid4(),
        case_id=case_id,
        status=CaseAnalysisStatus.READY,
        executive_summary=data.executive_summary or "Updated summary",
        created_at=datetime.utcnow()
    )
