# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EntroPy Backend"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./entropy.db"

    # 這是 Pydantic v2 的寫法
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# 👇【關鍵修復】這一行必須要加！👇
settings = Settings()
