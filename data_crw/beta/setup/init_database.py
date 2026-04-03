#!/usr/bin/env python
"""
Initialize PostgreSQL database for Facebook scraper
"""
import logging
from pathlib import Path
import sys

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import Base
from db.config import DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database schema"""
    try:
        logger.info("Initializing database...")
        
        # Create database manager
        db = DatabaseManager()
        
        # Create all tables
        Base.metadata.create_all(db.engine)
        
        logger.info("Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

def verify_database():
    """Verify database connection and schema"""
    try:
        logger.info("Verifying database connection...")
        
        # Test connection
        db = DatabaseManager()
        conn = db.engine.connect()
        conn.close()
        
        logger.info("Database connection successful!")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    if init_database() and verify_database():
        print("\nDatabase setup completed successfully!")
        print(f"\nConnection details:")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"Username: {DB_CONFIG['username']}")
    else:
        print("\nDatabase setup failed. Check the logs for details.")
