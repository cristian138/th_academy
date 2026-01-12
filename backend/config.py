from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # MongoDB Configuration
    mongo_url: str
    db_name: str
    
    # Azure Microsoft Graph Configuration
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""
    graph_api_endpoint: str = "https://graph.microsoft.com/v1.0"
    
    # JWT Configuration
    jwt_secret: str = "your-secret-key-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS Configuration
    cors_origins: str = "*"
    
    # Application Configuration
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
