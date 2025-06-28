#!/usr/bin/env python
"""
Facebook Scraper - Command Line Interface
"""

import sys
import logging
import argparse
import time
import os
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.config import LOGS_DIR
# Import SmartFacebookScraper via the facebook_scraper_all module
from facebook_scraper_smart import SmartFacebookScraper
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
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no UI)')
    parser.add_argument('--wait-time', type=int, default=300,
                        help='Maximum time to wait for manual login (seconds)')
    parser.add_argument('--no-images', action='store_true',
                        help='Do not download images')
    parser.add_argument('--screenshots', action='store_true',
                        help='Take screenshots of posts')
    parser.add_argument('--comment-limit', type=int, default=0,
                        help='Maximum number of comments to scrape (0 = all)')
    return parser.parse_args()

def read_pages_from_file(file_path):
    """Read list of pages from a text file"""
    pages = []
    try:
        pages_file = Path(file_path)
        if not pages_file.exists():
            logger.error(f"Pages file not found: {file_path}")
            print(f"Error: Pages file not found: {file_path}")
            return []
            
        with open(pages_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip whitespace and skip empty lines or comments
                line = line.strip()
                if line and not line.startswith('#'):
                    pages.append(line)
        
        if not pages:
            logger.warning(f"No page names found in {file_path}")
            print(f"Warning: No page names found in {file_path}")
        
        return pages
        
    except Exception as e:
        logger.error(f"Error reading pages file: {e}")
        print(f"Error reading pages file: {e}")
        return []

def main():
    """Main execution function"""
    # Parse command line arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("FACEBOOK SCRAPER - COMMAND LINE INTERFACE")
    print("="*80 + "\n")
    
    # Determine pages to scrape
    pages_to_scrape = []
    
    if args.pages:
        pages_to_scrape = args.pages
    else:
        pages_to_scrape = read_pages_from_file(args.pages_file)
    
    if not pages_to_scrape:
        print("No pages to scrape. Please provide page names using --pages or --pages-file.")
        return 1
    
    print(f"Will scrape {len(pages_to_scrape)} pages: {', '.join(pages_to_scrape)}")
    
    # Manual login mode
    if args.manual:
        print("\nMANUAL LOGIN MODE")
        print("-----------------")
        print("A browser will open for you to log in to Facebook.")
        print("Please log in and then return to this terminal.")
        print("After login, we'll verify access to Facebook.")
        
        # Use verify_access to check existing login
        print("\nChecking Facebook access...")
        access_verified = verify_facebook_access()
        
        if access_verified:
            print("\nFacebook access already verified. Proceeding to scrape.")
        else:
            print("\nNeed to log in to Facebook. Opening browser...")
            print("When you're done logging in, type 'done' and press Enter.")
            
            # Initialize scraper just for login purposes
            temp_scraper = SmartFacebookScraper(headless=False, wait_time=args.wait_time)
            login_result = temp_scraper.manual_login()
            temp_scraper.close()
            
            if not login_result:
                print("Manual login failed or was canceled.")
                return 1
    
    # Initialize scraper
    print("\nInitializing Facebook scraper...")
    scraper = SmartFacebookScraper(
        headless=args.headless,
        wait_time=args.wait_time,
        download_images=(not args.no_images),
        take_screenshots=args.screenshots,
        use_cookies=(not args.no_cookies),
        comment_limit=args.comment_limit
    )
    
    try:
        # Scrape each page
        total_posts = 0
        total_images = 0
        total_comments = 0
        
        for page_name in pages_to_scrape:
            print(f"\nScraping page: {page_name}")
            print("-" * 50)
            
            result = scraper.scrape_page(
                page_name=page_name,
                max_posts=args.max_posts
            )
            
            if result:
                posts, images, comments = result
                total_posts += len(posts)
                total_images += images
                total_comments += comments
                
                print(f"✅ Successfully scraped {len(posts)} posts, {images} images, and {comments} comments from {page_name}")
            else:
                print(f"❌ Failed to scrape page: {page_name}")
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Pages scraped: {len(pages_to_scrape)}")
        print(f"Total posts: {total_posts}")
        print(f"Total images: {total_images}")
        print(f"Total comments: {total_comments}")
        print("="*50)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error in scraper: {e}")
        print(f"\nError: {e}")
        return 1
        
    finally:
        # Make sure to close the scraper
        if scraper:
            scraper.close()

if __name__ == "__main__":
    sys.exit(main())
