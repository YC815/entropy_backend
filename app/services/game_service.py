# app/services/game_service.py
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.task import Task, TaskType, TaskStatus
from app.models.user import User


# app/services/game_service.py
# ... imports 保持不變 ...

class GameService:

    @staticmethod
    def calculate_state(db: Session, user_id: int = 1):
        # 1. 獲取 User (若無則建立)
        user = db.query(User).filter(User.id == user_id).first()
        now = datetime.now(timezone.utc)

        if not user:
            user = User(
                id=user_id,
                username="Commander",
                level=1.0,
                current_xp=0,
                blackhole_days=7.0,
                last_blackhole_update=now  # 初始化時間
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 👇 === ⏳ 新增：惰性計算黑洞扣除 ===
        # 確保 last_blackhole_update 有時區資訊
        last_update = user.last_blackhole_update.replace(tzinfo=timezone.utc) if user.last_blackhole_update.tzinfo is None else user.last_blackhole_update

        delta_seconds = (now - last_update).total_seconds()

        # 只有經過 60 秒以上才更新，避免頻繁寫入
        if delta_seconds > 60:
            days_elapsed = delta_seconds / 86400.0  # 換算成天
            user.blackhole_days -= days_elapsed

            if user.blackhole_days < 0:
                user.blackhole_days = 0.0

            # 更新時間戳記
            user.last_blackhole_update = now
            db.add(user)
            db.commit()
            # 記憶體中的 user 也已經被更新了
        # 👆 === 結束 ===

        # 2. 獲取 active tasks (後面邏輯保持不變...)
        active_school_tasks = db.query(Task).filter(
            # ... (複製你原本的程式碼)
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
