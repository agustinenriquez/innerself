import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/innerself")
    database_name: str = "innerself"
    
    # GitHub
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    # Service Configuration
    service_name: str = "github-integration"

settings = Settings()