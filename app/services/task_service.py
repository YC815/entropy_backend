# app/services/task_service.py
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate


def create_new_task(db: Session, task_in: TaskCreate) -> Task:
    """
    接收 Pydantic 模型，轉換為 ORM 模型並寫入資料庫
    """
    # 1. 將 Pydantic schema 轉換為 dict
    task_data = task_in.model_dump()

    # 2. 建立 ORM 物件
    # **task_data 等同於 title=..., type=...
    db_task = Task(**task_data)

    # 3. 加入 Session 並提交
    db.add(db_task)
    db.commit()

    # 4. 重新整理 (因為資料庫會自動生成 ID 和 created_at，我們需要拿回來)
    db.refresh(db_task)

    return db_task
