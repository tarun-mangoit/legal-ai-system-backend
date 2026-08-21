from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RecentCaseResponse(BaseModel):
    id: str
    title: str
    status: str
    updated_at: Optional[datetime] = None

class StatisticsCardResponse(BaseModel):
    label: str
    value: int
    trend: Optional[str] = None
    trend_value: Optional[str] = None

class ClientDashboardResponse(BaseModel):
    total_cases: int
    pending_cases: int
    completed_cases: int
    pending_payments: int
    recent_cases: List[RecentCaseResponse]

class AdvocateDashboardResponse(BaseModel):
    assigned_cases: int
    pending_reviews: int
    completed_reviews: int
    recent_assignments: List[RecentCaseResponse]
    avg_turnaround_days: str
    completed_this_month: int
    client_rating: str

class AdminDashboardResponse(BaseModel):
    total_users: int
    total_clients: int
    total_advocates: int
    total_cases: int
    completed_cases: int
    pending_cases: int
    payments_received: int
    ai_total_tokens: int = 0
    ai_total_cost: float = 0.0
    latest_registrations: List[dict] # Simplified for now
