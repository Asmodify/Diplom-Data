"""
Centralized Configuration for Facebook Scraper v2.0

This module provides all configuration settings in one place.
Settings can be overridden via environment variables or .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"


@dataclass
class BrowserConfig:
    """Browser/Selenium settings"""
    headless: bool = False
    window_width: int = 1366
    window_height: int = 768
    page_load_timeout: int = 30
    element_wait_timeout: int = 20
    max_restart_attempts: int = 3
    
    # Anti-detection settings
    disable_images: bool = False  # Set True for faster scraping
    disable_javascript: bool = False
    
    # Human-like behavior
    min_typing_delay: float = 0.05
    max_typing_delay: float = 0.2
    min_click_delay: float = 0.1
    max_click_delay: float = 0.3


@dataclass  
class ScrapingConfig:
    """Scraping behavior settings"""
    max_posts_per_page: int = 50
    max_comments_per_post: int = 100
    max_scroll_attempts: int = 60
    scroll_step_pixels: int = 400
    scroll_pause_seconds: float = 0.5
    
    # Retry settings
    max_page_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Content settings
    take_screenshots: bool = True
    download_images: bool = True
    scrape_comments: bool = True
    
    # Date filter (only scrape posts from last N days, 0 = no limit)
    max_post_age_days: int = 7


@dataclass
class DatabaseConfig:
    """Database connection settings"""
    use_sqlite: bool = False
    
    # PostgreSQL settings (from environment or defaults)
    pg_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    pg_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    pg_database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "facebook_data"))
    pg_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    pg_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    
    # SQLite settings (fallback)
    sqlite_path: str = "data/facebook_data.db"
    
    # Connection pool
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    @property
    def connection_url(self) -> str:
        if self.use_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"


@dataclass
class AuthConfig:
    """Facebook authentication settings"""
    email: str = field(default_factory=lambda: os.getenv("FB_EMAIL", ""))
    password: str = field(default_factory=lambda: os.getenv("FB_PASSWORD", ""))
    
    # Cookie-based auth (preferred)
    cookies: Dict[str, str] = field(default_factory=dict)
    
    # Login strategy: "cookies" -> "credentials" -> "manual"
    login_timeout_seconds: int = 300  # 5 minutes for manual login
    
    @classmethod
    def load_from_file(cls, filepath: str = "fb_credentials.py") -> "AuthConfig":
        """Load auth config from fb_credentials.py file"""
        config = cls()
        creds_path = BASE_DIR / filepath
        
        if creds_path.exists():
            try:
                # Read and execute the credentials file
                with open(creds_path, 'r') as f:
                    creds_content = f.read()
                
                local_vars = {}
                exec(creds_content, {}, local_vars)
                
                config.email = local_vars.get('FB_EMAIL', config.email)
                config.password = local_vars.get('FB_PASSWORD', config.password)
                config.cookies = local_vars.get('cookies', {})
                
            except Exception as e:
                print(f"Warning: Could not load credentials from {filepath}: {e}")
        
        return config


@dataclass
class APIConfig:
    """API server settings"""
    host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    api_token: str = field(default_factory=lambda: os.getenv("API_TOKEN", ""))
    enable_auth: bool = True
    enable_cors: bool = True
    version: str = "2.0.0"


@dataclass
class LogConfig:
    """Logging settings"""
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_to_file: bool = True
    log_file: str = "scraper.log"
    max_log_size_mb: int = 10
    backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class Config:
    """Main configuration container"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=lambda: AuthConfig.load_from_file())
    api: APIConfig = field(default_factory=APIConfig)
    logging: LogConfig = field(default_factory=LogConfig)
    
    # Pages to scrape
    pages_file: str = "pages.txt"
    
    def get_pages(self) -> List[str]:
        """Load pages from pages file"""
        pages_path = BASE_DIR / self.pages_file
        if not pages_path.exists():
            return []
        
        with open(pages_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    @classmethod
    def from_args(cls, args) -> "Config":
        """Create config from argparse args"""
        config = cls()
        
        if hasattr(args, 'headless') and args.headless:
            config.browser.headless = True
        if hasattr(args, 'max_posts'):
            config.scraping.max_posts_per_page = args.max_posts
        if hasattr(args, 'no_screenshots') and args.no_screenshots:
            config.scraping.take_screenshots = False
        if hasattr(args, 'no_images') and args.no_images:
            config.scraping.download_images = False
        if hasattr(args, 'debug') and args.debug:
            config.logging.level = "DEBUG"
        
        return config


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config):
    """Set the global config instance"""
    global _config
    _config = config
