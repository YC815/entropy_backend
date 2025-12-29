# app/models/user.py
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, default="Commander")

    # 遊戲化數據
    level: Mapped[float] = mapped_column(Float, default=1.0)
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    blackhole_days: Mapped[float] = mapped_column(Float, default=7.0)

    # ✅ 新增：上次扣除黑洞的時間
    last_blackhole_update: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

    last_login: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
