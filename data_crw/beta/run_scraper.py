"""
Main script to run the Facebook AutoScraper with configurable options.
"""

import logging
import argparse
import sys
from pathlib import Path
from automation.auto_scraper import AutoScraper
from fb_credentials import FB_EMAIL, FB_PASSWORD

# Configure logging with rotating file handler
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging with both file and console output"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            RotatingFileHandler(
                logs_dir / 'facebook_scraper.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()  # Console output
        ]
    )

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Facebook Page Scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--max-posts', type=int, default=100, help='Maximum posts to scrape per page')
    parser.add_argument('--no-screenshots', action='store_true', help='Disable screenshot capture')
    parser.add_argument('--no-images', action='store_true', help='Disable image downloads')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()

def ensure_directories(logger):
    """Ensure all required directories exist"""
    base_dir = Path(__file__).parent
    required_dirs = ['logs', 'images', 'screenshots', 'exports', 'debug']
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")

def main():
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Ensure directories exist
        ensure_directories(logger)
        
        print("\n" + "="*80)
        print(" "*30 + "FACEBOOK SCRAPER")
        print("="*80)
        print("Settings:")
        print(f"- Headless mode: {'Yes' if args.headless else 'No'}")
        print(f"- Max posts per page: {args.max_posts}")
        print(f"- Taking screenshots: {'No' if args.no_screenshots else 'Yes'}")
        print(f"- Downloading images: {'No' if args.no_images else 'Yes'}")
        print(f"- Debug mode: {'Yes' if args.debug else 'No'}")
        print("="*80 + "\n")
        
        # Initialize scraper with command line settings
        logger.info("Initializing Facebook scraper...")
        scraper = AutoScraper(
            headless=args.headless,
            max_posts=args.max_posts,
            take_screenshots=not args.no_screenshots,
            download_images=not args.no_images
        )
        
        # Read pages to scrape
        pages_file = Path(__file__).parent / 'pages.txt'
        try:
            with open(pages_file, 'r', encoding='utf-8') as f:
                pages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            logger.error(f"Pages file not found: {pages_file}")
            print(f"\nError: Pages file not found at {pages_file}")
            print("Please create this file with one Facebook page URL or ID per line.")
            return
        except Exception as e:
            logger.error(f"Error reading pages file: {e}")
            print(f"\nError reading pages file: {e}")
            return

        if not pages:
            logger.error("No pages found to scrape")
            print("\nError: No pages found to scrape in pages.txt")
            print("Please add at least one Facebook page URL or ID to the file.")
            return

        print(f"\nFound {len(pages)} pages to scrape:")
        for i, page in enumerate(pages, 1):
            print(f"{i}. {page}")
        print()

        # Initialize success counter
        successful_pages = 0
        
        # Start scraping
        for i, page in enumerate(pages, 1):
            print(f"\nProcessing page {i}/{len(pages)}: {page}")
            print("-" * 40)
            
            try:
                logger.info(f"Scraping page: {page}")
                if scraper.scrape_page(page):
                    successful_pages += 1
                    print(f"✓ Successfully scraped: {page}")
                else:
                    print(f"× Failed to scrape: {page}")
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                print(f"× Error scraping {page}: {str(e)}")
                continue
                
        # Print summary
        print("\n" + "="*40)
        print("SCRAPING SUMMARY")
        print("="*40)
        print(f"Total pages processed: {len(pages)}")
        print(f"Successfully scraped: {successful_pages}")
        print(f"Failed: {len(pages) - successful_pages}")
        print("="*40)
                
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        if 'scraper' in locals():
            scraper.stop()

if __name__ == "__main__":
    main()
