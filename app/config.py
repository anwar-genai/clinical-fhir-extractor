"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Clinical FHIR Extractor"
    app_version: str = "0.2.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./clinical_fhir.db"
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # JWT Authentication
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Security
    password_min_length: int = 8
    password_max_length: int = 72  # bcrypt limit
    api_key_length: int = 32
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 10
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    
    # LangChain
    chunk_size: int = 1000
    chunk_overlap: int = 200
    vector_search_k: int = 4
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()

