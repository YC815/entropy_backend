# app/services/game_service.py
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.task import Task, TaskType, TaskStatus
from app.models.user import User


class GameService:

    @staticmethod
    def calculate_state(db: Session, user_id: int = 1):
        """
        核心數學引擎：計算當下的 HP (Integrity) 與 效率倍率 (Multiplier)
        """
        # 1. 獲取 User 資料 (如果沒有就自動建立一個預設的)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, username="Commander", level=1.0, current_xp=0)
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. 獲取所有「活躍中」的「School」任務 (因為只有 School 會扣 HP)
        active_school_tasks = db.query(Task).filter(
            Task.type == TaskType.SCHOOL,
            Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.INCINERATED, TaskStatus.IN_DOCK])
            # 註：根據你的設計，IN_DOCK 視為「準備執行」，是否要扣壓力看你設定。
            # 這裡暫時假設 IN_DOCK 還是會產生壓力，直到做完 (COMPLETED) 為止。
        ).all()

        total_stress = 0.0
        now = datetime.now(timezone.utc)

        # 用於回傳給前端畫圖的詳細數據
        stress_breakdown = []

        # 3. 逐一計算壓力權重
        for task in active_school_tasks:
            # 計算剩餘天數 (Days Until Due)
            if task.deadline:
                # 確保 deadline 是 timezone-aware
                deadline = task.deadline.replace(tzinfo=timezone.utc) if task.deadline.tzinfo is None else task.deadline
                delta = (deadline - now).total_seconds() / 86400  # 換算成天
                days_left = max(delta, 0.001)  # 避免 days_left <= -1 導致 log 錯誤
            else:
                days_left = 7.0  # 若沒死線，預設給 7 天緩衝

            # 核心公式：W_stress = Difficulty / ln(Days + 1)
            # 使用 math.log (自然對數 ln)
            # 加 1 是為了避免 days_left 接近 0 時分母為負
            denominator = math.log(days_left + 1)

            # 保護機制：避免分母過小導致無限大
            if denominator < 0.1:
                denominator = 0.1

            task_stress = task.difficulty / denominator

            # 限制單一任務最大壓力 (例如 40%)，避免一個任務就讓系統崩潰
            task_stress = min(task_stress, 40.0)

            total_stress += task_stress

            stress_breakdown.append({
                "task_title": task.title,
                "days_left": round(days_left, 1),
                "stress_impact": round(task_stress, 1)
            })

        # 4. 計算 HP (Integrity)
        current_hp = 100.0 - total_stress
        current_hp = max(0.0, current_hp)  # HP 不能小於 0

        # 5. 判定狀態與倍率
        if current_hp >= 80:
            status = "FLOW"
            multiplier = 1.2
        elif current_hp >= 50:
            status = "NORMAL"
            multiplier = 1.0
        else:
            status = "BRAIN_FOG"
            multiplier = 0.5

        return {
            "user_info": {
                "level": user.level,
                "current_xp": user.current_xp,
                "blackhole_days": user.blackhole_days
            },
            "integrity": round(current_hp, 1),
            "total_stress": round(total_stress, 1),
            "multiplier": multiplier,
            "status": status,
            "stress_breakdown": stress_breakdown
        }


game_service = GameService()
