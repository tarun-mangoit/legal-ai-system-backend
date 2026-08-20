import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role
from app.schemas.legal_opinion import (
    LegalOpinionCreate,
    LegalOpinionUpdate,
    LegalOpinionResponse,
    OpinionCommentCreate,
    OpinionCommentResponse,
    OpinionRevisionResponse
)
from app.repositories.opinion_repository import LegalOpinionRepository, OpinionRevisionRepository, OpinionCommentRepository
from app.services.opinion_service import OpinionService

router = APIRouter()

def get_opinion_service(db: AsyncSession = Depends(get_db)):
    opinion_repo = LegalOpinionRepository(db)
    revision_repo = OpinionRevisionRepository(db)
    comment_repo = OpinionCommentRepository(db)
    return OpinionService(opinion_repo, revision_repo, comment_repo)

@router.get("", response_model=List[LegalOpinionResponse])
async def get_all_opinions(
    skip: int = 0,
    limit: int = 100,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name not in ["admin", "advocate", "client"]:
        raise HTTPException(status_code=403, detail="Not authorized to list opinions")
        
    advocate_id = current_user.id if role.name == "advocate" else None
    client_id = current_user.id if role.name == "client" else None
    return await service.get_all_opinions(skip, limit, advocate_id, client_id)

@router.post("", response_model=LegalOpinionResponse, status_code=201)
async def create_opinion(
    data: LegalOpinionCreate,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot create opinions")
    return await service.create_draft(data, current_user.id)

@router.get("/{opinion_id}", response_model=LegalOpinionResponse)
async def get_opinion(
    opinion_id: uuid.UUID,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    opinion = await service.get_opinion(opinion_id)
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        from app.models.case import CaseStatus
        if opinion.case and opinion.case.status in [CaseStatus.NEW, CaseStatus.PAYMENT_PENDING]:
            raise HTTPException(status_code=403, detail="Payment is required to view the legal opinion")
        if not opinion.is_final:
            raise HTTPException(status_code=404, detail="Opinion not found or not finalized")
    return opinion

@router.put("/{opinion_id}", response_model=LegalOpinionResponse)
async def update_opinion(
    opinion_id: uuid.UUID,
    data: LegalOpinionUpdate,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot update opinions")
    return await service.update_opinion(opinion_id, data, current_user.id)

@router.post("/{opinion_id}/finalize", response_model=LegalOpinionResponse)
async def finalize_opinion(
    opinion_id: uuid.UUID,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot finalize opinions")
    return await service.finalize_opinion(opinion_id, current_user.id)

@router.post("/{opinion_id}/save-draft", response_model=LegalOpinionResponse)
async def save_draft(
    opinion_id: uuid.UUID,
    data: LegalOpinionUpdate,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Same as PUT, but semantic
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot save drafts")
    # Mark as draft save specifically
    data.changes_summary = "Autosaved Draft"
    return await service.update_opinion(opinion_id, data, current_user.id)

@router.get("/{opinion_id}/history", response_model=List[OpinionRevisionResponse])
async def get_history(
    opinion_id: uuid.UUID,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot view revision history")
    opinion = await service.get_opinion(opinion_id)
    return opinion.revisions

@router.post("/{opinion_id}/comments", response_model=OpinionCommentResponse, status_code=201)
async def add_comment(
    opinion_id: uuid.UUID,
    data: OpinionCommentCreate,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot add internal comments")
    return await service.add_comment(opinion_id, data, current_user.id)

@router.get("/case/{case_id}", response_model=LegalOpinionResponse)
async def get_opinion_by_case(
    case_id: uuid.UUID,
    service: OpinionService = Depends(get_opinion_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    opinion = await service.get_opinion_by_case(case_id)
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        from app.models.case import CaseStatus
        if opinion.case and opinion.case.status in [CaseStatus.NEW, CaseStatus.PAYMENT_PENDING]:
            raise HTTPException(status_code=403, detail="Payment is required to view the legal opinion")
        if not opinion.is_final:
            raise HTTPException(status_code=404, detail="Opinion not found or not finalized")
    return opinion
