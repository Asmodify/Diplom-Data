#!/usr/bin/env python
"""
Initialize database and project structure for Facebook scraper
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import Base
from db.config import LOGS_DIR, IMAGES_DIR, DEBUG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary project directories"""
    try:
        # Create base directories
        LOGS_DIR.mkdir(exist_ok=True)
        IMAGES_DIR.mkdir(exist_ok=True)
        DEBUG_DIR.mkdir(exist_ok=True)
        
        # Read pages from pages.txt
        pages_file = ROOT_DIR / 'pages.txt'
        pages = []
        if pages_file.exists():
            with open(pages_file, 'r', encoding='utf-8') as f:
                pages = [line.strip() for line in f if line.strip()]
                
        # Create image directories for each page
        for page in pages:
            page_dir = IMAGES_DIR / page
            page_dir.mkdir(exist_ok=True)
            logger.info(f"Created directory for page: {page}")

        logger.info(f"Directory structure created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def init_database():
    """Initialize database tables"""
    try:
        db = DatabaseManager()
        db.init_db()
        
        # Test database connection
        if db.health_check():
            logger.info("✅ Database initialized and connection verified")
            return True
        else:
            logger.error("Database initialized but connection test failed")
            return False
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def main():
    """Main initialization function"""
    logger.info("Starting project initialization...")
    
    # Create directory structure
    if not create_directories():
        logger.error("Failed to create directory structure")
        return 1
        
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        return 1
        
    logger.info("✅ Project initialization completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
