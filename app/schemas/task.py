# app/schemas/task.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.task import TaskType, TaskStatus

# 1. 基礎底座：加入 difficulty


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    type: TaskType
    xp_value: int = Field(default=0, ge=0)
    # 🆕 新增難度欄位 (預設為 1)
    difficulty: int = Field(default=1, ge=1, le=10, description="1-10 難度係數")
    deadline: datetime | None = None

# 2. Create：繼承 Base，不用動


class TaskCreate(TaskBase):
    pass

# 3. Update：允許單獨更新難度


class TaskUpdate(BaseModel):
    title: str | None = None
    type: TaskType | None = None
    status: TaskStatus | None = None
    xp_value: int | None = Field(default=None, ge=0)
    # 🆕 允許更新難度
    difficulty: int | None = Field(default=None, ge=1, le=10)
    deadline: datetime | None = None

# 4. Response：回傳給前端的樣子


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
