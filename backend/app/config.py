from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "LMS Backend API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/lms_db?charset=utf8mb4"
    TEST_DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/lms_test_db?charset=utf8mb4"

    @field_validator("DATABASE_URL", "TEST_DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("mysql://"):
                return v.replace("mysql://", "mysql+pymysql://", 1)
            elif v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql://", 1)
        return v

    JWT_SECRET_KEY: str = "dev-only-insecure-secret-change-in-production-32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "uploads"
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_MATERIAL_SIZE_MB: int = 50
    MAX_ASSIGNMENT_FILE_SIZE_MB: int = 25
    MAX_IMAGE_SIZE_MB: int = 5

    S3_ENDPOINT_URL: str = ""
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "us-east-1"

    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@institute-lms.example"
    FRONTEND_RESET_URL: str = "http://localhost:5173/reset-password"

    INSTITUTE_NAME: str = "Apex Training Institute"
    INSTITUTE_TAGLINE: str = "Center for Professional & Technical Excellence"

    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_RESET: str = "5/minute"
    RATE_LIMIT_ENABLED: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
