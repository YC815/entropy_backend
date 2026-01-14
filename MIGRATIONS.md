# Database Migrations Guide

EntroPy 使用 Alembic 管理資料庫遷移，取代了之前的 `Base.metadata.create_all()` 方式。

## 為什麼使用 Alembic？

1. **版本控制**：每次資料庫結構變更都有完整記錄
2. **可回滾**：可以安全地回滾到之前的版本
3. **團隊協作**：遷移檔案可以 commit 到 Git，團隊成員同步
4. **生產環境安全**：避免意外刪除資料或結構

---

## 快速開始

### 1. 初始化資料庫（首次使用）

```bash
# 在 entropy_backend 目錄
cd entropy_backend

# 執行遷移
uv run alembic upgrade head
```

這會創建 `users` 和 `tasks` 兩張表格。

---

## 日常開發流程

### 2. 修改 Model 後創建新遷移

當你修改了 `app/models/` 中的 Model（例如添加新欄位）：

```bash
# 自動生成遷移檔案
uv run alembic revision --autogenerate -m "描述你的變更"

# 例如：
uv run alembic revision --autogenerate -m "add priority field to tasks"
```

Alembic 會自動比對現有資料庫與 Model，生成遷移檔案。

### 3. 檢查生成的遷移檔案

**重要**：永遠要檢查生成的遷移檔案！

```bash
# 遷移檔案位置
ls alembic/versions/

# 打開最新的遷移檔案檢查
cat alembic/versions/xxx_add_priority_field_to_tasks.py
```

確認：
- `upgrade()` 函式正確添加/修改了欄位
- `downgrade()` 函式可以回滾變更
- 沒有意外刪除資料的操作

### 4. 應用遷移

```bash
# 應用所有未執行的遷移
uv run alembic upgrade head
```

### 5. 回滾遷移（如果需要）

```bash
# 回滾一個版本
uv run alembic downgrade -1

# 回滾到特定版本
uv run alembic downgrade <revision_id>

# 回滾到最初狀態（危險！）
uv run alembic downgrade base
```

---

## 常用指令

### 查看遷移狀態

```bash
# 查看當前資料庫版本
uv run alembic current

# 查看遷移歷史
uv run alembic history

# 查看未應用的遷移
uv run alembic history --verbose
```

### 手動創建遷移（不使用 autogenerate）

```bash
uv run alembic revision -m "manual migration"
```

然後手動編輯生成的檔案，寫入 `upgrade()` 和 `downgrade()` 邏輯。

---

## Docker 環境

### Docker Compose（自動執行遷移）

Docker 容器啟動時會自動執行 `alembic upgrade head`（透過 `entrypoint.sh`）。

```bash
# 啟動服務（會自動遷移）
docker-compose up --build

# 或使用 PostgreSQL
docker-compose -f docker-compose.postgres.yml up --build
```

### 在運行中的容器手動執行遷移

```bash
# 進入容器
docker exec -it entropy-backend bash

# 執行遷移
uv run alembic upgrade head
```

---

## 資料庫切換（SQLite ↔ PostgreSQL）

### SQLite（開發環境）

```bash
# .env
DATABASE_URL=sqlite:///./entropy.db
```

### PostgreSQL（生產環境）

```bash
# .env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Alembic 會自動適配不同的資料庫類型。

---

## 常見問題

### Q: 我修改了 Model，但 autogenerate 沒有偵測到？

**可能原因**：
1. Model 沒有 import 到 `alembic/env.py`
2. Model 沒有繼承 `Base`
3. 欄位定義使用了 Alembic 不支援的語法

**解決方法**：
檢查 `alembic/env.py:10-11`，確保所有 Model 都有 import：
```python
from app.models.task import Task
from app.models.user import User
```

### Q: 遷移執行失敗怎麼辦？

```bash
# 1. 查看當前版本
uv run alembic current

# 2. 如果資料庫狀態不一致，強制標記為特定版本（危險！）
uv run alembic stamp <revision_id>

# 3. 或回滾到上一個版本
uv run alembic downgrade -1
```

### Q: 如何在多個開發者之間同步？

1. 遷移檔案 commit 到 Git
2. 其他開發者 pull 後執行：
   ```bash
   uv run alembic upgrade head
   ```

### Q: 生產環境如何遷移？

**推薦流程**：
1. 先在測試環境測試遷移
2. 備份生產資料庫
3. 停機維護（或使用藍綠部署）
4. 執行遷移：
   ```bash
   uv run alembic upgrade head
   ```
5. 驗證遷移成功
6. 啟動新版本應用

---

## 遷移檔案命名規範

```
<revision_id>_<description>.py
```

例如：
- `001_initial_schema.py` - 初始結構
- `002_add_priority_to_tasks.py` - 添加優先級欄位
- `003_create_categories_table.py` - 創建分類表

---

## 進階：撰寫自訂遷移

有時 autogenerate 無法處理複雜變更（如資料轉換），需要手動撰寫：

```python
def upgrade() -> None:
    # 1. 添加新欄位（允許 NULL）
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True))

    # 2. 填充預設值
    op.execute('UPDATE tasks SET priority = 1')

    # 3. 設定為 NOT NULL
    op.alter_column('tasks', 'priority', nullable=False)

def downgrade() -> None:
    op.drop_column('tasks', 'priority')
```

---

## 參考資料

- [Alembic 官方文件](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 官方文件](https://docs.sqlalchemy.org/)

---

**最後更新**：2026-01-14
