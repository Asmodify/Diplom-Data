from typing import Dict, Optional
import os
from pathlib import Path

# Database configuration - Using PostgreSQL for better performance and features
USE_SQLITE = False  # Set to False to use PostgreSQL
DB_CONFIG = {
    "username": "postgres",
    "password": "Keqing17",
    "host": "localhost",
    "port": "5432",
    "database": "facebook_scraper_beta"
}

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_ROOT / "images"
LOGS_DIR = PROJECT_ROOT / "logs"
DEBUG_DIR = PROJECT_ROOT / "debug"
EXPORTS_DIR = PROJECT_ROOT / "exports"
SQLITE_DB_PATH = PROJECT_ROOT / "facebook_scraper.db"

def get_database_url() -> str:
    """Generate SQLAlchemy database URL from config"""
    if USE_SQLITE:
        return f"sqlite:///{SQLITE_DB_PATH}"
    else:
        return (
            f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )

def get_image_path(page_name: str) -> Path:
    """Get the image directory path for a specific page"""
    page_dir = IMAGES_DIR / page_name
    page_dir.mkdir(parents=True, exist_ok=True)
    return page_dir

def init_project_structure() -> None:
    """Initialize project directory structure"""
    # Create required directories
    IMAGES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    EXPORTS_DIR.mkdir(exist_ok=True)

def validate_config() -> bool:
    """Validate database configuration"""
    required_keys = ['username', 'password', 'host', 'port', 'database']
    return all(key in DB_CONFIG and DB_CONFIG[key] for key in required_keys)

def get_env_config() -> Dict[str, str]:
    """Get configuration from environment variables if available"""
    env_config = {}
    for key in DB_CONFIG:
        env_var = f"FB_SCRAPER_DB_{key.upper()}"
        if os.getenv(env_var):
            env_config[key] = os.getenv(env_var)
    return env_config

# Initialize project structure on import
init_project_structure()

# Update config with environment variables if available
DB_CONFIG.update(get_env_config())

# Validate configuration
if not validate_config():
    raise ValueError(
        "Invalid database configuration. Please check DB_CONFIG values "
        "or set environment variables."
    )
