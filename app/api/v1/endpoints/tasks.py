from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service
from app.models.task import Task  # 用於查詢檢查

router = APIRouter()

# 1. 取得列表 (GET /tasks)


@router.get("/", response_model=List[TaskResponse])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # 這裡未來可以加 filter，例如 ?status=staged
    return db.query(Task).offset(skip).limit(limit).all()

# 2. 建立任務 (POST /tasks) - 注意狀態碼是 201


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: TaskCreate
):
    return task_service.create_new_task(db=db, task_in=task_in)

# 3. 取得單一任務 (GET /tasks/{task_id})


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        # RESTful 精神：找不到就回 404，不要回 200 然後內容寫 "not found"
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# 4. 修改任務 (PATCH /tasks/{task_id})
# 使用 PATCH 而不是 PUT，因為我們通常只改標題或狀態，不用傳整包資料


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,  # 這裡需要去 schemas 定義 TaskUpdate
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Pydantic v2 的 update 寫法
    update_data = task_in.model_dump(exclude_unset=True)  # 只取有傳的欄位
    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

# 5. 刪除任務 (DELETE /tasks/{task_id})
# 成功刪除通常不需要回傳資料，所以用 204


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None
