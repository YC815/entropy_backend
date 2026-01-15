# app/core/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import Pool
from app.core.config import settings

# 根據資料庫類型決定連接參數
# check_same_thread 是 SQLite 專用，PostgreSQL 不認識這個參數
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# 連線池配置：處理遠端資料庫連線不穩定問題
pool_settings = {
    "pool_pre_ping": True,  # 每次從池中取連線前先測試是否存活
    "pool_recycle": 3600,   # 1小時後回收連線，避免長時間閒置被伺服器關閉
    "pool_size": 5,         # 連線池大小
    "max_overflow": 10,     # 超過 pool_size 時最多再建立幾個臨時連線
}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **pool_settings
)

# 2. 建立 Session 工廠 (負責生產連線)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 定義 ORM 的基底類別 (之後所有的 Model 都要繼承它)


class Base(DeclarativeBase):
    pass

# 4. Dependency (依賴注入用)
# 這是一個 Generator，確保每次 Request 結束後，資料庫連線會被正確關閉


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
