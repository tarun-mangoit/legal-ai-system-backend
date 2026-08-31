from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from pydantic import UUID4
from app.models.case import Case, CaseStatus
from app.models.case_history import CaseHistory
from app.models.case_assignment import CaseAssignment
from app.models.user import User
from app.models.role import Role
from app.models.payment import Payment
from app.repositories.case_repository import case_repository
from app.repositories.case_history_repository import case_history_repository
from app.repositories.case_assignment_repository import case_assignment_repository
from app.repositories.document_repository import DocumentRepository
from app.schemas.case import CaseCreate, CaseUpdate
from sqlalchemy import select
from typing import Dict, Any, List
from app.services.notification_events import notification_events

VALID_STATUS_TRANSITIONS = {
    CaseStatus.NEW: [CaseStatus.PAYMENT_PENDING, CaseStatus.CANCELLED],
    CaseStatus.PAYMENT_PENDING: [CaseStatus.PAYMENT_COMPLETED, CaseStatus.CANCELLED],
    CaseStatus.PAYMENT_COMPLETED: [CaseStatus.DOCUMENTS_UPLOADED],
    CaseStatus.DOCUMENTS_UPLOADED: [CaseStatus.AI_PROCESSING],
    CaseStatus.AI_PROCESSING: [CaseStatus.UNDER_REVIEW],
    CaseStatus.UNDER_REVIEW: [CaseStatus.OPINION_GENERATED],
    CaseStatus.OPINION_GENERATED: [CaseStatus.REPORT_GENERATED],
    CaseStatus.REPORT_GENERATED: [CaseStatus.COMPLETED],
    CaseStatus.COMPLETED: [],
    CaseStatus.CANCELLED: []
}

