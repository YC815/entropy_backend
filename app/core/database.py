# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# 1. 建立引擎
# connect_args={"check_same_thread": False} 是 SQLite 專用的設定
# 因為 SQLite 預設不允許不同執行緒共用連線，但在 FastAPI 這是常態
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
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
