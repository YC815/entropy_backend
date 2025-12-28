# app/api/v1/endpoints/user.py
from fastapi import APIRouter

# 這就是 api.py 在找的那個變數！
router = APIRouter()


@router.get("/")
def read_users():
    """
    獲取使用者列表 (測試用)
    """
    return [{"username": "entropy_user", "level": 1.42}]
