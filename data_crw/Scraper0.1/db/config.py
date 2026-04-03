from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ==================== DATABASE CONFIGURATION ====================

# Database backend selection
# Options: 'postgresql', 'sqlite', 'firebase'
DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'postgresql')

# PostgreSQL configuration
USE_SQLITE = False
DB_CONFIG = {
    "username": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "Keqing17"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "Facebook_Scraper0.1")
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

