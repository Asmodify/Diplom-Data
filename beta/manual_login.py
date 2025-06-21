#!/usr/bin/env python
"""
Facebook Scraper - Manual Login Helper
This script runs the Facebook scraper in manual login mode, which opens a browser window 
and allows you to log in manually before scraping begins.
"""

import sys
import logging
import argparse
import time
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.config import LOGS_DIR, DEBUG_DIR
from facebook_scraper import ManualLoginFacebookScraper as FacebookScraper
from verify_access import verify_facebook_access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'manual_login.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Manual Login Facebook Scraper')
    parser.add_argument('--pages', nargs='+', help='List of Facebook page names to scrape')
    parser.add_argument('--pages-file', type=str, default='pages.txt',
                       help='File containing list of Facebook page names (one per line)')
    parser.add_argument('--max-posts', type=int, default=5,
                       help='Maximum number of posts to scrape per page')
    parser.add_argument('--wait-time', type=int, default=300,
                       help='Maximum time to wait for manual login (seconds)')
    return parser.parse_args()

def read_pages_from_file(file_path):
    """Read list of pages from file"""
    try:
        pages_path = Path(file_path)
        if not pages_path.is_absolute():
            pages_path = ROOT_DIR / file_path
            
        with open(pages_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading pages file: {e}")
        return []

def print_guide():
    """Print manual login guide"""
    guide = """
==========================================
MANUAL LOGIN MODE - INSTRUCTIONS
==========================================
1. A browser window will open to Facebook
2. Log in with your Facebook credentials
3. If prompted for security checks, complete them
4. After login is successful, RETURN TO THIS WINDOW
5. The scraping will begin automatically once login is detected
6. Or type 'done' and press Enter when logged in manually

Note: The browser will remain open during scraping
==========================================
"""
    print(guide)

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Ensure directories exist
    LOGS_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    
    # Get pages to scrape
    pages = args.pages
    if not pages:
        pages = read_pages_from_file(args.pages_file)
    
    if not pages:
        logger.error("No pages specified for scraping!")
        print("ERROR: No pages specified for scraping! Please add page names to pages.txt")
        return 1
    
    # Print the guide
    print_guide()
      # Initialize scraper with manual login
    scraper = FacebookScraper(headless=False)
    logger.info("Running Facebook scraper with manual login...")
    
    try:        # Run the scraper with manual login
        success = scraper.run(
            pages=pages, 
            max_posts_per_page=args.max_posts, 
            wait_time=args.wait_time
        )
        
        if success:
            logger.info("✅ Scraping completed successfully")
            print("\n✅ Scraping completed successfully!")
        else:
            logger.error("❌ Scraping failed")
            print("\n❌ Scraping failed!")
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        print(f"\nError: {e}")
        return 1
    
    finally:
        if scraper:
            scraper.close()
            logger.info("Browser closed")

if __name__ == "__main__":
    sys.exit(main())
