# config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # AWS Credentials (Optional - will use IAM role if not provided)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_REGION: str = "us-east-1"  # Or your preferred region

    # Resource Names
    S3_BUCKET_NAME: str
    DYNAMODB_USERS_TABLE: str = "diia_hack_users"
    DYNAMODB_REQUESTS_TABLE: str = "diia_hack_requests"

    # Google Auth
    GOOGLE_CLIENT_ID: str  # From Google Cloud Console

    # Core AI Service (The GPU machine)
    CORE_AI_URL: str = "http://localhost:8080"  # Placeholder for now

    TRANSLATION_ENDPOINT: str | None = os.getenv("TRANSLATION_ENDPOINT")
    OCR_ENDPOINT: str | None = os.getenv("OCR_ENDPOINT")

    class Config:
        env_file = ".env"


settings = Settings()
print(f"AWS Region: {settings.AWS_REGION}")
print(f"Using explicit credentials: {settings.AWS_ACCESS_KEY_ID is not None}")
