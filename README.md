# EntroPy v1.0：個人戰略指揮系統設計規格書

## 1. 核心哲學 (Core Philosophy)

這不僅僅是一個待辦清單，而是一個**「抗熵系統 (Anti-Entropy System)」**。

- **目標：** 在數位實驗高中的多變學制下，維持學業生存（Maintenance），同時推進 School 42 的技術進化（Evolution）。
- **隱喻：** **重型物流 (Heavy Logistics)** x **賽博龐克控制台 (Cyberpunk Console)**。
- **平台策略：** **Desktop First (電腦優先)**，強調滑鼠拖曳的精準手感與大螢幕的戰略視野。

---

## 2. 視覺語言系統 (Visual Language System)

採用 **Neo-Brutalism (新粗獷主義)** 結合 **Bento Grid (便當盒佈局)**。

- **結構 (Structure)：**
- **邊框：** 所有元件皆有 `2px solid #000000` 黑色邊框。無陰影 (No Drop-shadow)，無 3D 導角。
- **圓角：** 標準狀態 `border-radius: 12px`；緊急狀態/鎖定狀態 `border-radius: 0px` (尖角)。

- **字體 (Typography)：**
- **標題：** `Archivo Black` 或 `Inter (Extra Bold)` - 寬版、有力、工業感。
- **數據/細節：** `JetBrains Mono` 或 `Roboto Mono` - 等寬字體，強調駭客風格。

- **色票 (Color Palette)：**
- **School (Maintenance)：** 冷靜藍 (`#AEE2FF`) -> 警告黃 (`#FFEA20`) -> 危機紅 (`#FF5B5B`)。
- **Skill (Evolution)：** 深空紫 (`#9D44C0`) -> 霓虹紫 (`#E056FD`)。
- **Done/System：** 終端機綠 (`#00E676`)、深灰 (`#1A1A1A`)。
- **Blackhole：** 虛空黑 (`#000000`) 搭配 粒子紅 (`#FF003C`)。

---

## 3. 系統架構：三階段分頁 (The 3-Stage Pipeline)

系統分為三個獨立的 Tabs，分別對應不同的心智狀態：**輸入 (Logistics)** -> **規劃 (Dashboard)** -> **執行 (Runtime)**。

### 分頁一：LOGISTICS (後勤輸入與分流)

**功能：** 接收混沌資訊，透過 AI 轉化為結構化原子任務。

- **1.1 輸入介面 (Input Mechanism)**
- **觸發：** 按住 `Space` 鍵或點擊底部長條膠囊按鈕 `[ HOLD TO SPEAK ]`。
- **動畫：** 按鈕變形為聲波頻譜 (Audio visualizer)，背景變暗。
- **AI 處理：**
- **STT + LLM：** 語音轉文字後，LLM 進行意圖分析。
- **原子化拆解 (Atomization)：** 如果你說「我要學 C 語言」，AI **不會**生成一張「學 C 語言」的卡片，而是拆解成：「閱讀 Pointer 章節 (1h)」、「實作 Swap 練習 (30m)」。

- **1.2 中央舞台 (The Staging Area)**
- 解析完成的任務以 **「原形卡片 (Draft Cards)」** 形式堆疊在畫面中央。
- **線上修正 (Inline Editing)：** 點擊卡片上的文字可直接修改標題；點擊日期跳出迷你日曆。

- **1.3 拖曳分流 (Drag & Route)**
- 畫面右側設有四個巨大的「投遞區 (Drop Zones)」，具備磁吸效果：

1. 🟦 **SCHOOL ZONE:** 進入 Dashboard 左區。
2. 🟪 **SKILL ZONE:** 進入 Dashboard 右區。
3. ⬜ **MISC:** 進入雜項區。
4. ⬛ **INCINERATOR (焚化爐):**

- **視覺：** 帶有黃黑警示條紋的區域。
- **互動：** 拖入放開後，卡片被**碎紙機特效 (Glitch Shredder)** 粉碎，伴隨電子雜訊音效 `Zzt-dorp`。

---

### 分頁二：DASHBOARD (戰略指揮中心)

**功能：** 全局總覽，視覺化死線壓力，裝填任務。

- **2.1 HUD 抬頭顯示器 (Top Bar)**
- **左側 User Profile:** 太空人頭像 + `Lv. 1.42` + 細長的 XP 進度條。
- **右側 Blackhole Status:**
- 顯示：`BLACKHOLE: 12 DAYS`。
- **動態懲罰：** 若天數 < 3，螢幕邊緣出現紅色暈影 (Vignette)，像遊戲中的瀕死紅光。若歸零，數字碎裂，連勝紀錄 (Streak) 歸零。

