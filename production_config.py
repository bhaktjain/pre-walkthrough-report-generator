"""
Production configuration for Pre-Walkthrough Report Generator
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class ProductionConfig(BaseSettings):
    """Production configuration settings"""
    
    # API Keys (Required)
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    rapidapi_key: str = Field(..., env="RAPIDAPI_KEY")
    serpapi_key: Optional[str] = Field(None, env="SERPAPI_KEY")
    
    # Server Settings
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(1, env="WORKERS")
    reload: bool = Field(False, env="RELOAD")
    
    # File Upload Settings
    max_file_size: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: list = Field([".txt", ".docx", ".pdf"], env="ALLOWED_FILE_TYPES")
    
    # Request Settings
    request_timeout: int = Field(300, env="REQUEST_TIMEOUT")  # 5 minutes
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    enable_file_logging: bool = Field(True, env="ENABLE_FILE_LOGGING")
    log_file_path: str = Field("logs/app.log", env="LOG_FILE_PATH")
    
    # Security
    enable_cors: bool = Field(True, env="ENABLE_CORS")
    cors_origins: list = Field(["*"], env="CORS_ORIGINS")
    api_key_header: Optional[str] = Field(None, env="API_KEY_HEADER")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # Monitoring
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    # Storage
    temp_dir: str = Field("/tmp", env="TEMP_DIR")
    output_dir: str = Field("data", env="OUTPUT_DIR")
    
    # External Services
    openai_base_url: Optional[str] = Field(None, env="OPENAI_BASE_URL")
    rapidapi_base_url: str = Field("https://realtor.p.rapidapi.com", env="RAPIDAPI_BASE_URL")
    
    # Feature Flags
    enable_property_search: bool = Field(True, env="ENABLE_PROPERTY_SEARCH")
    enable_image_download: bool = Field(True, env="ENABLE_IMAGE_DOWNLOAD")
    enable_floor_plans: bool = Field(True, env="ENABLE_FLOOR_PLANS")
    
    # Performance
    cache_ttl: int = Field(3600, env="CACHE_TTL")  # 1 hour
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: int = Field(1, env="RETRY_DELAY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_production_config() -> ProductionConfig:
    """Get production configuration"""
    return ProductionConfig()


# Environment-specific configurations
class DevelopmentConfig(ProductionConfig):
    """Development configuration with relaxed settings"""
    reload: bool = True
    log_level: str = "DEBUG"
    enable_cors: bool = True
    cors_origins: list = ["*"]
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    request_timeout: int = 600  # 10 minutes


class TestingConfig(ProductionConfig):
    """Testing configuration"""
    log_level: str = "DEBUG"
    enable_file_logging: bool = False
    enable_metrics: bool = False
    temp_dir: str = "/tmp/test"
    output_dir: str = "test_data"


def get_config(environment: str = None) -> ProductionConfig:
    """Get configuration based on environment"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "production")
    
    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig
    }
    
    return config_map.get(environment, ProductionConfig)() 