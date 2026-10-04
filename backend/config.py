"""
Backend Configuration Settings
------------------------------
Defines application environment variables, paths, and CORS settings.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Movie Recommendation Data Serving API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENV", "development")
    DEBUG: bool = True

    # Server config
    HOST: str = os.getenv("API_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("API_PORT", "8000"))

    # Database paths
    DB_PATH: Path = BASE_DIR / "data" / "serving" / "movies.duckdb"
    PARQUET_DIR: Path = BASE_DIR / "data" / "serving"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw" / "ml-latest-small"

    # External enrichment (TMDB) - optional, only used for posters/descriptions
    TMDB_API_KEY: str = ""

    # CORS origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(BASE_DIR / ".env"),
        extra="ignore",
    )


settings = Settings()
