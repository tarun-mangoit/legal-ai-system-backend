from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.case import (
    CaseCreate, CaseUpdate, CaseStatusUpdate, CaseAssignmentCreate, 
    CaseResponse, CaseListResponse, CaseHistoryResponse, CaseDetailAggregatedResponse,
    CaseFeeUpdate
)
from app.services.case_service import case_service
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.case import CaseStatus, CasePriority
from typing import Optional
from pydantic import UUID4
from datetime import datetime

router = APIRouter()

# Role Dependencies
RequireAdmin = Depends(require_roles(["admin"]))
RequireAdvocate = Depends(require_roles(["admin", "advocate"]))
RequireAny = Depends(require_roles(["admin", "advocate", "client"]))

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    current_user: User = Depends(require_roles(["admin", "client"])),
    db: AsyncSession = Depends(get_db)
):
    return await case_service.create_case(db, case_in, current_user)

@router.get("/summary", response_model=dict)
async def get_cases_summary(
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    
    filters = {}
    if role.name == "client":
        filters["client_id"] = current_user.id
    elif role.name == "advocate":
        filters["advocate_id"] = current_user.id
        
    return await case_service.get_case_summary_stats(db, filters)

@router.get("", response_model=CaseListResponse)
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    status: Optional[CaseStatus] = None,
    priority: Optional[CasePriority] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    client_id: Optional[UUID4] = None,
    advocate_id: Optional[UUID4] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    
    filters = {
        "status": status,
        "priority": priority,
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
        "search": search
    }
    
    # Clean None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Enforce RBAC filtering
    if role.name == "client":
        filters["client_id"] = current_user.id
    elif role.name == "advocate":
        filters["advocate_id"] = current_user.id
    elif role.name == "admin":
        if client_id: filters["client_id"] = client_id
        if advocate_id: filters["advocate_id"] = advocate_id
        
    return await case_service.search_cases(db, filters, skip, limit, sort_by, sort_order)

@router.get("/{case_id}", response_model=CaseDetailAggregatedResponse)
async def get_case(
    case_id: UUID4,
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    return await case_service.get_case_details_aggregated(db, case_id, current_user)

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID4,
    case_in: CaseUpdate,
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    # Authorization handled via get_case fetch internally in service + wrapper here
    case = await case_service.get_case(db, case_id)
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    
    # Only Admin can update case details
    if role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can edit case details")
        
    return await case_service.update_case(db, case_id, case_in, current_user)

@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_case_status(
    case_id: UUID4,
    status_update: CaseStatusUpdate,
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    case = await case_service.get_case(db, case_id)
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    if role.name == "client":
        raise HTTPException(status_code=403, detail="Clients cannot update status")
    if role.name == "advocate" and str(case.advocate_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this case")
        
    return await case_service.update_status(db, case_id, status_update.status, current_user)

@router.post("/{case_id}/assign", response_model=CaseResponse)
async def assign_advocate(
    case_id: UUID4,
    assign_in: CaseAssignmentCreate,
    current_user: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    return await case_service.assign_advocate(db, case_id, assign_in.advocate_id, current_user)

@router.post("/{case_id}/set-fee", response_model=CaseResponse)
async def set_case_fee(
    case_id: UUID4,
    fee_in: CaseFeeUpdate,
    current_user: User = RequireAdmin,
    db: AsyncSession = Depends(get_db)
):
    return await case_service.set_case_fee(db, case_id, fee_in.fee, current_user)

@router.get("/{case_id}/history", response_model=list[CaseHistoryResponse])
async def get_case_history(
    case_id: UUID4,
    current_user: User = RequireAny,
    db: AsyncSession = Depends(get_db)
):
    case = await case_service.get_case(db, case_id)
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    if role.name == "client" and str(case.client_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this case history")
    if role.name == "advocate" and str(case.advocate_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this case history")
        
    return await case_service.get_case_history(db, case_id)
