from scraper.edge_scraper import EdgeFacebookScraper
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Example usage of EdgeFacebookScraper"""
    try:
        # Initialize the scraper (no credentials for manual login)
        scraper = EdgeFacebookScraper(
            max_posts=10,  # Scrape 10 posts
            take_screenshots=True,  # Save screenshots
            download_images=True  # Download images
        )
        
        # Initialize the browser
        if not scraper.initialize_driver():
            logger.error("Failed to initialize browser")
            return
            
        # Login (will wait for manual login)
        logger.info("Please login manually when the browser opens...")
        if not scraper.login():
            logger.error("Login failed")
            return
            
        # List of pages to scrape
        pages = [
            "https://www.facebook.com/cnn",
            "https://www.facebook.com/bbcnews"
        ]
        
        # Create output directory
        output_dir = Path("example_output")
        output_dir.mkdir(exist_ok=True)
        
        # Scrape each page
        for page_url in pages:
            try:
                logger.info(f"Scraping page: {page_url}")
                
                # Get posts
                posts = scraper.scrape_posts(page_url)
                
                if posts:
                    # Print posts to console
                    scraper.print_posts(posts)
                    
                    # Save posts to JSON
                    page_name = page_url.split('/')[-1]
                    output_file = output_dir / f"{page_name}_posts.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(posts, f, indent=2, ensure_ascii=False)
                        
                    logger.info(f"Saved {len(posts)} posts to {output_file}")
                else:
                    logger.warning(f"No posts found for {page_url}")
                    
            except Exception as e:
                logger.error(f"Error scraping {page_url}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        
    finally:
        # Clean up
        if scraper:
            scraper.close()
            
if __name__ == "__main__":
    main()
