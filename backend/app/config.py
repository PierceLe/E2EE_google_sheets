from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/e2ee_sheets"
    database_url_test: str = "postgresql://username:password@localhost:5432/e2ee_sheets_test"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Google Sheets API
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    
    # Application
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Encryption
    master_key_salt: str = "your-master-key-salt"
    key_derivation_iterations: int = 100000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
