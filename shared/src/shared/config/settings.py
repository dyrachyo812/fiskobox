from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    telegram_bot_token: str
    telegram_bot_username: str

    ocr_engine: str = "tesseract"
    ocr_provider: str = "tesseract"
    tesseract_languages: str = "ukr+rus+eng"
    google_application_credentials: str | None = None
    ocr_timeout_seconds: float = 30.0
    google_vision_monthly_limit: int = 1000
    google_vision_warn_threshold: int = 900
    google_vision_enforce_limit: bool = True

    parser_mode: str = "hybrid"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 60.0
    ollama_temperature: float = 0.1

    upload_dir: str = "/data/uploads"

    photo_rate_limit: int = 10
    photo_rate_window_seconds: int = 60
    blur_variance_threshold: float = 100.0
    blur_warn_variance_threshold: float = 250.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
