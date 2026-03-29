#!/usr/bin/env python
"""
PostgreSQL Database Setup Script for Facebook Scraper
This script sets up the PostgreSQL database structure required for the Facebook scraper.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import psycopg2
from sqlalchemy import create_engine

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

# Import project modules
from db.config import DB_CONFIG, get_database_url
from db.models import Base
from db.config import init_project_structure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_postgres_database():
    """Create the PostgreSQL database if it doesn't exist"""
    try:
        # Connect to the PostgreSQL server without specifying a database
        logger.info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["username"],
            password=DB_CONFIG["password"],
            database="postgres"  # Connect to default postgres database
        )
        conn.autocommit = True  # Needed for creating database
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["database"],))
        exists = cur.fetchone()
        
        if not exists:
            # Create database
            logger.info(f"Creating database: {DB_CONFIG['database']}...")
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']} WITH OWNER = {DB_CONFIG['username']}")
            logger.info(f"Database {DB_CONFIG['database']} created successfully")
        else:
            logger.info(f"Database {DB_CONFIG['database']} already exists")
        
        # Close connection
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating PostgreSQL database: {e}")
        print(f"Error creating PostgreSQL database: {e}")
        return False

def create_database_tables():
    """Create all database tables defined in models"""
    try:
        # Create a SQLAlchemy engine
        logger.info("Creating database tables...")
        engine = create_engine(get_database_url())
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        print(f"Error creating database tables: {e}")
        return False

def main():
    """Main function to run database setup"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='PostgreSQL Database Setup')
    parser.add_argument('--skip-db-creation', action='store_true', 
                        help='Skip database creation (use when created via pgAdmin)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose output')
    args = parser.parse_args()
    
    # Adjust logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Print banner
    print("\n" + "="*80)
    print("POSTGRESQL DATABASE SETUP")
    print("="*80)
    
    # Initialize project structure (directories)
    logger.info("Initializing project directory structure...")
    init_project_structure()
    print("✅ Project directories created")
    
    # Create database if not skipping
    if not args.skip_db_creation:
        print("\nCreating PostgreSQL database...")
        if not create_postgres_database():
            logger.error("Failed to create database")
            print("❌ Database creation failed")
            return 1
        print("✅ Database created or already exists")
    else:
        logger.info("Skipping database creation (--skip-db-creation specified)")
        print("\nSkipping database creation (using existing database)")
    
    # Create database tables
    print("\nCreating database tables...")
    if not create_database_tables():
        logger.error("Failed to create database tables")
        print("❌ Database table creation failed")
        return 1
    print("✅ Database tables created successfully")
    
    # Success message
    print("\n" + "="*80)
    print("✅ PostgreSQL database setup completed successfully!")
    print("="*80)
    print("You can now run the Facebook scraper with:")
    print("  python manual_login.py")
    print("  python facebook_scraper_all.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
