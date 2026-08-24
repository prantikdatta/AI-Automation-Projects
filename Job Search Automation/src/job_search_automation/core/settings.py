from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    All environment variables are loaded from the project .env file.
    This is the only place in the application that should access
    environment variables directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    API_NAME: str = Field(default="Job Search Automation")
    API_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)

    # ==========================================================
    # Provider Priority
    # ==========================================================

    PRIMARY_PROVIDER: str = Field(default="rapidapi")
    SECONDARY_PROVIDER: str = Field(default="apify")
    TERTIARY_PROVIDER: str = Field(default="jobspy")

    # ==========================================================
    # RapidAPI
    # ==========================================================

    RAPIDAPI_KEY: str = ""
    RAPIDAPI_HOST: str = "jsearch.p.rapidapi.com"

    # ==========================================================
    # Apify
    # ==========================================================

    APIFY_API_TOKEN: str = ""
    APIFY_ACTOR_ID: str = "epctex/google-jobs-scraper"

    # ==========================================================
    # Gemini
    # ==========================================================

    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"

    # ==========================================================
    # Google Sheets
    # ==========================================================

    GOOGLE_SERVICE_ACCOUNT_JSON: str = (
        "credentials/google-service-account.json"
    )

    SPREADSHEET_ID: str = ""

    # ==========================================================
    # Scheduler
    # ==========================================================

    SEARCH_INTERVAL_DAYS: int = 2
    SEARCH_LIMIT: int = 50

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()