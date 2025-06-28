#!/usr/bin/env python
"""
Remove duplicate comments, post images, and screenshots from the database
"""
from pathlib import Path
import logging

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
import sys
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'duplicates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run duplicate removal process"""
    try:
        print("Checking for and removing duplicates...")
        db = DatabaseManager()
        
        # Remove duplicates
        stats = db.remove_duplicates()
        
        # Print results
        print("\nDuplicate Removal Results:")
        print("=========================")
        print(f"Comments removed:    {stats['comments']}")
        print(f"Post images removed: {stats['images']}")
        print(f"Screenshots removed: {stats['screenshots']}")
        print(f"Total items removed: {sum(stats.values())}")
        print("\nDone! All duplicates have been removed.")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Error in duplicate removal script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
