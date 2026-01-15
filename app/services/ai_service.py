# app/services/ai_service.py
import json
from datetime import datetime
from typing import Any

import pytz
from fastapi import UploadFile, HTTPException
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.task import TaskCreate

# 初始化新版 Client
# 注意：這裡不直接 configure，而是建立 client 實體
client = None
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)


class AIService:

    @staticmethod
    async def process_audio_instruction(file: UploadFile) -> list[TaskCreate]:
        """
        【Gemini 2.5 原生多模態】
        輸入：音檔 (Bytes)
        輸出：包含難度與 XP 的結構化任務 (JSON)
        """
        if not client:
            raise HTTPException(status_code=500, detail="Gemini API Key not configured")

        # 1. 準備環境資訊
        local_tz = pytz.timezone(settings.TZ)
        now = datetime.now(local_tz)
        current_time_str = now.strftime("%Y-%m-%d %A %H:%M")

        # 2. 讀取音檔
        file_content = await file.read()
        mime_type = file.content_type or "audio/mp3"

        # 3. 定義 System Prompt (包含新的數學模型邏輯)
        system_prompt = AIService._build_prompt(current_time_str)

        try:
            print(f"✨ Sending Audio to Gemini (New SDK)... ({len(file_content)} bytes)")
            last_error: str | None = None

            for attempt in range(3):
                # ✅ 自我修正：把上一次的錯誤附加給模型重新生成
                prompt_with_feedback = (
                    system_prompt
                    if not last_error
                    else f"{system_prompt}\n先前輸出錯誤：{last_error}\n請重新輸出純 JSON 陣列，保持同一格式與時區規則。"
                )

                response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=prompt_with_feedback),
                                types.Part.from_bytes(data=file_content, mime_type=mime_type)
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )

                print(f"🧠 Gemini Output (attempt {attempt + 1}): {response.text}")

                try:
                    return AIService._parse_ai_output(response.text)
                except (ValueError, ValidationError) as parse_error:
                    last_error = str(parse_error)
                    print(f"🔁 AI output invalid (attempt {attempt + 1}): {last_error}")
                    continue

            raise HTTPException(status_code=400, detail=f"AI output invalid after 3 attempts: {last_error}")

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

    @staticmethod
    def _build_prompt(current_time_str: str) -> str:
        return f"""
        你是一個高科技戰略控制台 'EntroPy' 的後勤官。
        當前時間: {current_time_str} ({settings.TZ})。

        【任務目標】
        聆聽使用者的語音指令，將其轉化為符合「抗熵數學模型」的原子任務。

        【時間與格式要求】
        - 時區一律視為 {settings.TZ}；輸出 ISO-8601 含時區偏移 (例如 2025-12-30T09:00:00+08:00)。
        - 僅有日期時，預設時間為 23:59。
        - 推測模糊時間 (早上/下午/今晚/明天 9 點等) 並填入具體時間 (24h 制)。
        - 嚴格輸出 JSON 陣列，無 Markdown、無註解。
        - 若未提到時間但有日期，請使用時間片語對應表或預設 23:59；若連日期也沒有，deadline 填 null。
        - 如果語句完全沒有任何時間詞或數字，deadline 必須設為該日期的 23:59 ({settings.TZ})；禁止使用 00:00 或 12:00 作為預設時間。
        - 解析相對日期：明天(+1)、後天(+2)、下週一~日=下一個該星期，今天=當日。

        【時間片語對應表 (無具體時刻時使用)】
        - 早上/上午: 09:00
        - 中午: 12:00
        - 下午: 15:00
        - 傍晚/晚上/今晚: 20:00
        - 凌晨/深夜/午夜: 01:00
        - 「晚上八點」等含數字時，轉為 24h 例如 20:00；「下午 1 點」=> 13:00。

        【例子】
        - 「下週一要繳交設計思考」 => deadline 為下週一 23:59 ({settings.TZ})
        - 「明天晚上要交英文非同步」 => deadline 為明天 20:00 ({settings.TZ})
        - 「今天晚上八點想研究 Python 的函式撰寫最佳實踐」 => deadline 為今天 20:00 ({settings.TZ})；type=skill, xp 依專注小時數

        【變數計算邏輯 - 核心規則】
        請根據任務類型，智慧判斷以下數值：

        1. **type="school" (維運任務)**
           - **xp_value**: 設為 0 (學校任務不直接給 XP，而是恢復 HP)。
           - **difficulty** (1-10):
             - 1-3: 簡單雜務 (買文具、填表單)。
             - 4-7: 一般作業、小考、報告。
             - 8-10: 期末考、大型專題、論文 (這會造成高壓力)。

        2. **type="skill" (進化任務)**
           - **difficulty**: 預設為 1 (不重要)。
           - **xp_value**: 請估算該任務需要的「專注小時數」，公式為 `Hours * 100`。
             - 例如：「練 C 語言一小時」 -> 100 XP。
             - 例如：「搞懂 Docker 架構 (約需 3 小時)」 -> 300 XP。

        3. **type="misc" (雜項)**
           - **difficulty**: 1
           - **xp_value**: 10 (象徵性獎勵)

        【輸出格式】
        Strict JSON Array only. No Markdown.
        Example:
        [
            {{
                "title": "微積分期末考準備",
                "type": "school",
                "difficulty": 9,
                "xp_value": 0,
                "deadline": "2025-12-30T23:59:00+08:00"
            }},
            {{
                "title": "練習 ft_printf",
                "type": "skill",
                "difficulty": 1,
                "xp_value": 200,
                "deadline": null
            }}
        ]
        """

    @staticmethod
    def _parse_ai_output(raw_text: str) -> list[TaskCreate]:
        try:
            parsed_json: Any = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI output is not valid JSON: {e}")

        tasks_payload = AIService._extract_task_list(parsed_json)
        if not tasks_payload:
            raise ValueError("AI output is empty or missing task list")

        return [TaskCreate(**item) for item in tasks_payload]

    @staticmethod
    def _extract_task_list(data: Any):
        if isinstance(data, dict):
            for _, value in data.items():
                if isinstance(value, list):
                    return value
        if isinstance(data, list):
            return data
        return []


ai_service = AIService()
