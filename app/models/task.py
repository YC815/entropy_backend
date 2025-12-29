# app/models/task.py
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# ✅ 同樣定義 helper


def get_utc_now():
    return datetime.now(timezone.utc)


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


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.DRAFT)

    # 🆕 新增欄位：難度 (School 專用, 1-10)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    # 🆕 欄位意義變更：這現在代表 Base XP
    xp_value: Mapped[int] = mapped_column(Integer, default=0)

    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ✅ 修正時間預設值
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    # onupdate 也建議改用 function，但 SQLAlchemy 的 onupdate 比較特殊，
    # 這裡我們先維持 datetime.now(timezone.utc) 的 lambda 寫法或直接傳入函數
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    def __repr__(self):
        return f"<Task {self.title} ({self.type})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, default="Commander")

    # 遊戲化數據
    level: Mapped[float] = mapped_column(Float, default=1.0)  # Lv 1.42
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    blackhole_days: Mapped[float] = mapped_column(Float, default=7.0)  # 初始 7 天

    # 上次更新時間
    # ✅ 這裡改用 get_utc_now，不再用 datetime.utcnow
    last_login: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
