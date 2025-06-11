from dotenv import load_dotenv
load_dotenv()  # Load.env

import os
import yaml
import logging.config
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "My FastAPI Project"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A fullstack template with FastAPI backend"

    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Other settings
    DEBUG: bool = True

# Create a settings instance to be imported elsewhere
settings = Settings()

def setup_logging(yaml_path="logging_config.yaml"):
    os.makedirs("logs", exist_ok=True)
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)