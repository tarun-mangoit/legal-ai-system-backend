from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict, Any

from app.models.case import Case, CaseStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.role import Role
from app.models.job_tracking import AIUsageLog

class DashboardRepository:
    async def get_client_stats(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        total_cases = await db.scalar(select(func.count()).select_from(Case).where(Case.client_id == user_id)) or 0
        
        pending_cases = await db.scalar(
            select(func.count()).select_from(Case).where(
                Case.client_id == user_id, 
                Case.status.notin_([CaseStatus.COMPLETED, CaseStatus.CANCELLED])
            )
        ) or 0
        
        completed_cases = await db.scalar(
            select(func.count()).select_from(Case).where(
                Case.client_id == user_id, 
                Case.status == CaseStatus.COMPLETED
            )
        ) or 0
        
        pending_payments = await db.scalar(
            select(func.count()).select_from(Payment).where(
                Payment.client_id == user_id, 
                Payment.status == PaymentStatus.PENDING
            )
        ) or 0
        
        recent_cases_result = await db.execute(
            select(Case.id, Case.title, Case.status, Case.updated_at)
            .where(Case.client_id == user_id)
            .order_by(desc(Case.updated_at))
            .limit(5)
        )
        
        recent_cases = [
            {
                "id": str(row.id),
                "title": row.title,
                "status": row.status.value if hasattr(row.status, 'value') else row.status,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            for row in recent_cases_result.all()
        ]

        return {
            "total_cases": total_cases,
            "pending_cases": pending_cases,
            "completed_cases": completed_cases,
            "pending_payments": pending_payments,
            "recent_cases": recent_cases
        }

    async def get_advocate_stats(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        assigned_cases = await db.scalar(select(func.count()).select_from(Case).where(Case.advocate_id == user_id)) or 0
        
        pending_reviews = await db.scalar(
            select(func.count()).select_from(Case).where(
                Case.advocate_id == user_id, 
                Case.status.in_([CaseStatus.UNDER_REVIEW, CaseStatus.AI_PROCESSING])
            )
        ) or 0
        
        completed_reviews = await db.scalar(
            select(func.count()).select_from(Case).where(
                Case.advocate_id == user_id, 
                Case.status.in_([CaseStatus.OPINION_GENERATED, CaseStatus.REPORT_GENERATED, CaseStatus.COMPLETED])
            )
        ) or 0
        
        recent_assignments_result = await db.execute(
            select(Case.id, Case.title, Case.status, Case.updated_at)
            .where(Case.advocate_id == user_id)
            .order_by(desc(Case.updated_at))
            .limit(5)
        )
        
        recent_assignments = [
            {
                "id": str(row.id),
                "title": row.title,
                "status": row.status.value if hasattr(row.status, 'value') else row.status,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            for row in recent_assignments_result.all()
        ]

        completed_this_month = await db.scalar(
            select(func.count()).select_from(Case).where(
                Case.advocate_id == user_id, 
                Case.status.in_([CaseStatus.OPINION_GENERATED, CaseStatus.REPORT_GENERATED, CaseStatus.COMPLETED]),
                func.date_trunc('month', Case.updated_at) == func.date_trunc('month', func.current_date())
            )
        ) or 0
        
        avg_turnaround = await db.scalar(
            select(func.avg(func.extract('epoch', Case.updated_at - Case.created_at)) / 86400.0)
            .select_from(Case)
            .where(
                Case.advocate_id == user_id,
                Case.status.in_([CaseStatus.OPINION_GENERATED, CaseStatus.REPORT_GENERATED, CaseStatus.COMPLETED])
            )
        )
        avg_turnaround_str = f"{float(avg_turnaround):.1f} Days" if avg_turnaround else "N/A"
        
        return {
            "assigned_cases": assigned_cases,
            "pending_reviews": pending_reviews,
            "completed_reviews": completed_reviews,
            "recent_assignments": recent_assignments,
            "avg_turnaround_days": avg_turnaround_str,
            "completed_this_month": completed_this_month,
            "client_rating": "N/A"
        }

    async def get_admin_stats(self, db: AsyncSession) -> Dict[str, Any]:
        total_users = await db.scalar(select(func.count()).select_from(User)) or 0
        
        total_clients = await db.scalar(
            select(func.count()).select_from(User).join(Role, User.role_id == Role.id).where(Role.name == 'client')
        ) or 0
        
        total_advocates = await db.scalar(
            select(func.count()).select_from(User).join(Role, User.role_id == Role.id).where(Role.name == 'advocate')
        ) or 0
        
        total_cases = await db.scalar(select(func.count()).select_from(Case)) or 0
        
        completed_cases = await db.scalar(
            select(func.count()).select_from(Case).where(Case.status == CaseStatus.COMPLETED)
        ) or 0
        
        pending_cases = await db.scalar(
            select(func.count()).select_from(Case).where(Case.status.notin_([CaseStatus.COMPLETED, CaseStatus.CANCELLED]))
        ) or 0
        
        payments_received = await db.scalar(
            select(func.sum(Payment.amount)).select_from(Payment).where(Payment.status == PaymentStatus.SUCCESS)
        ) or 0.0

        latest_registrations_result = await db.execute(
            select(User.id, User.first_name, User.last_name, User.email, User.created_at, Role.name.label('role'))
            .join(Role, User.role_id == Role.id)
            .order_by(desc(User.created_at))
            .limit(5)
        )
        
        latest_registrations = [
            {
                "id": str(row.id),
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
                "role": str(row.role).upper(),
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in latest_registrations_result.all()
        ]
        
        ai_input_tokens = await db.scalar(select(func.sum(AIUsageLog.input_tokens)).select_from(AIUsageLog)) or 0
        ai_output_tokens = await db.scalar(select(func.sum(AIUsageLog.output_tokens)).select_from(AIUsageLog)) or 0
        ai_total_tokens = ai_input_tokens + ai_output_tokens
        ai_total_cost = await db.scalar(select(func.sum(AIUsageLog.cost)).select_from(AIUsageLog)) or 0.0
        
        return {
            "total_users": total_users,
            "total_clients": total_clients,
            "total_advocates": total_advocates,
            "total_cases": total_cases,
            "completed_cases": completed_cases,
            "pending_cases": pending_cases,
            "payments_received": float(payments_received),
            "ai_total_tokens": int(ai_total_tokens),
            "ai_total_cost": float(ai_total_cost),
            "latest_registrations": latest_registrations
        }

dashboard_repository = DashboardRepository()
