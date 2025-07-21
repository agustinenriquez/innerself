import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/innerself")
    database_name: str = "innerself"
    
    # JWT
    secret_key: str = os.getenv("JWT_SECRET", "dev-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # GitHub OAuth
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "InnerSelf"

settings = Settings()