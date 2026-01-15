# app/schemas/task.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from app.models.task import TaskType, TaskStatus
from app.utils.datetime_utils import normalize_deadline_input, serialize_deadline

# 1. 基礎底座：加入 difficulty


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    type: TaskType
    xp_value: int = Field(default=0, ge=0)
    # 🆕 新增難度欄位 (預設為 1)
    difficulty: int = Field(default=1, ge=1, le=10, description="1-10 難度係數")
    deadline: datetime | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("deadline", mode="before")
    @classmethod
    def _normalize_deadline(cls, value):
        return normalize_deadline_input(value)

    @field_serializer("deadline", when_used="json")
    def _serialize_deadline(self, value: datetime | None):
        return serialize_deadline(value)

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

    @field_validator("deadline", mode="before")
    @classmethod
    def _normalize_deadline(cls, value):
        return normalize_deadline_input(value)

    @field_serializer("deadline", when_used="json")
    def _serialize_deadline(self, value: datetime | None):
        return serialize_deadline(value)

# 4. Response：回傳給前端的樣子


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
