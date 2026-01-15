# app/services/ai_service.py
import asyncio
import json
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Any

import pytz
import requests
from fastapi import UploadFile, HTTPException
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.task import TaskCreate

# 初始化新版 Client
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"
GROQ_LANGUAGE = "zh"
GEMINI_AUDIO_TIMEOUT_SEC = 90
GEMINI_TEXT_TIMEOUT_SEC = 45
GROQ_TIMEOUT_SEC = 90
MAX_RETRIES = 3
MIN_AUDIO_BYTES = 500
MIN_AUDIO_DURATION_SEC = 0.5


def _preview(text: str, limit: int = 1200) -> str:
    """Trim long strings for logging."""
    if text is None:
        return ""
    return text if len(text) <= limit else f"{text[:limit]}...[truncated {len(text) - limit} chars]"


class AIService:
    @staticmethod
    async def process_audio_instruction(file: UploadFile) -> tuple[list[TaskCreate], str]:
        """
        兩段式流程：
        1) Groq Whisper 取得 rough transcript + segments
        2) Gemini 多模態校正 transcript（音檔 + Groq 結果）
        3) Gemini 文字模式做任務抽取（使用校正後 transcript）
        """
        if not client:
            raise HTTPException(status_code=500, detail="Gemini API Key not configured")
        if not settings.GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="Groq API Key not configured")

        local_tz = pytz.timezone(settings.TZ)
        now = datetime.now(local_tz)
        current_time_str = now.strftime("%Y-%m-%d %A %H:%M")
        model_name = getattr(settings, "GEMINI_MODEL", DEFAULT_GEMINI_MODEL) or DEFAULT_GEMINI_MODEL

        file_content = await file.read()
        mime_type = file.content_type or "audio/mp3"
        filename = file.filename or "audio.webm"
        if len(file_content) < MIN_AUDIO_BYTES:
            print(f"⛔ Audio too small ({len(file_content)} bytes) < MIN_AUDIO_BYTES={MIN_AUDIO_BYTES}")
            raise HTTPException(
                status_code=400,
                detail=f"Audio too small ({len(file_content)} bytes). Recording/upload likely failed."
            )

        source_suffix = AIService._guess_suffix(filename, mime_type)
        probe_info = await AIService._probe_audio(file_content, source_suffix)
        audio_stream = next((s for s in probe_info.get("streams", []) if s.get("codec_type") == "audio"), None)
        duration = float(
            (audio_stream or {}).get("duration")
            or probe_info.get("format", {}).get("duration")
            or 0
        )
        if not audio_stream or duration < MIN_AUDIO_DURATION_SEC:
            print(f"⛔ Invalid audio stream or too short. duration={duration:.2f}s streams={len(probe_info.get('streams', []))}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio stream or too short (duration={duration:.2f}s)"
            )

        wav_bytes, wav_mime = await AIService._convert_to_wav(file_content, source_suffix, mime_type)
        wav_name = "audio.wav" if wav_mime == "audio/wav" else filename

        print(f"🎧 Audio received: {len(file_content)} bytes, mime={mime_type}, name={filename}")
        print(f"🛰️ Using model: {model_name}")

        groq_result = await AIService._groq_transcribe(wav_bytes, wav_name, wav_mime)
        rough_transcript = (groq_result.get("text") or "").strip()
        rough_segments = groq_result.get("segments") or []
        if not rough_transcript:
            print("⛔ Groq transcription returned empty text")
            raise HTTPException(status_code=400, detail="Groq transcription returned empty text")
        print(f"📝 Groq transcript len={len(rough_transcript)}, segments={len(rough_segments)}")

        corrected_transcript = await AIService._gemini_correct_transcript(
            model_name=model_name,
            file_content=wav_bytes,
            mime_type=wav_mime,
            rough_transcript=rough_transcript,
            rough_segments=rough_segments
        )
        transcript_clean = AIService._clean_transcript(corrected_transcript or rough_transcript)

        tasks = await AIService._gemini_extract_tasks(
            model_name=model_name,
            transcript=transcript_clean,
            current_time_str=current_time_str
        )

        print(f"✅ Parsed {len(tasks)} tasks; transcript length={len(transcript_clean)} characters.")
        return tasks, transcript_clean

    @staticmethod
    async def _groq_transcribe(file_content: bytes, filename: str, mime_type: str) -> dict:
        """
        呼叫 Groq Whisper 取得逐字稿（verbose_json 含 segments）。
        """
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        files = {"file": (filename, file_content, mime_type)}
        data = {
            "model": GROQ_MODEL,
            "response_format": "verbose_json",
            "language": GROQ_LANGUAGE,
        }

        def _call():
            print(f"📤 Groq request: model={GROQ_MODEL}, filename={filename}, mime={mime_type}, bytes={len(file_content)}, format=verbose_json, language={GROQ_LANGUAGE}")
            resp = requests.post(
                GROQ_TRANSCRIBE_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=GROQ_TIMEOUT_SEC
            )
            resp.raise_for_status()
            resp_json = resp.json()
            print(f"📥 Groq response: {_preview(json.dumps(resp_json, ensure_ascii=False))}")
            return resp_json

        try:
            return await asyncio.to_thread(_call)
        except requests.HTTPError as e:
            detail = f"Groq transcription failed: {e.response.text if e.response else str(e)}"
            print(f"❌ {detail}")
            raise HTTPException(status_code=502, detail=detail)
        except Exception as e:
            print(f"❌ Groq transcription error: {e}")
            raise HTTPException(status_code=500, detail=f"Groq transcription error: {e}")

    @staticmethod
    async def _gemini_correct_transcript(
        model_name: str,
        file_content: bytes,
        mime_type: str,
        rough_transcript: str,
        rough_segments: list[dict]
    ) -> str:
        """
        多模態校正逐字稿：音檔 + Groq 粗稿 → 更準的 transcript。
        """
        context_block = (
            "你是一個語音校正器，會同時收到原始音檔與 Whisper 粗稿。"
            "請以音檔為準，修正粗稿錯字/漏字，保持原語言與語序，不要添加編號或時間碼。\n"
            f"Whisper transcript (rough):\n{rough_transcript}\n\n"
            f"Whisper segments (rough JSON):\n{json.dumps(rough_segments, ensure_ascii=False)}"
        )
        print(f"📤 Gemini transcript input: system='語音校正', audio_bytes={len(file_content)}, mime={mime_type}")
        print(f"📤 Gemini transcript context preview: {_preview(context_block)}")

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=file_content, mime_type=mime_type),
                        types.Part.from_text(text=context_block),
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction="你是語音校正專家，只輸出校正後的 transcript JSON 物件，禁止編造內容。",
                        response_mime_type="application/json",
                        response_schema=AIService._transcript_schema(),
                        temperature=0
                    )
                ),
                timeout=GEMINI_AUDIO_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            print(f"⏱️ Gemini transcript correction timed out after {GEMINI_AUDIO_TIMEOUT_SEC}s, fallback to Groq text.")
            return rough_transcript
        except Exception as e:
            print(f"❌ Gemini transcript correction error: {e}, fallback to Groq text.")
            return rough_transcript

        raw_text = response.text or ""
        print(f"🧠 Gemini transcript output len={len(raw_text)}")
        print(f"📥 Gemini transcript raw: {_preview(raw_text)}")
        try:
            parsed = json.loads(raw_text)
            transcript = (parsed.get("transcript") or "").strip()
            return transcript or rough_transcript
        except Exception as e:
            print(f"❌ Transcript parse error: {e}, fallback to Groq text.")
            return rough_transcript

    @staticmethod
    async def _gemini_extract_tasks(
        model_name: str,
        transcript: str,
        current_time_str: str
    ) -> list[TaskCreate]:
        """
        純文字模式抽取任務（避免再傳音檔，降低延遲）。
        """
        system_prompt = AIService._build_prompt(current_time_str)
        last_error: str | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            user_text = transcript if not last_error else f"{transcript}\n先前錯誤：{last_error}"
            print(f"🚀 Gemini task extraction (attempt {attempt})...")
            print(f"📤 Gemini tasks input: system_prompt_len={len(system_prompt)}, transcript_preview={_preview(user_text)}")
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=[types.Part.from_text(text=user_text)],
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=AIService._tasks_response_schema(),
                            temperature=0
                        )
                    ),
                    timeout=GEMINI_TEXT_TIMEOUT_SEC
                )
            except asyncio.TimeoutError:
                last_error = f"Gemini task extraction timeout after {GEMINI_TEXT_TIMEOUT_SEC}s"
                print(f"⏱️ {last_error}")
                continue
            except Exception as e:
                last_error = f"Gemini task extraction error: {e}"
                print(f"❌ {last_error}")
                continue

            raw_text = response.text or ""
            print(f"🧠 Gemini task output len={len(raw_text)}")
            print(f"📥 Gemini task raw: {_preview(raw_text)}")
            try:
                tasks, _ = AIService._parse_ai_output(raw_text)
                return tasks
            except (ValueError, ValidationError) as parse_error:
                last_error = str(parse_error)
                print(f"🔁 Task parse invalid (attempt {attempt}): {last_error}")
                continue

        raise HTTPException(status_code=400, detail=f"Task extraction failed after {MAX_RETRIES} attempts: {last_error}")

    @staticmethod
    def _clean_transcript(raw: str) -> str:
        """
        移除模型產生的時間碼/序號，避免被當成任務內容。
        """
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        time_pattern = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?(?::\d{2})?$")
        cleaned_lines = []

        for line in lines:
            tokens = line.split()
            if tokens and all(time_pattern.match(tok) for tok in tokens):
                continue
            cleaned_lines.append(line)

        cleaned = " ".join(cleaned_lines).strip()
        if not cleaned:
            raise HTTPException(status_code=400, detail="Transcription contained no speech content")
        return cleaned

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
        - 嚴格輸出 JSON 物件，無 Markdown、無註解。
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
        回傳 JSON 物件，且只能含下列欄位：
        {{
            "tasks": [
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
        }}
        - 僅能根據提供的 transcript 內容生成任務，禁止臆測或新增額外任務。
        """

    @staticmethod
    def _tasks_response_schema() -> types.Schema:
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "tasks": types.Schema(
                    type=types.Type.ARRAY,
                    description="Tasks parsed from the transcript",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "title": types.Schema(type=types.Type.STRING),
                            "type": types.Schema(
                                type=types.Type.STRING,
                                enum=["school", "skill", "misc"]
                            ),
                            "difficulty": types.Schema(type=types.Type.INTEGER),
                            "xp_value": types.Schema(type=types.Type.INTEGER),
                            "deadline": types.Schema(
                                type=types.Type.STRING,
                                description="ISO-8601 with timezone offset or null"
                            )
                        },
                        required=["title", "type", "difficulty", "xp_value", "deadline"],
                    )
                ),
            },
            required=["tasks"],
        )

    @staticmethod
    def _parse_ai_output(raw_text: str) -> tuple[list[TaskCreate], str]:
        try:
            parsed_json: Any = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI output is not valid JSON: {e}")

        tasks_payload = AIService._extract_task_list(parsed_json)
        if not tasks_payload:
            raise ValueError("AI output is empty or missing task list")

        tasks = [TaskCreate(**item) for item in tasks_payload]
        return tasks, ""

    @staticmethod
    def _transcript_schema() -> types.Schema:
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "transcript": types.Schema(
                    type=types.Type.STRING,
                    description="Corrected transcript without timestamps or numbering"
                )
            },
            required=["transcript"]
        )

    @staticmethod
    def _guess_suffix(filename: str, mime_type: str) -> str:
        lower = filename.lower()
        if lower.endswith(".wav"):
            return ".wav"
        if lower.endswith(".mp3"):
            return ".mp3"
        if lower.endswith(".m4a"):
            return ".m4a"
        if lower.endswith(".ogg"):
            return ".ogg"
        if lower.endswith(".flac"):
            return ".flac"
        if "wav" in mime_type:
            return ".wav"
        if "mp3" in mime_type:
            return ".mp3"
        if "m4a" in mime_type:
            return ".m4a"
        if "ogg" in mime_type:
            return ".ogg"
        return ".webm"

    @staticmethod
    async def _probe_audio(file_content: bytes, suffix: str) -> dict:
        """
        使用 ffprobe 驗證音軌與時長，避免空檔/壞檔。
        """
        def _call():
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(file_content)
                input_path = f.name
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                input_path,
            ]
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                return json.loads(out)
            finally:
                try:
                    subprocess.run(["rm", "-f", input_path], check=False)
                except Exception:
                    pass

        try:
            return await asyncio.to_thread(_call)
        except FileNotFoundError:
            print("⚠️ ffprobe not found; skipping probe and trusting upload.")
            return {"format": {"duration": 1}, "streams": [{"codec_type": "audio", "duration": 1}]}
        except subprocess.CalledProcessError as e:
            print(f"⚠️ ffprobe failed, skipping probe and trusting upload. error={e.output.decode(errors='ignore')}")
            return {"format": {"duration": 1}, "streams": [{"codec_type": "audio", "duration": 1}]}
        except Exception as e:
            print(f"⚠️ ffprobe error, skipping probe and trusting upload. error={e}")
            return {"format": {"duration": 1}, "streams": [{"codec_type": "audio", "duration": 1}]}

    @staticmethod
    async def _convert_to_wav(file_content: bytes, source_suffix: str, original_mime: str) -> tuple[bytes, str]:
        """
        將輸入音訊轉為 16k mono wav，提升 ASR 穩定度。
        """
        def _call():
            with tempfile.NamedTemporaryFile(suffix=source_suffix, delete=False) as src:
                src.write(file_content)
                src_path = src.name
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst:
                dst_path = dst.name

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                src_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                dst_path,
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                with open(dst_path, "rb") as f:
                    return f.read()
            finally:
                for path in (src_path, dst_path):
                    try:
                        subprocess.run(["rm", "-f", path], check=False)
                    except Exception:
                        pass

        try:
            wav_bytes = await asyncio.to_thread(_call)
            print(f"🎛️ Converted audio to wav: {len(wav_bytes)} bytes")
            return wav_bytes, "audio/wav"
        except FileNotFoundError:
            print("⚠️ ffmpeg not found; using original audio bytes.")
            return file_content, original_mime
        except subprocess.CalledProcessError as e:
            print(f"⚠️ ffmpeg conversion failed, using original audio bytes. error={e.stderr.decode(errors='ignore')}")
            return file_content, original_mime
        except Exception as e:
            print(f"⚠️ ffmpeg conversion error, using original audio bytes. error={e}")
            return file_content, original_mime

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
