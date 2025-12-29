# app/api/v1/endpoints/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.game_service import game_service
from app.schemas.dashboard import DashboardResponse

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def get_dashboard_status(db: Session = Depends(get_db)):
    """
    獲取當前的戰略狀態 (HP, XP Multiplier, User Stats)
    """
    # 這裡預設 user_id = 1 (單機版)
    return game_service.calculate_state(db, user_id=1)
