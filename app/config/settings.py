"""Application configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-20250514"

    # Logging
    log_level: str = "INFO"

    # Application
    max_resume_size_mb: int = 10
    max_job_ad_length: int = 50000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
