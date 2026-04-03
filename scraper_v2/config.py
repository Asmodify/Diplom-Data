"""
Configuration Management v2.0
=============================
Comprehensive configuration combining all settings from beta and Scraper0.1.

Features:
- Dataclass-based configuration with type hints
- Environment variable loading
- fb_credentials.py integration
- Multiple database support (PostgreSQL, SQLite, Firebase)
- ML/API configuration
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from pathlib import Path

# Try to load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


def get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """Get environment variable with type casting."""
    value = os.environ.get(key, default)
    if value is None:
        return default
    if cast_type == bool:
        return str(value).lower() in ('true', '1', 'yes', 'on')
    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return default


@dataclass
class BrowserConfig:
    """Browser and Selenium configuration."""
    headless: bool = get_env('HEADLESS', False, bool)
    window_width: int = get_env('WINDOW_WIDTH', 1920, int)
    window_height: int = get_env('WINDOW_HEIGHT', 1080, int)
    page_load_timeout: int = get_env('PAGE_LOAD_TIMEOUT', 30, int)
    element_wait_timeout: int = get_env('ELEMENT_WAIT_TIMEOUT', 20, int)
    max_restart_attempts: int = get_env('MAX_RESTART_ATTEMPTS', 3, int)
    
    # Performance options
    disable_images: bool = get_env('DISABLE_IMAGES', True, bool)
    disable_javascript: bool = False
    enable_event_listener: bool = True  # For debugging
    
    # Human-like behavior
    min_typing_delay: float = 0.05
    max_typing_delay: float = 0.3
    min_click_delay: float = 0.1
    max_click_delay: float = 0.3
    
    # Random viewport (from beta)
    random_viewport: bool = True
    viewports: List[tuple] = field(default_factory=lambda: [
        (1920, 1080), (1366, 768), (1440, 900), (1536, 864)
    ])


@dataclass
class ScrapingConfig:
    """Scraping behavior configuration."""
    # Post limits
    min_posts_per_page: int = get_env('MIN_POSTS_PER_PAGE', 10, int)
    max_posts_per_page: int = get_env('MAX_POSTS_PER_PAGE', 50, int)
    max_comments_per_post: int = get_env('MAX_COMMENTS_PER_POST', 50, int)
    
    # Scrolling (from both projects)
    max_scroll_attempts: int = get_env('MAX_SCROLL_ATTEMPTS', 60, int)
    scroll_step_pixels: int = 400
    scroll_pause_min: float = 0.08
    scroll_pause_max: float = 2.0
    scroll_patience: int = 3  # Attempts before giving up
    
    # Retries
    max_page_retries: int = 3
    max_modal_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Content options
    take_screenshots: bool = get_env('TAKE_SCREENSHOTS', True, bool)
    download_images: bool = get_env('DOWNLOAD_IMAGES', True, bool)
    scrape_comments: bool = True
    save_debug_html: bool = True  # Save HTML on failures (from Scraper0.1)
    
    # Mobile fallback (from Scraper0.1)
    use_mobile_fallback: bool = True
    
    # Time limits
    max_post_age_days: int = 7
    scrape_interval_seconds: int = get_env('SCRAPE_INTERVAL', 300, int)
    page_delay_min: int = 10
    page_delay_max: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration for multiple backends."""
    # PostgreSQL
    postgres_enabled: bool = get_env('POSTGRES_ENABLED', False, bool)
    postgres_host: str = get_env('POSTGRES_HOST', 'localhost')
    postgres_port: int = get_env('POSTGRES_PORT', 5432, int)
    postgres_user: str = get_env('POSTGRES_USER', 'postgres')
    postgres_password: str = get_env('POSTGRES_PASSWORD', '')
    postgres_database: str = get_env('POSTGRES_DATABASE', 'facebook_scraper')
    
    # SQLite (fallback)
    sqlite_enabled: bool = True
    sqlite_database: str = 'data/scraper.db'
    
    # Firebase (from beta)
    firebase_enabled: bool = get_env('FIREBASE_ENABLED', False, bool)
    firebase_credentials_path: str = get_env('FIREBASE_CREDENTIALS', '')
    firebase_project_id: str = get_env('FIREBASE_PROJECT_ID', '')
    
    # Connection pool
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    # Data directories
    data_dir: str = 'data'
    exports_dir: str = 'exports'
    debug_dir: str = 'debug'


