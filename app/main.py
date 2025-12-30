# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# 👇 設定 CORS (Cross-Origin Resource Sharing)
# 這是讓前端 (React/Next.js) 能成功呼叫後端的關鍵
origins = [
    "http://localhost",
    "http://localhost:3000",  # Next.js / React 預設 Port
    "http://localhost:5173",
    "http://localhost:3001"
]

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
