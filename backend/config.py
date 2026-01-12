from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Optional
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
    
    # SMTP Configuration
    smtp_host: str = ""
    smtp_server: str = ""  # Alias alternativo
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "Sistema Talento Humano"
    
    # Storage Configuration
    storage_type: str = "local"
    storage_path: str = "/var/www/jotuns-th/storage"
    
    # JWT Configuration
    jwt_secret: str = "your-secret-key-change-in-production-min-32-chars"
    jwt_secret_key: str = ""  # Alias alternativo
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS Configuration
    cors_origins: str = "*"
    
    # Application Configuration
    debug: bool = False
    
    def get_smtp_host(self) -> str:
        """Get SMTP host from either smtp_host or smtp_server"""
        return self.smtp_host or self.smtp_server
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret from either jwt_secret or jwt_secret_key"""
        return self.jwt_secret_key or self.jwt_secret
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