@dataclass
class AuthConfig:
    """Facebook authentication configuration."""
    email: str = ''
    password: str = ''
    cookies: Dict[str, str] = field(default_factory=dict)
    login_timeout_seconds: int = 300  # 5 minutes
    
    def __post_init__(self):
        """Load credentials from fb_credentials.py if available."""
        try:
            import fb_credentials
            if hasattr(fb_credentials, 'FB_EMAIL'):
                self.email = fb_credentials.FB_EMAIL or self.email
            if hasattr(fb_credentials, 'FB_PASSWORD'):
                self.password = fb_credentials.FB_PASSWORD or self.password
            if hasattr(fb_credentials, 'cookies'):
                self.cookies = fb_credentials.cookies or self.cookies
            if hasattr(fb_credentials, 'FB_COOKIES'):
                self.cookies = fb_credentials.FB_COOKIES or self.cookies
        except ImportError:
            pass
        
        # Also check environment variables
        self.email = get_env('FB_EMAIL', self.email)
        self.password = get_env('FB_PASSWORD', self.password)


@dataclass
class APIConfig:
    """REST API configuration (from beta)."""
    enabled: bool = get_env('API_ENABLED', True, bool)
    host: str = get_env('API_HOST', '0.0.0.0')
    port: int = get_env('API_PORT', 8000, int)
    api_token: str = get_env('FB_SCRAPER_API_TOKEN', 'dev-token-change-in-production')
    enable_auth: bool = True
    enable_cors: bool = True
    version: str = '2.0.0'
    allowed_origins: List[str] = field(default_factory=lambda: ['*'])


@dataclass
class MLConfig:
    """Machine learning configuration (from beta)."""
    enabled: bool = get_env('ML_ENABLED', True, bool)
    use_advanced_sentiment: bool = get_env('USE_ADVANCED_SENTIMENT', True, bool)
    sentiment_model: str = 'textblob'  # Options: textblob, vader, bert
    bert_model_name: str = 'nlptown/bert-base-multilingual-uncased-sentiment'
    cache_predictions: bool = True
    batch_size: int = 32


@dataclass
class IntegrationConfig:
    """External service integrations (from beta)."""
    # Google Sheets
    google_sheets_enabled: bool = get_env('GOOGLE_SHEETS_ENABLED', False, bool)
    google_credentials_path: str = get_env('GOOGLE_CREDENTIALS', '')
    spreadsheet_id: str = get_env('SPREADSHEET_ID', '')
    
    # Telegram notifications (optional)
    telegram_enabled: bool = False
    telegram_bot_token: str = ''
    telegram_chat_id: str = ''


@dataclass
class LogConfig:
    """Logging configuration."""
    level: str = get_env('LOG_LEVEL', 'INFO')
    log_to_file: bool = True
    log_file: str = 'logs/scraper.log'
    max_log_size_mb: int = 10
    backup_count: int = 5
    log_format: str = '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'


@dataclass
class AppConfig:
    """Main application configuration combining all settings."""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    api: APIConfig = field(default_factory=APIConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    logging: LogConfig = field(default_factory=LogConfig)
    
    # Project paths
    pages_file: str = 'pages.txt'
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)
    
    def get_data_path(self, *args) -> Path:
        """Get path within data directory."""
        return self.project_root / self.database.data_dir / Path(*args)
    
    def get_export_path(self, *args) -> Path:
        """Get path within exports directory."""
        return self.project_root / self.database.exports_dir / Path(*args)


# Global config instance (singleton pattern)
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


def reset_config():
    """Reset configuration (useful for testing)."""
    global _config_instance
    _config_instance = None


# Convenience exports
Config = AppConfig
