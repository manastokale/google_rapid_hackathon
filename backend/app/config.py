"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gcp_project_id: str = ""
    bq_project_id: str = ""
    gcp_region: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"
    bigquery_dataset: str = "margintrust"
    bq_raw_dataset: str = ""
    bq_analytics_dataset: str = "margintrust_analytics"
    google_application_credentials: str = ""
    google_application_credentials_json: str = ""
    fivetran_mcp_mode: str = "mock"
    fivetran_api_key: str = ""
    fivetran_api_secret: str = ""
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    use_bigquery: bool = False

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
