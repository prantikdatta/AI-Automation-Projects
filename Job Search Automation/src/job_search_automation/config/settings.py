from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Every environment variable should be accessed only through this class.
    """

    # ==========================================================
    # APPLICATION
    # ==========================================================

    APP_NAME: str = "Job Search Automation"

    APP_ENV: str = "development"

    LOG_LEVEL: str = "INFO"

    # ==========================================================
    # RAPIDAPI
    # ==========================================================

    RAPIDAPI_KEY: str = Field(...)

    RAPIDAPI_HOST: str = Field(...)

    RAPIDAPI_BASE_URL: str = (
        "https://jsearch.p.rapidapi.com"
    )

    # ==========================================================
    # APIFY
    # ==========================================================

    APIFY_API_TOKEN: str = Field(...)

    APIFY_ACTOR_ID: str = Field(...)

    # ==========================================================
    # GEMINI
    # ==========================================================

    GEMINI_API_KEY: str = Field(...)

    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ==========================================================
    # ADZUNA
    # ==========================================================

    ADZUNA_APP_ID: str = ""

    ADZUNA_APP_KEY: str = ""

    # ==========================================================
    # SERPAPI
    # ==========================================================

    SERPAPI_API_KEY: str = ""

    # ==========================================================
    # JOOBLE
    # ==========================================================

    JOOBLE_API_KEY: str = ""

    # ==========================================================
    # GOOGLE SHEETS
    # ==========================================================

    GOOGLE_SHEET_ID: str = ""

    GOOGLE_WORKSHEET_NAME: str = "Jobs"

    GOOGLE_CREDENTIALS_FILE: str = (
    "credentials/google-service-account.json"
    )

    GOOGLE_AUDIT_WORKSHEET_NAME: str = "Pipeline Audit"

    # ==========================================================
    # SEARCH DEFAULTS
    # ==========================================================

    DEFAULT_JOB_LIMIT: int = 50

    DEFAULT_POSTED_WITHIN_DAYS: int = 3

    REQUEST_TIMEOUT: int = 30

    # ==========================================================
    # MODEL CONFIG
    # ==========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()