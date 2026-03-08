from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "KindlyCloud"
    PROJECT_DESCRIPTION: str = "A comprehensive kindergarten management system"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/kindlycloud"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API
    API_V1_STR: str = "/api/v1"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
