from dotenv import load_dotenv
load_dotenv()  # Load .env

import os
import re
import yaml
import logging.config
from pydantic_settings import BaseSettings

# Docs / health probes — skip logging, rate limit, and tracing.
# Not an env setting: these paths are part of the app, not deployment.
SKIP_PATHS: frozenset[str] = frozenset(
    {"/", "/docs", "/redoc", "/openapi.json", "/healthz"}
)
# CORS preflight — skip logging, rate limit, and tracing (URL exclude cannot filter method).
SKIP_METHODS: frozenset[str] = frozenset({"OPTIONS"})


def otel_excluded_urls(paths: frozenset[str] = SKIP_PATHS) -> str:
    """Regexes matched with search() against the full URL (e.g. http://host:5000/healthz).

    Anchored path-only patterns like ^/healthz$ never match, so Docker healthchecks
    would still create server spans and show up in p95.
    """
    patterns: list[str] = []
    for path in sorted(paths):
        if path == "/":
            patterns.append(r"https?://[^/?]+/?$")
        else:
            patterns.append(re.escape(path))
    return ",".join(patterns)

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Backend API Docs"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Backend API Docs"

    # Basic settings
    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_HTTP_BODY: bool = False
    LOG_HTTP_BODY_MAX_BYTES: int = 8192
    SSL_ENABLE: bool = False

    # OpenTelemetry settings
    OTEL_ENABLE: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://alloy:4318"

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
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    PASSWORD_RESET_EMAIL_COOLDOWN_SECONDS: int = 60  # 1 minute

    # Email verification settings
    EMAIL_VERIFICATION_ENABLE: bool = False
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    EMAIL_VERIFICATION_COOLDOWN_SECONDS: int = 60  # 1 minute

    # Session settings
    SESSION_EXPIRE_MINUTES: int = 10080  # 7 days
    CSRF_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cookie settings
    COOKIE_SECURE: bool = SSL_ENABLE
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"  # "strict", "lax", "none"

    # Security settings
    PASSWORD_MIN_LENGTH: int = 6
    RATE_LIMIT: int = 200
    RATE_LIMIT_WINDOW_SECONDS: int = 300  # 5 minutes
    BLOCK_TIME_SECONDS: int = 600  # 10 minutes
    RATE_LIMIT_WHITELIST: str = ""

    @property
    def rate_limit_whitelist_ips(self) -> set[str]:
        raw = (self.RATE_LIMIT_WHITELIST or "").strip()
        if not raw:
            return set()
        return {ip.strip() for ip in raw.split(",") if ip.strip()}

    # Registration settings
    REGISTRATION_ENABLE: bool = True

    # SMTP setting
    SMTP_ENABLE: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Docker Fullstack Template"
    SMTP_ENCRYPTION: str = "tls"

    # Default admin user settings
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_FIRST_NAME: str = "Admin"
    DEFAULT_ADMIN_LAST_NAME: str = "User"
    DEFAULT_ADMIN_PHONE: str = "0000000000"
    # System role with full access bypass (not editable via roles UI/API)
    DEFAULT_SUPER_ADMIN_ROLE: str = "super-admin"
    DEFAULT_SUPER_ADMIN_LEVEL: int = 100
    DEFAULT_USER_ROLE_LEVEL: int = 1
    # Custom roles created via API must stay below the system super-admin level
    MAX_CUSTOM_ROLE_LEVEL: int = 99
    # When false, users with the system super-admin role are hidden from user list for everyone
    SHOW_SUPER_ADMIN: bool = False

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