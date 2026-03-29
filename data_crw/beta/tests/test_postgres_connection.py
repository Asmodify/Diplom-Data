#!/usr/bin/env python
"""
Test PostgreSQL Connection for Facebook Scraper
This script tests if the PostgreSQL connection is correctly set up.
"""

import sys
import unittest
import logging
from pathlib import Path
import psycopg2
from sqlalchemy import text

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Import project modules
from db.database import DatabaseManager
from db.config import DB_CONFIG, get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestPostgresConnection(unittest.TestCase):
    """Test PostgreSQL connection and database setup"""
    
    def setUp(self):
        """Set up test case"""
        self.db = DatabaseManager()
        
    def test_server_connection(self):
        """Test basic connection to PostgreSQL server"""
        logger.info("Testing PostgreSQL server connection...")
        
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["username"],
                password=DB_CONFIG["password"]
            )
            conn.close()
            logger.info("Successfully connected to PostgreSQL server")
            self.assertTrue(True)  # If we get here, connection succeeded
        except Exception as e:
            self.fail(f"Failed to connect to PostgreSQL server: {e}")
    
    def test_database_connection(self):
        """Test connection to specific database"""
        logger.info(f"Testing connection to database '{DB_CONFIG['database']}'...")
        
        self.assertTrue(
            self.db.health_check(),
            "Failed to connect to database. Database may not exist."
        )
    
    def test_required_tables(self):
        """Test that all required tables exist"""
        required_tables = ['facebook_posts', 'post_images', 'post_comments']
        missing_tables = []
        
        try:
            with self.db.session_scope() as session:
                for table in required_tables:
                    sql = text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                    result = session.execute(sql).scalar()
                    if not result:
                        missing_tables.append(table)
            
            self.assertEqual(
                len(missing_tables), 0,
                f"Missing required tables: {', '.join(missing_tables)}"
            )
        except Exception as e:
            self.fail(f"Error checking required tables: {e}")
    
    def tearDown(self):
        """Clean up after test case"""
        if hasattr(self, 'db'):
            del self.db

if __name__ == '__main__':
    unittest.main(verbosity=2)
