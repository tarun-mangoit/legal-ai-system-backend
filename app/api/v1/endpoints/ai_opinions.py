import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.ai_legal import LegalOpinionResponse, LegalOpinionUpdate
from app.models.legal_opinion import LegalOpinion, OpinionStatus
from app.tasks.ai_tasks import generate_legal_opinion_draft_task
from app.services.pdf_service import PDFService
from app.services.storage.local import LocalStorageProvider
from datetime import datetime
from sqlalchemy import select

from app.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role
from app.models.case import Case

router = APIRouter()

@router.get("/legal-opinions", response_model=List[LegalOpinionResponse])
async def get_all_legal_opinions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = await db.get(Role, current_user.role_id)
    stmt = select(LegalOpinion)
    
    if role.name == "advocate":
        stmt = stmt.join(Case, LegalOpinion.case_id == Case.id).where(Case.advocate_id == current_user.id)
    elif role.name == "client":
        stmt = stmt.join(Case, LegalOpinion.case_id == Case.id).where(Case.client_id == current_user.id)
        
    result = await db.execute(stmt)
    opinions = result.scalars().all()
    return opinions

@router.post("/cases/{case_id}/legal-opinion", response_model=LegalOpinionResponse)
async def generate_legal_opinion(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalOpinion).where(LegalOpinion.case_id == case_id))
    opinion = result.scalars().first()
    
    if opinion:
        opinion.status = OpinionStatus.GENERATING
    else:
        opinion = LegalOpinion(
            case_id=case_id,
            status=OpinionStatus.GENERATING,
            version=1
        )
        db.add(opinion)
    
    await db.commit()
    await db.refresh(opinion)

    # Dispatch background task
    generate_legal_opinion_draft_task.delay(str(case_id))
    
    return opinion

@router.get("/cases/{case_id}/legal-opinion", response_model=LegalOpinionResponse)
async def get_legal_opinion(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalOpinion).where(LegalOpinion.case_id == case_id))
    opinion = result.scalars().first()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Legal opinion not found")
        
    return opinion

@router.put("/legal-opinions/{opinion_id}", response_model=LegalOpinionResponse)
async def update_legal_opinion(opinion_id: uuid.UUID, data: LegalOpinionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalOpinion).where(LegalOpinion.id == opinion_id))
    opinion = result.scalars().first()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Legal opinion not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(opinion, key, value)
        
    await db.commit()
    await db.refresh(opinion)
    return opinion

@router.post("/legal-opinions/{opinion_id}/approve", response_model=LegalOpinionResponse)
async def approve_legal_opinion(opinion_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalOpinion).where(LegalOpinion.id == opinion_id))
    opinion = result.scalars().first()
    
    if not opinion:
        raise HTTPException(status_code=404, detail="Legal opinion not found")
        
    opinion.status = OpinionStatus.FINALIZED if hasattr(OpinionStatus, 'FINALIZED') else OpinionStatus.APPROVED
    opinion.approved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(opinion)
    return opinion

@router.get("/legal-opinions/{opinion_id}/versions", response_model=List[dict])
async def get_legal_opinion_versions(opinion_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # To implement fully we would query LegalOpinionVersion table. For now return empty list or mock.
    return []

@router.post("/legal-opinions/{opinion_id}/pdf", response_model=dict)
async def generate_legal_opinion_pdf(opinion_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Create an instance of the service
    storage = LocalStorageProvider(base_path="uploads")
    pdf_service = PDFService(storage)
    
    # Mock data fetch - in reality we would fetch from DB
    mock_opinion = LegalOpinionResponse(
        id=opinion_id,
        case_id=uuid.uuid4(),
        version=1,
        status=OpinionStatus.APPROVED,
        brief_facts="The client entered into an agreement on Jan 1, 2025. The opposing party failed to deliver goods.",
        issues=["Whether the opposing party breached the contract?"],
        applicable_law=["Contract Act, 1872"],
        legal_analysis="Based on the facts, there is a clear breach of Section 73...",
        conclusion="The client has a strong case for claiming damages.",
        winning_probability=75,
        advocate_opinion="Strong case. We should proceed with notice.",
        created_at=datetime.utcnow()
    )
    
    # Generate PDF
    file_name = f"legal_opinion_{opinion_id}.pdf"
    file_path = await pdf_service.generate_legal_opinion_pdf(
        opinion_dict=mock_opinion.model_dump(), 
        file_name=file_name,
        is_draft=False
    )
    
    return {"status": "success", "download_url": f"/static/{file_path}"}
