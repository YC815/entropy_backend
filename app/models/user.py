# app/models/user.py
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# ✅ 定義一個獲取當前 UTC 時間的函式


def get_utc_now():
    return datetime.now(timezone.utc)


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
