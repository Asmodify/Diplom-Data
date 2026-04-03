"""
scraper_v2 - Facebook Scraper v2.0

A robust Facebook page scraper combining the best features from
beta and Scraper0.1 projects.

Features:
- Robust browser session management with auto-recovery
- Multi-tier login (cookies, credentials, manual)
- Detailed post and comment extraction
- PostgreSQL/SQLite database storage
- Configurable settings via environment or config file
"""

__version__ = "2.0.0"
__author__ = "Diploma Project"

from config import get_config, AppConfig

__all__ = ['get_config', 'AppConfig', '__version__']
