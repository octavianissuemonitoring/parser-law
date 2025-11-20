"""
Configuration settings for the database service.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env (like Docker vars)
    )
    
    # API Settings
    api_title: str = "Legislatie Database API"
    api_version: str = "2.1.0"
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
    # Allow string in env (comma-separated or JSON) so we normalize below
    cors_origins: Optional[str] = None
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
    
    # Security Settings
    api_key: str = ""  # API key for protected endpoints (AI, Export)
    api_key_header: str = "X-API-Key"
    allowed_ips: list[str] = []  # Empty = allow all; specify IPs to whitelist
    
    # AI Service Settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: str = "openai"  # "openai" or "anthropic"
    ai_model: str = "gpt-4o"  # Model to use
    ai_rate_limit_delay: float = 1.0  # Seconds between API calls
    
    # Issue Monitoring Integration
    issue_monitoring_api_url: str = "https://api.issuemonitoring.ro/v1"
    issue_monitoring_api_key: str = ""
    
    @property
    def async_database_url(self) -> str:
        """Convert psycopg URL to asyncpg URL."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


# Global settings instance
settings = Settings()

# Post-process cors_origins to a list[str]
try:
    cors_val = settings.cors_origins
    if cors_val is None:
        # Use sensible defaults
        settings.cors_origins = ["http://localhost:3000", "http://localhost:8080"]
    elif isinstance(cors_val, str):
        cors_val = cors_val.strip()
        if cors_val.startswith('['):
            # JSON array string
            settings.cors_origins = json.loads(cors_val)
        elif cors_val == '':
            settings.cors_origins = []
        else:
            # Comma-separated
            settings.cors_origins = [s.strip() for s in cors_val.split(',') if s.strip()]
except Exception:
    # If normalization fails, fall back to default
    settings.cors_origins = ["http://localhost:3000", "http://localhost:8080"]
