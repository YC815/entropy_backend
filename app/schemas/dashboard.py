# app/schemas/dashboard.py
from pydantic import BaseModel


class StressItem(BaseModel):
    task_title: str
    days_left: float
    stress_impact: float


class UserInfo(BaseModel):
    level: float
    current_xp: int
    blackhole_days: float


class DashboardResponse(BaseModel):
    user_info: UserInfo
    integrity: float
    total_stress: float
    multiplier: float
    status: str
    stress_breakdown: list[StressItem]
