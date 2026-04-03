#!/usr/bin/env python
"""
Initialize database and project structure for Facebook scraper
"""

import sys
import os
import logging
import argparse
import re
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import Base
from db.config import LOGS_DIR, IMAGES_DIR, DEBUG_DIR, EXPORTS_DIR

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

def sanitize_directory_name(name):
    """Convert a page name/ID to a valid directory name"""
    # Replace any non-alphanumeric characters (except -_) with underscore
    sanitized = re.sub(r'[^\w\-]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized

def create_directories():
    """Create necessary project directories"""
    try:
        # Create base directories
        LOGS_DIR.mkdir(exist_ok=True)
        IMAGES_DIR.mkdir(exist_ok=True)
        DEBUG_DIR.mkdir(exist_ok=True)
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        logger.info("Base directories created")
        print("✅ Created base directories")
        
        # Read pages from pages.txt
        pages_file = ROOT_DIR / "pages.txt"
        if pages_file.exists():
            with open(pages_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Strip whitespace and skip empty lines or comments
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Sanitize the page name for directory creation
                        safe_name = sanitize_directory_name(line)
                        try:
                            # Create directories for each page
                            (IMAGES_DIR / safe_name).mkdir(exist_ok=True)
                            (DEBUG_DIR / safe_name).mkdir(exist_ok=True)
                            logger.info(f"Created directories for page: {line} (as {safe_name})")
                        except Exception as e:
                            logger.warning(f"Could not create directories for page {line}: {e}")
                            continue
        
        logger.info("Directory structure created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        print(f"Error creating directories: {e}")
        return False

def init_database():
    """Initialize database tables"""
    try:
        db = DatabaseManager()
        
        # Check database connection
        if not db.health_check():
            logger.error("Database connection failed")
            print("Error: Database connection failed. Please check your configuration.")
            print("Make sure PostgreSQL is running and the database exists.")
            return False
            
        # Create tables
        db.init_db()
        
        logger.info("Database initialized successfully")
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        print(f"Error initializing database: {e}")
        print("If using PostgreSQL, make sure it's running and properly configured.")
        print("Check db/config.py for database connection settings.")
        return False

def main():
    """Main initialization function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Initialize Facebook Scraper project')
    parser.add_argument('--skip-db', action='store_true', 
                        help='Skip database initialization')
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("FACEBOOK SCRAPER - PROJECT INITIALIZATION")
    print("="*80 + "\n")
    
    logger.info("Starting project initialization...")
    
    # Create directory structure
    print("Creating project directory structure...")
    if not create_directories():
        logger.error("Failed to create directory structure")
        return 1
        
    # Initialize database
    if not args.skip_db:
        print("\nInitializing database...")
        if not init_database():
            logger.error("Failed to initialize database")
            return 1
    else:
        logger.info("Database initialization skipped")
        print("Database initialization skipped")
        
    logger.info("✅ Project initialization completed successfully")
    print("\n✅ Project initialization completed successfully!")
    print("\nYou can now run:")
    print("  - manual_login.py    - To log in to Facebook manually")
    print("  - scraper_cli.py     - To run the scraper with various options")
    print("  - view_comments.py   - To browse, search and export comments")
    return 0

if __name__ == "__main__":
    sys.exit(main())
