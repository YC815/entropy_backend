# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

# 【重要】資料庫遷移現在使用 Alembic 管理
# 不再使用 Base.metadata.create_all()
# 請使用以下指令初始化資料庫：
#   alembic upgrade head
#
# 開發時創建新遷移：
#   alembic revision --autogenerate -m "描述"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 👇 設定 CORS (Cross-Origin Resource Sharing)
# 這是讓前端 (React/Next.js) 能成功呼叫後端的關鍵
origins = [
    "http://localhost",
    "http://localhost:3000",  # Next.js / React 預設 Port
    "http://localhost:5173",
    "http://localhost:3001",
]

# 生產環境：從環境變數讀取前端 URL
if frontend_url := os.getenv("FRONTEND_URL"):
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 允許哪些網站連進來
    allow_credentials=True,     # 是否允許攜帶 Cookie
    allow_methods=["*"],        # 允許哪些 HTTP 方法 (GET, POST...)，"*" 代表全部允許
    allow_headers=["*"],        # 允許哪些 Header
)
# 👆 設定結束

# 掛載剛剛寫好的總路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"system": "EntroPy v1.0", "status": "operational"}
