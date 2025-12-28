# app/schemas/task.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.task import TaskType, TaskStatus  # 複用剛剛定義的 Enum

# 基礎底座：共用欄位


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, example="Complete Calculus HW")
    type: TaskType
    xp_value: int = Field(default=0, ge=0, example=10)
    deadline: datetime | None = None

# Create：前端建立時，只需要傳 Base 的內容


class TaskCreate(TaskBase):
    pass

# Response：回傳時，我們要補上 ID、狀態、建立時間


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    # 【重要】告訴 Pydantic 可以直接讀取 SQLAlchemy 的物件
    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    # 所有欄位都是 Optional，因為我們只更新變動的部分
    title: str | None = None
    type: TaskType | None = None
    status: TaskStatus | None = None
    xp_value: int | None = Field(default=None, ge=0)
    deadline: datetime | None = None