- **2.2 雙核心儀表板佈局 (Dual-Core Grid)**
- **左區 [MAINTENANCE] (學校/生存):**
- **排序邏輯：** 絕對時間排序 (Time-to-Live)。死線最近的在最上面。
- **卡片設計 (School Card):**
- **左側 (70%):** `#MATH` (Tag) + `Calculus Homework` (Title)。
- **右側 (30%):** **熱度倒數區**。背景色隨時間變紅。顯示巨大數字 `2` + `DAYS LEFT`。若小於 24h，數字變為 `14` + `HOURS` 且微幅閃爍。
- **情緒化排版：** 緊急的卡片高度會自動變高 (Row Span)，佔據更多視野。

- **右區 [EVOLUTION] (技能/42):**
- **排序邏輯：** XP 價值排序。
- **卡片設計 (Skill Card):**
- 背景為深色網格。
- 內容強調 **原子任務目標** (e.g., `ft_atoi`)。
- 右側顯示：`+500 XP` (獎勵預覽)。

- **2.3 底部常駐：The Payload Dock (物流裝載區)**
- **位置：** 螢幕最底部置中，半透明磨砂玻璃質感。
- **結構：** 3 個空插槽 (Slots) + 右側一個 **[ ENGAGE ]** 發射按鈕。
- **互動 (The Loading Ritual)：**
- 將 Dashboard 上的方塊拖曳至插槽。
- **音效：** `Ka-clack` (槍枝上膛或機械鎖定聲)。
- **限制：** 最多 3 個。滿了之後再拖會被彈開 (Bounciness)，強迫單工。

- **發射 (Launch)：**
- 只有當插槽內有任務時，[ ENGAGE ] 按鈕才會亮起黃光並跳動。
- 點擊後，執行 **轉場動畫**：Dashboard 後退變暗，Dock 向上滑動覆蓋全螢幕，進入 Tab 3。

---

### 分頁三：RUNTIME (執行與專注)

**功能：** 深度工作，排除干擾，結算獎勵。

- **3.1 生產線視圖 (Production Line)**
- 剛剛裝填的 3 個任務，現在變成螢幕上巨大的三張並排卡片。
- 背景全黑或深灰，無其他 UI 干擾。

- **3.2 專注模式 (Focus Session)**
- 點擊其中一張卡片，進入**全螢幕單一視角**。
- **番茄鐘 (Pomodoro):** 中央顯示巨大倒數計時。
- **視覺回饋：** 卡片邊框隨著呼吸頻率發出微光 (Breathing Light)。

- **3.3 提交與結算 (Commit & Reward)**
- 任務完成後，點擊 **[ COMMIT ]** 按鈕。
- **升空動畫 (The Rocket Launch):**
- 卡片瞬間收縮成一個發光球體。
- 尾部噴射出幾何線條，向上衝出螢幕頂端。
- **音效：** `Whoosh` (氣閥釋放聲) + `Ding` (XP 獲得聲)。

- **數據回饋：**
- 左上角 XP 條瞬間填滿一格。
- Blackhole 天數 `+1` (學校任務) 或 `+3` (技能任務)。
- 該插槽變空，顯示 `SLOT EMPTY`。

---

## 4. 使用者旅程設計 (Target User Journey)

**場景：週五晚上，身為 T-School 學生，你需要管理週末進度。**

1. **Input (Tab 1):**

- 你對著電腦說：「這週末要把物理期末報告寫完，然後我要把 C 語言的指標搞懂，還要記得幫媽媽買咖啡。」
- AI 生成三張卡片：「物理報告 (School)」、「指標練習 (Skill)」、「買咖啡 (Misc)」。
- 你拖曳分類：物理->藍區，指標->紫區，買咖啡->灰區。

2. **Plan (Tab 2):**

- 你看到物理報告卡片是紅色的（剩 2 天），而且因為很急，它在左側變得很大一張。
- 你把它拖進底部的 **Dock Slot 1**。
- 你想著 42 的進度，把「指標練習」拖進 **Dock Slot 2**。
- 你按下發光的 **[ ENGAGE ]**。

3. **Execute (Tab 3):**

- 進入黑暗的專注空間。
- 你先點擊「物理報告」，開啟 50 分鐘番茄鐘。
- 完成後 Commit，看著它化為光束飛走，Blackhole 天數加 1，生存確認。
- 接著你點擊「指標練習」，繼續戰鬥。

---

## 5. 技術與開發建議 (Tech Stack Hint)

- **Frontend:** React / Next.js
- **Styling:** Tailwind CSS (處理 Flat Colors 很方便) + Framer Motion (處理 Bento Grid 的變大變小、拖曳、碎紙機動畫)。
- **State Management:** Zustand 或 React Context (管理跨 Tab 的 Dock 狀態)。

- **Backend:** Python (FastAPI)
- **AI:** OpenAI API (Whisper for Audio, GPT-4o for parsing intent).
- **DB:** SQLite (本機開發) 或 Supabase。
