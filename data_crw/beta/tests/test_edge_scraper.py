import os
import sys
import time
import logging
import logging
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.browser_manager import BrowserManager
from fb_credentials import FB_EMAIL, FB_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_edge_scraper():
    # Initialize the scraper
    scraper = EdgeFacebookScraper(
        email="",  # Will use manual login
        password="",
        max_posts=10,
        take_screenshots=True,
        download_images=True
    )
    
    try:
        # Initialize driver
        if not scraper.initialize_driver():
            logger.error("Failed to initialize EdgeDriver")
            return
            
        # Direct to Facebook login
        scraper.driver.get("https://www.facebook.com/login")
        
        # Prompt for manual login
        print("\nPlease log in manually in the browser window.")
        input("Press Enter after you have logged in successfully...")
        
        # Verify login by checking for typical elements
        try:
            WebDriverWait(scraper.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Facebook']"))
            )
            logger.info("Login successful")
        except Exception as e:
            logger.error("Login verification failed")
            return
            
        # Test pages to scrape
        test_pages = [
            "https://www.facebook.com/cnn",
            "https://www.facebook.com/bbcnews"
        ]
        
        for page_url in test_pages:
            logger.info(f"\nTesting scraper on {page_url}")
            posts = scraper.scrape_posts(page_url, max_posts=5)
            
            if posts:
                logger.info(f"Successfully scraped {len(posts)} posts")
                scraper.print_posts(posts)
            else:
                logger.error(f"No posts were scraped from {page_url}")
                
            # Wait between pages
            time.sleep(10)
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    test_edge_scraper()
