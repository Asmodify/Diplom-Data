from typing import Dict, Optional
import os
from pathlib import Path

# ==================== DATABASE CONFIGURATION ====================

# Database backend selection
# Options: 'postgresql', 'sqlite', 'firebase'
DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'postgresql')

# PostgreSQL configuration
USE_SQLITE = False  # Set to False to use PostgreSQL
DB_CONFIG = {
    "username": os.getenv('DB_USERNAME', 'postgres'),
    "password": os.getenv('DB_PASSWORD', 'Keqing17'),
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": os.getenv('DB_PORT', '5432'),
    "database": os.getenv('DB_NAME', 'facebook_scraper_beta')
}

# ==================== FIREBASE CONFIGURATION ====================

FIREBASE_CONFIG = {
    # Path to Firebase service account credentials JSON
    "credentials_path": os.getenv('FIREBASE_CREDENTIALS', None),
    # Firestore collection names
    "posts_collection": "facebook_posts",
    "analysis_collection": "analysis_results"
}

# ==================== GOOGLE SHEETS CONFIGURATION ====================

GOOGLE_SHEETS_CONFIG = {
    # Path to Google service account credentials JSON
    "credentials_path": os.getenv('GOOGLE_SHEETS_CREDENTIALS', None),
    # Default spreadsheet name for exports
    "default_spreadsheet": "Facebook_Scraper_Data"
}

# ==================== FASTAPI CONFIGURATION ====================

API_CONFIG = {
    "host": os.getenv('API_HOST', '0.0.0.0'),
    "port": int(os.getenv('API_PORT', '8000')),
    "reload": os.getenv('API_RELOAD', 'false').lower() == 'true',
    "cors_origins": os.getenv('CORS_ORIGINS', '*').split(',')
}

# ==================== ML CONFIGURATION ====================

ML_CONFIG = {
    "models_dir": os.getenv('ML_MODELS_DIR', None),  # None = use default
    "n_topics": int(os.getenv('ML_N_TOPICS', '5')),
    "sentiment_threshold": float(os.getenv('ML_SENTIMENT_THRESHOLD', '0.1'))
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
