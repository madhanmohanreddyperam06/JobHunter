import os
import urllib.parse
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized Application Configuration.
    Loads values from environment variables or .env file using Pydantic Settings.
    """
    APP_NAME: str = "Job Application Command Center"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database Configuration (MySQL 8)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_NAME: str = "job_command_center"
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000"

    # Storage Configuration
    STORAGE_DIR: str = "storage"

    # JWT Security Configuration
    JWT_SECRET_KEY: str = "insecure_dev_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs a sanitized SQLAlchemy MySQL connection URL.
        URL-encodes both username and password to handle special characters properly.
        """
        encoded_user = urllib.parse.quote_plus(self.DATABASE_USER)
        encoded_password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}@"
            f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Returns parsed list of allowed CORS origin URLs.
        """
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def resumes_storage_path(self) -> str:
        """
        Absolute filesystem path to the resume uploads storage directory.
        Defaults to backend/storage/resumes.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, self.STORAGE_DIR, "resumes")
        os.makedirs(path, exist_ok=True)
        return path


# Global application settings singleton
settings = Settings()
