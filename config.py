"""Application configuration management."""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # App
    PROJECT_NAME: str = "KindlyCloud - Kindergarten Management System"
    PROJECT_DESCRIPTION: str = "A comprehensive REST API for kindergarten management"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://kindergarten:0ha8oxyPXxSe2DCl1efWU27R0YSxIiiG@dpg-d6jcj1s50q8c739ju3m0-a.singapore-postgres.render.com/kindlycloud"
    DATABASE_ECHO: bool = False
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-keep-it-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common environment labels in addition to strict booleans."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
