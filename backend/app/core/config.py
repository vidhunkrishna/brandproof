import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BrandProof"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/brandproof"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Security / JWT
    SECRET_KEY: str = Field(
        default="brandproof-hackathon-insecure-default-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # External LLM Configuration (Configurable via ENV)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    LLM_MODEL: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # In production, disallow default placeholder or empty keys
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            if not v or "insecure" in v.lower() or "change-in-production" in v.lower():
                raise ValueError(
                    "CRITICAL SECURITY ERROR: A secure, non-default SECRET_KEY environment variable "
                    "must be provided in production mode."
                )
        return v


settings = Settings()
