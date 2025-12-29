# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import tasks, dashboard

api_router = APIRouter()

# 這裡把 tasks.py 裡面的路由掛載進來
# prefix="/tasks" 代表網址會是 /api/v1/tasks/...
# tags=["tasks"] 會在 Swagger UI 上建立分類標籤
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
# api_router.include_router(user.router, prefix="/users", tags=["users"])
