"""
Configuration management using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql://nitter_user:nitter_pass@localhost:5432/nitter_db",
        alias="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_secret_key: str = Field(
        default="change-this-to-a-random-secret-key",
        alias="API_SECRET_KEY"
    )

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        alias="CELERY_RESULT_BACKEND"
    )

    # Scraping
    min_request_delay: int = Field(default=2, alias="MIN_REQUEST_DELAY")
    max_request_delay: int = Field(default=8, alias="MAX_REQUEST_DELAY")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    health_check_interval: int = Field(default=300, alias="HEALTH_CHECK_INTERVAL")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    # Twitter Direct Scraping
    use_twitter_direct: bool = Field(default=False, alias="USE_TWITTER_DIRECT")
    twitter_username: str = Field(default="", alias="TWITTER_USERNAME")
    twitter_password: str = Field(default="", alias="TWITTER_PASSWORD")
    twitter_cookies_file: str = Field(default="", alias="TWITTER_COOKIES_FILE")

    # Proxy
    use_proxy: bool = Field(default=False, alias="USE_PROXY")
    proxy_url: str = Field(default="", alias="PROXY_URL")

    # Monitoring
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/nitter_scraper.log", alias="LOG_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
