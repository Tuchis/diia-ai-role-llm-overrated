# config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Credentials
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_SESSION_TOKEN: str
    AWS_REGION: str = "us-east-1"  # Or your preferred region

    # Resource Names
    S3_BUCKET_NAME: str
    DYNAMODB_USERS_TABLE: str = "diia_hack_users"
    DYNAMODB_REQUESTS_TABLE: str = "diia_hack_requests"

    # Google Auth
    GOOGLE_CLIENT_ID: str  # From Google Cloud Console

    # Core AI Service (The GPU machine)
    CORE_AI_URL: str = "http://localhost:8080"  # Placeholder for now

    class Config:
        env_file = ".env"


settings = Settings()
print(settings.AWS_REGION)