class CaseService:
    async def _create_history(self, db: AsyncSession, case_id: UUID4, changed_by: UUID4, action_type: str, prev_val: str = None, new_val: str = None):
        history_data = {
            "case_id": case_id,
            "changed_by": changed_by,
            "action_type": action_type,
            "previous_value": prev_val,
            "new_value": new_val
        }
        await case_history_repository.create(db, history_data)

    async def create_case(self, db: AsyncSession, case_in: CaseCreate, current_user: User) -> Case:
        # Generate case number
        case_number = await case_repository.generate_case_number(db)
        client_id = current_user.id
        role = await db.get(Role, current_user.role_id)
        if role.name == "admin" and getattr(case_in, "client_id", None):
            client_id = case_in.client_id

        # Build case object data
        case_data = {
            **case_in.model_dump(exclude={'client_id'}),
            "case_number": case_number,
            "client_id": client_id,
            "status": CaseStatus.NEW
        }
        
        # Save case
        created_case = await case_repository.create(db, case_data)
        
        # Create history
        await self._create_history(db, created_case.id, current_user.id, "CASE_CREATED", None, str(CaseStatus.NEW))
        
        # Trigger notification
        await notification_events.handle_case_created(
            db=db,
            user_id=str(current_user.id),
            case_number=created_case.case_number,
            title=created_case.title
        )
        
        return created_case

    async def get_case(self, db: AsyncSession, case_id: UUID4) -> Case:
        case = await case_repository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return case

    async def get_case_details_aggregated(self, db: AsyncSession, case_id: UUID4, current_user: User) -> dict:
        case = await self.get_case(db, case_id)
        
        # Get roles
        role = await db.get(Role, current_user.role_id)
        role_name = role.name
        
        # Authorization check
        if role_name == "client" and str(case.client_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this case")
        if role_name == "advocate" and str(case.advocate_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this case")
            
        # Get related data
        doc_repo = DocumentRepository(db)
        documents = await doc_repo.list_by_case(case_id)
        
        all_docs_have_summary = False
        if documents:
            from app.models.document_summary import DocumentSummary
            doc_ids = [d.id for d in documents]
            summary_result = await db.execute(select(DocumentSummary.document_id).where(DocumentSummary.document_id.in_(doc_ids)))
            summary_doc_ids = summary_result.scalars().all()
            if len(set(summary_doc_ids)) == len(documents):
                all_docs_have_summary = True
        
        payments_result = await db.execute(select(Payment).where(Payment.case_id == case_id).order_by(Payment.created_at.desc()))
        payments = list(payments_result.scalars().all())
        
        activities = await case_history_repository.get_by_case(db, case_id)
        
        # Build permissions
        permissions = {
            "can_view_ai_analysis": role_name in ["admin", "advocate"],
            "can_edit_case": role_name == "admin",
            "can_assign_advocate": role_name == "admin",
            "can_update_status": role_name in ["admin", "advocate"],
            "can_view_audit_logs": role_name == "admin",
            "can_view_internal_notes": role_name in ["admin", "advocate"],
            "can_view_payment_admin": role_name == "admin",
            "can_delete_case": role_name == "admin",
            "can_close_case": role_name == "admin"
        }
        
        return {
            "case": case,
            "client": case.client,
            "advocate": case.advocate,
            "documents": documents,
            "payments": payments,
            "activities": activities,
            "permissions": permissions
        }

    async def search_cases(self, db: AsyncSession, filters: Dict[str, Any], skip: int = 0, limit: int = 100, sort_by: str = "created_at", sort_order: str = "desc"):
        items = await case_repository.search(db, filters, skip, limit, sort_by, sort_order)
        total = await case_repository.count(db, filters)
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def get_case_summary_stats(self, db: AsyncSession, filters: Dict[str, Any]) -> Dict[str, int]:
        from sqlalchemy import select, func
        
        # Base query to respect any global filters (like client_id or advocate_id for non-admins)
        base_query = select(Case.status, func.count()).group_by(Case.status)
        base_query = case_repository._apply_filters(base_query, filters)
        
        result = await db.execute(base_query)
        status_counts = dict(result.all())
        
        total_cases = sum(status_counts.values())
        
        return {
            "total_cases": total_cases,
            "new": status_counts.get(CaseStatus.NEW, 0),
            "pending_assignment": status_counts.get(CaseStatus.PAYMENT_COMPLETED, 0), # Example mapping for 'pending assignment'
            "in_progress": status_counts.get(CaseStatus.UNDER_REVIEW, 0) + status_counts.get(CaseStatus.AI_PROCESSING, 0),
            "pending_review": status_counts.get(CaseStatus.OPINION_GENERATED, 0) + status_counts.get(CaseStatus.REPORT_GENERATED, 0),
            "payment_pending": status_counts.get(CaseStatus.PAYMENT_PENDING, 0),
            "completed": status_counts.get(CaseStatus.COMPLETED, 0),
            "cancelled": status_counts.get(CaseStatus.CANCELLED, 0),
        }

    async def update_case(self, db: AsyncSession, case_id: UUID4, case_in: CaseUpdate, current_user: User) -> Case:
        case = await self.get_case(db, case_id)
        
        update_data = case_in.model_dump(exclude_unset=True)
        if not update_data:
            return case

        # Only check RBAC if advocate is modifying (they can only modify if assigned)
        # Client can modify if they own it. Admin can modify anything.
        # This RBAC logic is abstracted here, assuming router passed the current_user
        
        updated_case = await case_repository.update(db, case, update_data)
        
        changes = ", ".join(update_data.keys())
        await self._create_history(db, updated_case.id, current_user.id, "INFO_UPDATED", None, changes)
        
        return updated_case

    async def update_status(self, db: AsyncSession, case_id: UUID4, new_status: CaseStatus, current_user: User) -> Case:
        case = await self.get_case(db, case_id)
        
        # Relaxed transition checks for Admin/Advocate manual operations
        # Note: Frontend handles which statuses are available to select
        pass

        prev_status = case.status
        updated_case = await case_repository.update(db, case, {"status": new_status})
        
        await self._create_history(db, updated_case.id, current_user.id, "STATUS_CHANGE", prev_status, new_status)
        
        return await self.get_case(db, case_id)

    async def set_case_fee(self, db: AsyncSession, case_id: UUID4, fee: float, current_user: User) -> Case:
        case = await self.get_case(db, case_id)
        
        if case.status not in [CaseStatus.NEW, CaseStatus.PAYMENT_PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Can only set fee for NEW or PAYMENT_PENDING cases"
            )

        prev_status = case.status
        updated_case = await case_repository.update(db, case, {
            "case_fee": fee,
            "status": CaseStatus.PAYMENT_PENDING
        })
        
        if prev_status != CaseStatus.PAYMENT_PENDING:
            await self._create_history(db, updated_case.id, current_user.id, "STATUS_CHANGE", str(prev_status), str(CaseStatus.PAYMENT_PENDING))
        
        await self._create_history(db, updated_case.id, current_user.id, "FEE_SET", None, str(fee))
        
        # Trigger notification
        if updated_case.client_id:
            await notification_events.handle_payment_required(
                db=db,
                user_id=str(updated_case.client_id),
                case_id=str(updated_case.id),
                case_number=updated_case.case_number,
                title=updated_case.title,
                amount=fee
            )
            
        return await self.get_case(db, case_id)

    async def assign_advocate(self, db: AsyncSession, case_id: UUID4, advocate_id: UUID4, current_user: User) -> Case:
        case = await self.get_case(db, case_id)
        
        # Assuming we have validated advocate_id exists and has advocate role in the router/dependency
        prev_advocate = str(case.advocate_id) if case.advocate_id else None
        
        updated_case = await case_repository.update(db, case, {"advocate_id": advocate_id})
        
        # Track assignment
        assignment_data = {
            "case_id": case_id,
            "assigned_by": current_user.id,
            "assigned_to": advocate_id
        }
        await case_assignment_repository.create(db, assignment_data)
        
        await self._create_history(db, updated_case.id, current_user.id, "ADVOCATE_ASSIGNED", prev_advocate, str(advocate_id))
        
        # Trigger notification
        advocate_user = await db.get(User, advocate_id)
        if advocate_user and updated_case.client_id:
            await notification_events.handle_case_assigned(
                db=db,
                case_id=str(case_id),
                case_number=updated_case.case_number,
                advocate_id=str(advocate_id),
                advocate_name=f"{advocate_user.first_name} {advocate_user.last_name}",
                client_id=str(updated_case.client_id)
            )
        
        
        return await self.get_case(db, case_id)

    async def get_case_history(self, db: AsyncSession, case_id: UUID4) -> List[CaseHistory]:
        await self.get_case(db, case_id) # ensure exists
        return await case_history_repository.get_by_case(db, case_id)

case_service = CaseService()
