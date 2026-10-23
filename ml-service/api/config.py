"""
Configuration settings for FastAPI ML service.
Loads from environment variables and .env file.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    API_KEY: str = "dev-secret-key-food-waste-2026"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ]

    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models" / "saved"
    METRICS_FILE: Path = BASE_DIR / "models" / "metrics.json"
    BATCH_RESULTS_DIR: Path = BASE_DIR / "reports" / "batch_predictions"

    DEFAULT_BUSINESS_ID: str = "biz_001"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
settings.BATCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
