# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# 根據資料庫類型決定連接參數
# check_same_thread 是 SQLite 專用，PostgreSQL 不認識這個參數
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

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
