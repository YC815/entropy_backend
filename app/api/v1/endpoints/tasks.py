# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/")
def read_tasks(db: Session = Depends(get_db)):
    """
    獲取所有任務 (目前僅測試連線)
    """
    # 這裡之後會呼叫 CRUD Service，現在先回傳假資料證明活著
    return {"message": "Task module is active", "status": "Ready for Logistics"}
