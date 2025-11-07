"""
Configuration settings for the database service.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Settings
    api_title: str = "Legislatie Database API"
    api_version: str = "1.0.0"
    api_description: str = "REST API pentru gestionarea actelor legislative"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Database Settings
    database_url: str = "postgresql://legislatie_user:password@localhost:5432/monitoring_platform"
    db_schema: str = "legislatie"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False  # Log SQL queries
    
    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    # Import Settings
    import_batch_size: int = 100
    
    @property
    def async_database_url(self) -> str:
        """Convert psycopg URL to asyncpg URL."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


# Global settings instance
settings = Settings()
