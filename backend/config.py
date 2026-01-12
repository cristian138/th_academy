from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os

class Settings(BaseSettings):
    # MongoDB Configuration
    mongo_url: str
    db_name: str
    
    # Azure Microsoft Graph Configuration (opcional)
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""
    graph_api_endpoint: str = "https://graph.microsoft.com/v1.0"
    
    # SMTP Configuration - accepts both smtp_host and smtp_server
    smtp_host: str = Field(default="", validation_alias="smtp_server")
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "Sistema Talento Humano"
    
    # Storage Configuration
    storage_type: str = "local"  # local or onedrive
    storage_path: str = "/var/www/jotuns-th/storage"
    
    # JWT Configuration - accepts both jwt_secret and jwt_secret_key
    jwt_secret: str = Field(default="your-secret-key-change-in-production-min-32-chars", validation_alias="jwt_secret_key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS Configuration
    cors_origins: str = "*"
    
    # Application Configuration
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
