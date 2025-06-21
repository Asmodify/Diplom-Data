#!/usr/bin/env python
"""
Facebook Scraper - Command Line Interface
"""

import sys
import logging
import argparse
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.config import LOGS_DIR
from facebook_scraper import ManualLoginFacebookScraper as FacebookScraper
from verify_access import verify_facebook_access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Facebook Scraper')
    parser.add_argument('--pages', nargs='+', help='List of Facebook page names to scrape')
    parser.add_argument('--pages-file', type=str, default='pages.txt',
                        help='File containing list of Facebook page names (one per line)')
    parser.add_argument('--max-posts', type=int, default=5,
                        help='Maximum number of posts to scrape per page')
    parser.add_argument('--no-cookies', action='store_true',
                        help='Do not use saved cookies for login')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify Facebook access without scraping')
    parser.add_argument('--manual', action='store_true', default=True,
                        help='Use manual login mode (default)')
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

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Get pages to scrape
    pages = args.pages
    if not pages:
        pages = read_pages_from_file(args.pages_file)
    
    if not pages and not args.verify_only:
        logger.error("No pages specified for scraping!")
        return 1
    
    # Import cookies if needed
    cookies = None
    if not args.no_cookies:
        try:
            from fb_credentials import cookies
            logger.info("Using saved cookies for login")
        except ImportError:
            logger.warning("Could not import cookies from fb_credentials.py")      # Initialize scraper with manual login
    scraper = FacebookScraper(headless=False)
    logger.info("Running Facebook scraper with manual login")
    
    try:
        # If verify only, just check the login
        if args.verify_only:
            logger.info("Verifying Facebook access...")
            success = verify_facebook_access()
            if success:
                logger.info("✅ Facebook access verified successfully")
            else:
                logger.error("❌ Facebook access verification failed")
            return 0 if success else 1
          # Run the scraper with manual login
        success = scraper.run(pages=pages, max_posts_per_page=args.max_posts, wait_time=300)
        if success:
            logger.info("✅ Scraping completed successfully")
        else:
            logger.error("❌ Scraping failed")
        
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        return 1
    finally:
        scraper.close()

if __name__ == "__main__":
    sys.exit(main())
