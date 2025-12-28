# app/models/task.py
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base  # 記得從 database.py 匯入 Base

# 1. 定義 Enum (讓程式碼更乾淨，避免 Magic String)


class TaskType(str, PyEnum):
    SCHOOL = "school"
    SKILL = "skill"
    MISC = "misc"


class TaskStatus(str, PyEnum):
    DRAFT = "draft"
    STAGED = "staged"
    IN_DOCK = "in_dock"
    COMPLETED = "completed"
    INCINERATED = "incinerated"

# 2. 定義 Table


class Task(Base):
    __tablename__ = "tasks"

    # Mapped[...] 是 SQLAlchemy 2.0 的新語法，支援 Type Hinting
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)

    # 使用 Enum 型別
    type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.DRAFT)

    xp_value: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
