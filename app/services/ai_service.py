# app/services/ai_service.py
import json
from datetime import datetime
import pytz
from fastapi import UploadFile, HTTPException
from google import genai
from google.genai import types
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
        system_prompt = f"""
        你是一個高科技戰略控制台 'EntroPy' 的後勤官。
        當前時間: {current_time_str} ({settings.TZ})。

        【任務目標】
        聆聽使用者的語音指令，將其轉化為符合「抗熵數學模型」的原子任務。

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
        
        Example JSON Output:
        [
            {{
                "title": "微積分期末考準備", 
                "type": "school", 
                "difficulty": 9, 
                "xp_value": 0, 
                "deadline": "2025-12-30T09:00:00"
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

        try:
            print(f"✨ Sending Audio to Gemini (New SDK)... ({len(file_content)} bytes)")

            # 使用新版 SDK 的 Async 方法
            # model 可嘗試 'gemini-2.0-flash-exp' 或 'gemini-1.5-flash'
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=system_prompt),
                            types.Part.from_bytes(data=file_content, mime_type=mime_type)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )

            print(f"🧠 Gemini Output: {response.text}")

            result_json = json.loads(response.text)
            return AIService._clean_json(result_json)

        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

    @staticmethod
    def _clean_json(data):
        if isinstance(data, dict):
            # 有時候 AI 會多包一層 {"tasks": [...]}
            for key, value in data.items():
                if isinstance(value, list):
                    return [TaskCreate(**item) for item in value]
        if isinstance(data, list):
            return [TaskCreate(**item) for item in data]
        return []


ai_service = AIService()
