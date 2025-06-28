#!/usr/bin/env python
"""
Complete Facebook Scraper
Combines all scraping functionality in one script:
- Posts scraping with screenshots
- Images downloading
- Smart comment detection and extraction
- Automatic handling of comment limits (50 comments if >100 available)
- Manual login support

This script is a thin wrapper around SmartFacebookScraper from facebook_scraper_smart.py
"""

import sys
import logging
import argparse
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

# Import smart scraper
from facebook_scraper_smart import SmartFacebookScraper

from db.config import LOGS_DIR, DEBUG_DIR, IMAGES_DIR
from db.models import FacebookPost, PostComment, PostImage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'facebook_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Complete Facebook Scraper')
    parser.add_argument('--pages', nargs='+', help='List of Facebook page names to scrape')
    parser.add_argument('--pages-file', type=str, default='pages.txt',
                        help='File containing list of Facebook page names (one per line)')
    parser.add_argument('--max-posts', type=int, default=10,
                        help='Maximum number of posts to scrape per page (0 = all)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no UI)')
    parser.add_argument('--no-images', action='store_true',
                        help='Do not download images')
    parser.add_argument('--no-comments', action='store_true',
                        help='Do not extract comments')
    parser.add_argument('--no-screenshots', action='store_true',
                        help='Do not take screenshots of posts')
    parser.add_argument('--wait-time', type=int, default=300,
                        help='Maximum time to wait for manual login (seconds)')
    parser.add_argument('--max-comments', type=int, default=50,
                        help='Maximum number of comments to extract per post (0 = all)')
    return parser.parse_args()

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("COMPLETE FACEBOOK SCRAPER WITH SMART COMMENT DETECTION")
    print("="*80)
    print("Features:")
    print("✓ Post scraping")
    print("✓ Image downloading")
    print("✓ Smart comment detection")
    print("✓ Comment extraction (up to 50 comments for posts with >100 comments)")
    print("✓ Post screenshots")
    print("✓ Manual login support")
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
    print(f"Max posts per page: {args.max_posts if args.max_posts > 0 else 'All'}")
    print(f"Download images: {'No' if args.no_images else 'Yes'}")
    print(f"Extract comments: {'No' if args.no_comments else 'Yes'}")
    print(f"Take screenshots: {'No' if args.no_screenshots else 'Yes'}")
    print(f"Headless mode: {'Yes' if args.headless else 'No'}")
    
    # Initialize the smart scraper
    print("\nInitializing Smart Facebook scraper...")
    scraper = SmartFacebookScraper(
        headless=args.headless,
        wait_time=args.wait_time,
        download_images=(not args.no_images),
        take_screenshots=(not args.no_screenshots),
        max_comments=args.max_comments if not args.no_comments else 0
    )
    
    try:
        # Start the browser
        if not scraper.start():
            print("Failed to start browser. Check logs for details.")
            return 1
            
        # Perform manual login - always required for new sessions
        print("\nChecking login status...")
        if not scraper.manual_login():
            print("Login failed or was canceled. Cannot proceed.")
            return 1
        
        # Process each page
        total_posts = 0
        total_images = 0
        total_comments = 0
        
        for page_name in pages_to_scrape:
            print(f"\n{'='*40}")
            print(f"SCRAPING PAGE: {page_name}")
            print(f"{'='*40}")
            
            result = scraper.smart_scrape_page(
                page_name, 
                max_posts=args.max_posts
            )
            
            if result:
                posts_data, images_count, comments_count = result
                total_posts += len(posts_data)
                total_images += images_count
                total_comments += comments_count
                print(f"\n✅ Successfully scraped {len(posts_data)} posts from {page_name}")
                print(f"   - {images_count} images downloaded")
                print(f"   - {comments_count} comments extracted")
            else:
                print(f"\n❌ Failed to scrape page: {page_name}")
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total pages scraped: {len(pages_to_scrape)}")
        print(f"Total posts scraped: {total_posts}")
        print(f"Total images downloaded: {total_images}")
        print(f"Total comments extracted: {total_comments}")
        print("="*50)
        
        if total_comments == 0 and not args.no_comments:
            print("\n⚠️ WARNING: No comments were extracted. Possible issues:")
            print("  1. Comments might be disabled or hidden on these pages/posts")
            print("  2. Facebook's layout might have changed")
            print("  3. Login session might not have proper access to comments")
            print("\nTry running the comment_fix.py script to fix any missing comments.")
        
        print("\n✅ Scraping completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        return 130
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        logger.exception("Unhandled exception during scraping:")
        return 1
        
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    sys.exit(main())