# app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EntroPy Backend"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(
        default="sqlite:///./entropy.db",
        description="Database connection URL. Use sqlite:////app/data/entropy.db in Docker"
    )

    # AI Service API Keys
    GROQ_API_KEY: str
    GEMINI_API_KEY: str

    # Timezone for task scheduling
    TZ: str = "Asia/Taipei"

    # 這是 Pydantic v2 的寫法
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# 👇【關鍵修復】這一行必須要加！👇
settings = Settings()
