from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service
from app.services.ai_service import ai_service
from app.services.game_service import game_service

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


# app/api/v1/endpoints/tasks.py

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
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

# 🆕 新增：AI 語音指令入口
# POST /api/v1/tasks/speech


class SpeechTasksResponse(BaseModel):
    transcript: str
    tasks: List[TaskResponse]


@router.post("/speech", response_model=SpeechTasksResponse, status_code=status.HTTP_201_CREATED)
async def create_tasks_from_speech(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    【Gemini 原生版】接收語音檔 -> Gemini 直接聽並回傳 JSON -> 批次建立任務
    """
    # 1. 呼叫 AI Service (直接處理音訊)
    tasks_data, transcript = await ai_service.process_audio_instruction(file)

    # 2. 寫入資料庫
    created_tasks = []
    for task_in in tasks_data:
        new_task = task_service.create_new_task(db=db, task_in=task_in)
        created_tasks.append(new_task)

    return {"transcript": transcript, "tasks": created_tasks}


class CommitResponse(BaseModel):
    task_id: int
    status: str
    xp_gained: int
    hp_restored: bool
    message: str


@router.post("/{task_id}/commit", response_model=CommitResponse)
def commit_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    【結算儀式】完成任務並計算獎勵
    - School: 釋放壓力 (HP 回升), 黑洞 +0.5 天
    - Skill: 獲得 XP (Base * Multiplier), 黑洞 +3.0 天
    """
    # 1. 找任務
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task already completed")

    # 2. 獲取 User
    user = db.query(User).filter(User.id == 1).first()  # 單機版預設 ID 1

    if not user:
        user = User(id=1, username="Commander", level=1.0, current_xp=0, blackhole_days=7.0)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. 取得當下的狀態倍率 (在按下按鈕的那一刻結算)
    # 我們只需要 multiplier，所以呼叫 game_service
    state = game_service.calculate_state(db, user_id=1)
    multiplier = state["multiplier"]

    response_data = {
        "task_id": task.id,
        "status": "completed",
        "xp_gained": 0,
        "hp_restored": False,
        "message": ""
    }

    # 4. 分歧判斷
    if task.type == TaskType.SCHOOL:
        # === SCHOOL (維運) ===
        # 獎勵：黑洞 +0.5 天
        user.blackhole_days += 0.5
        response_data["hp_restored"] = True
        response_data["message"] = "Integrity Restored. Blackhole delayed by 12 hours."

    elif task.type == TaskType.SKILL:
        # === SKILL (進化) ===
        # 獎勵：XP * 倍率
        final_xp = int(task.xp_value * multiplier)
        user.current_xp += final_xp

        # 獎勵：黑洞 +3.0 天
        user.blackhole_days += 3.0

        # 升級邏輯 (簡單版：XP 累積到一定程度升級，這裡先不實作複雜公式)
        # 假設每 1000 XP 升一級
        user.level = 1.0 + (user.current_xp / 1000.0)

        response_data["xp_gained"] = final_xp
        response_data["message"] = f"Evolution Complete! +{final_xp} XP ({multiplier}x Efficiency). Blackhole delayed by 3 days."

    else:
        # === MISC ===
        user.blackhole_days += 0.1  # 微量獎勵
        response_data["xp_gained"] = 10
        user.current_xp += 10
        response_data["message"] = "Task done."

    # 5. 標記完成並存檔
    task.status = TaskStatus.COMPLETED
    # 更新 User 的最後登入時間/活躍時間
    user.last_login = datetime.now(timezone.utc)

    db.commit()

    return response_data
