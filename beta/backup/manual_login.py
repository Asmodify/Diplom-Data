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
from facebook_scraper_smart import SmartFacebookScraper
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
    parser.add_argument('--no-scrape', action='store_true',
                       help='Only perform login without scraping')
    parser.add_argument('--no-images', action='store_true',
                       help='Do not download images')
    parser.add_argument('--screenshots', action='store_true',
                       help='Take screenshots of posts')
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

def print_guide():
    """Print manual login guide"""
    print("\n" + "="*80)
    print("FACEBOOK MANUAL LOGIN GUIDE")
    print("="*80)
    print("This tool will:") 
    print("1. Open a Firefox browser window to Facebook")
    print("2. Wait for you to log in manually")
    print("3. Detect when you've successfully logged in")
    print("4. Either proceed to scrape or save your login state")
    print("\nIMPORTANT TIPS:")
    print("- Facebook may ask for additional verification like phone/email")
    print("- Complete all verification steps in the browser")
    print("- Stay on Facebook until the terminal confirms login detected")
    print("- You can type 'done' after logging in to continue")
    print("="*80 + "\n")

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Ensure directories exist
    LOGS_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    
    # Print guide
    print_guide()
    
    # Initialize scraper for login
    print("\nInitializing Facebook login process...")
    scraper = SmartFacebookScraper(
        headless=False,  # Never use headless for manual login
        wait_time=args.wait_time,
        download_images=(not args.no_images),
        take_screenshots=args.screenshots
    )
    
    try:
        # Perform manual login
        print("\nOpening browser for manual login...")
        if not scraper.manual_login():
            logger.error("Manual login failed or timed out")
            print("\n❌ Manual login failed or timed out!")
            return 1
            
        print("\n✅ Successfully logged in to Facebook!")
        
        # If we're just doing login without scraping
        if args.no_scrape:
            print("\nLogin completed successfully. No scraping requested.")
            return 0
            
        # Determine pages to scrape
        pages_to_scrape = []
        if args.pages:
            pages_to_scrape = args.pages
        else:
            pages_to_scrape = read_pages_from_file(args.pages_file)
            
        if not pages_to_scrape:
            print("No pages to scrape. Please provide page names using --pages or --pages-file.")
            return 1
            
        print(f"\nScraping {len(pages_to_scrape)} pages: {', '.join(pages_to_scrape)}")
        
        # Process each page
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
        if not args.no_scrape:
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
        logger.error(f"Error: {e}")
        print(f"\nError: {e}")
        return 1
        
    finally:
        # Make sure to close the scraper
        if scraper:
            scraper.close()

if __name__ == "__main__":
    sys.exit(main())
