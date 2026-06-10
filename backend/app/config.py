"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"
    bigquery_dataset: str = "margintrust"
    fivetran_mcp_mode: str = "mock"
    fivetran_api_key: str = ""
    fivetran_api_secret: str = ""
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    use_bigquery: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

