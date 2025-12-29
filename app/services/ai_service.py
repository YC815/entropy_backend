# app/services/ai_service.py
import json
import os
from datetime import datetime
import pytz
from fastapi import UploadFile, HTTPException
import google.generativeai as genai
from app.core.config import settings
from app.schemas.task import TaskCreate, TaskType

# 設定 Google Gemini API
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class AIService:

    @staticmethod
    async def process_audio_instruction(file: UploadFile) -> list[TaskCreate]:
        """
        【終極方案】Gemini 2.5 Flash Lite 原生多模態處理
        輸入：音檔 (Bytes)
        輸出：結構化任務 (JSON)
        說明：跳過 STT 步驟，直接讓 AI 聽聲音並回傳 JSON
        """

        # 1. 準備環境資訊
        local_tz = pytz.timezone(settings.TZ)
        now = datetime.now(local_tz)
        current_time_str = now.strftime("%Y-%m-%d %A %H:%M")

        # 2. 讀取音檔並準備 Payload
        # Gemini API 需要 mime_type (例如 audio/mp3, audio/wav)
        file_content = await file.read()
        mime_type = file.content_type or "audio/mp3"  # 預設 fallback

        # 3. 定義 System Prompt (針對聲音輸入優化)
        system_prompt = f"""
        你是一個高科技戰略控制台 'EntroPy' 的後勤官。
        當前時間: {current_time_str} ({settings.TZ})。

        【任務目標】
        聆聽使用者的語音指令，直接將其轉化為結構化的「原子任務」JSON。

        【語音處理與校對】
        - 你的聽力極佳。請忽略語助詞（嗯、啊、然後）。
        - 自動修正同音錯字（例如：「講教」->「繳交」）。
        - 根據語氣與內容拆解任務。

        【輸出欄位定義】
        - title: 修正後的精簡標題。
        - type: 'school' | 'skill' | 'misc'
        - xp_value: 10-100 (根據聽起來的緊急度或困難度判斷)
        - deadline: ISO8601 String (YYYY-MM-DDTHH:MM:SS) 或 null。

        【輸出格式】
        Strict JSON Array. Do NOT use Markdown blocks.
        
        Example JSON:
        [
            {{"title": "繳交物理報告", "type": "school", "xp_value": 50, "deadline": "2025-12-30T10:00:00"}}
        ]
        """

        try:
            print(f"✨ Sending Audio to Gemini 2.5 Flash Lite... ({len(file_content)} bytes)")

            # 使用最新的 Flash Lite 模型
            # 注意：如果 API 尚未支援 'gemini-2.5-flash-lite' alias，
            # 可能需要用 'gemini-2.0-flash-lite-preview' 或類似名稱，視當下 Google 策略而定。
            # 這裡我們假設使用 'gemini-2.0-flash-exp' 或 'gemini-1.5-flash' 作為目前可用代號
            # 若您有 2.5 的權限，請直接改為 'gemini-2.5-flash-lite'
            model_name = "gemini-2.5-flash-lite"  # 暫用 1.5 Flash 代表 (2.5 若可用請替換)

            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"response_mime_type": "application/json"}
            )

            # 4. 多模態輸入：提示詞 + 音訊資料
            response = await model.generate_content_async([
                system_prompt,
                {
                    "mime_type": mime_type,
                    "data": file_content
                }
            ])

            print(f"🧠 Gemini Output: {response.text}")

            # 5. 解析 JSON
            result_json = json.loads(response.text)

            # 清洗與轉換
            return AIService._clean_json(result_json)

        except Exception as e:
            print(f"❌ Gemini Multimodal Error: {e}")
            # 如果失敗，這裡很難 fallback，因為我們沒有文字。
            # 實務上可以這裡再呼叫一次純 STT，但通常 Gemini 掛了 STT 也會掛。
            raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

    @staticmethod
    def _clean_json(data):
        # (保持原本的清洗邏輯)
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    return [TaskCreate(**item) for item in value]
        if isinstance(data, list):
            return [TaskCreate(**item) for item in data]
        return []


ai_service = AIService()
