from dotenv import load_dotenv
load_dotenv()  # Load .env

import os
import yaml
import logging.config
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Backend API Docs"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Backend API Docs"

    # Basic settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SSL_ENABLE: bool = False

    # Database settings
    DATABASE_URL: str
    DATABASE_URL_TEST: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_CONNECT_TIMEOUT: int = 60
    DB_READ_TIMEOUT: int = 30
    DB_WRITE_TIMEOUT: int = 30

    # Redis settings
    REDIS_URL: str

    # CORS settings
    HOSTNAME: str
    BACKEND_PORT: str
    FRONTEND_PORT: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    # Session settings
    SESSION_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Cookie settings
    COOKIE_SECURE: bool = SSL_ENABLE
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"  # "strict", "lax", "none"

    # Security settings
    PASSWORD_MIN_LENGTH: int = 6
    FAIL_LIMIT: int = 5
    FAIL_WINDOW_SECONDS: int = 300  # 5 minutes
    BLOCK_TIME_SECONDS: int = 900  # 15 minutes

# Create a settings instance to be imported elsewhere
settings = Settings()

def setup_logging(yaml_path="logging_config.yaml"):
    os.makedirs("logs", exist_ok=True)
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    # Override the root logger or specified logger's level with LOG_LEVEL from environment
    log_level = settings.LOG_LEVEL
    if "root" in config:
        config["root"]["level"] = log_level
    # If there are multiple loggers, override their levels as well
    if "loggers" in config:
        for logger in config["loggers"].values():
            logger["level"] = log_level
    logging.config.dictConfig(config)