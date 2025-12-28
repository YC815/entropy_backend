# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import Base, engine

# 【重要】這行程式碼會在啟動時，自動依照 Models 在資料庫建立表格
# 在正式生產環境通常會用 Alembic 做遷移，但在開發初期這樣最快
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 掛載剛剛寫好的總路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"system": "EntroPy v1.0", "status": "operational"}
