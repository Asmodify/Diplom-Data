"""
Automated Facebook scraper that coordinates browser management,
scraping, and content saving with human-like behavior.
"""

import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from fb_credentials import FB_EMAIL, FB_PASSWORD
from scraper.browser_manager import BrowserManager
from scraper.post_scraper import PostScraper
from content_manager.content_manager import ContentSaver

# Configure logging
logger = logging.getLogger(__name__)

class AutoScraper:
    """Automates the Facebook scraping process"""
    def __init__(self, headless: bool = False, max_posts: int = 100,
                 take_screenshots: bool = True, download_images: bool = True,
                 pages_file: str = "pages.txt", max_retries: int = 3):
        self.headless = headless
        self.max_posts = max_posts
        self.take_screenshots = take_screenshots
        self.download_images = download_images
        self.pages_file = pages_file
        self.max_retries = max_retries
        self.browser = None
        self.driver = None
        self.scraper = None
        self.content_saver = None
        self.logger = logging.getLogger(__name__)
        self._initialize_browser()

    def _initialize_browser(self):
        """Initialize or reinitialize the browser and related components"""
        try:
            # Close existing browser if any
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
                    
            self.browser = BrowserManager(headless=self.headless)
            self.driver = self.browser.start()
            self.scraper = PostScraper(
                driver=self.driver,
                max_comments=self.max_posts,
                take_screenshots=self.take_screenshots,
                download_images=self.download_images
            )
            self.content_saver = ContentSaver(base_dir=str(Path(__file__).parent.parent))
            self.logger.info("Browser initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def _ensure_browser_ready(self) -> bool:
        """Ensure browser is ready, restart if necessary"""
        if self.browser and self.browser.is_session_alive():
            return True
        
        self.logger.warning("Browser session not ready, reinitializing...")
        return self._initialize_browser()

    def start(self) -> bool:
        """
        Start the scraping session
        
        Returns:
            bool: Whether startup was successful
        """
        try:
            if not self._ensure_browser_ready():
                return False
                
            # Attempt login
            if not self.browser.manual_login():
                self.logger.error("Failed to log in")
                return False
                
            time.sleep(random.uniform(3, 5))  # Wait for login to settle
            return True
            
        except Exception as e:
            self.logger.error(f"Error during startup: {str(e)}")
            return False
            
    def read_pages(self) -> List[str]:
        """Read the list of pages to scrape from a file"""
        try:
            pages_path = Path(__file__).parent.parent / self.pages_file
            if not pages_path.exists():
                self.logger.error(f"Pages file not found: {self.pages_file}")
                return []
                
            with open(pages_path, 'r') as f:
                pages = [line.strip() for line in f if line.strip()]
                
            self.logger.info(f"Found {len(pages)} pages to scrape")
            return pages
            
        except Exception as e:
            self.logger.error(f"Error reading pages file: {e}")
            return []
    
    def parse_comment_count(self, comment_text: Optional[str]) -> int:
        """Parse Facebook comment count text to number"""
        try:
            if not comment_text:
                return 0
            # Remove 'comment' or 'comments' and any extra spaces
            count = comment_text.lower().split()[0]
            if 'k' in count:  # Handle "1.2K comments" format
                return int(float(count.replace('k', '')) * 1000)
            return int(count)
        except:
            return 0
            
    def should_scrape_comments(self, post_data: Dict[str, Any]) -> Tuple[bool, int]:
        """
        Check if a post's comments should be scraped
        Returns:
            Tuple of (should_scrape: bool, comment_count: int)
        """
        comment_count = self.parse_comment_count(post_data.get('comments'))
        return comment_count > 0, comment_count
        
    def scrape_pages(self, pages: List[str] = None) -> bool:
        """
        Scrape posts from multiple Facebook pages
        
        Args:
            pages: Optional list of Facebook page URLs to scrape.
                  If not provided, reads from pages file.
            
        Returns:
            bool: Whether all pages were scraped successfully
        """
        # If no pages provided, read from file
        if pages is None:
            pages = self.read_pages()
            
        if not pages:
            self.logger.warning("No pages to scrape")
            return False
            
        success = True
        for page_url in pages:
            if not self.scrape_page(page_url):
                success = False
                # Wait between pages
                time.sleep(10)
                
        return success
    
    def scrape_page(self, page_url: str) -> bool:
        """
        Scrape a single Facebook page with robust navigation and scrolling
        
        Args:
            page_url: The Facebook page URL or ID to scrape
            
        Returns:
            bool: Whether scraping was successful
        """
        for attempt in range(self.max_retries):
            try:
                # Ensure browser is ready
                if not self._ensure_browser_ready():
                    self.logger.error("Cannot establish browser session")
                    continue
                
                # Ensure we're logged in
                if not self.browser.logged_in:
                    self.logger.info("Attempting to log in...")
                    if not self.browser.manual_login():
                        self.logger.error("Failed to log in")
                        # Try reinitializing browser for next attempt
                        if attempt < self.max_retries - 1:
                            self._initialize_browser()
                        continue

                # Build full URL
                if not page_url.startswith('https://'):
                    full_url = f'https://www.facebook.com/{page_url}'
                else:
                    full_url = page_url

                # Robust navigation
                if not self.browser.navigate_to(full_url):
                    self.logger.error(f"Failed to navigate to {full_url}")
                    # Check if session died during navigation
                    if not self.browser.is_session_alive():
                        self._initialize_browser()
                    continue

                # Simulate human scrolling to load content
                self.browser.simulate_human_scroll(max_scrolls=8)

                # Get the page name from the URL
                page_name = page_url.split('/')[-1] if '/' in page_url else page_url
                if '?' in page_name:
                    page_name = page_name.split('?')[0]

                # Scrape the page using get_posts
                posts_data = self.scraper.get_posts(page_name)

                # Save content
                for post in posts_data:
                    try:
                        self.content_saver.save_post(post, page_name)
                    except Exception as save_error:
                        self.logger.warning(f"Error saving post: {save_error}")

                self.logger.info(f"Successfully scraped {len(posts_data)} posts from {page_url}")
                return True
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}/{self.max_retries} failed for {page_url}: {e}")
                
                # Check if we need to restart browser
                if not self.browser or not self.browser.is_session_alive():
                    self.logger.warning("Browser session died, reinitializing...")
                    self._initialize_browser()
                
                if attempt < self.max_retries - 1:
                    time.sleep(5)  # Wait before retry
        
        self.logger.error(f"Failed to scrape page {page_url} after {self.max_retries} attempts")
        return False
    
    def close(self):
        """Close the scraping session"""
        try:
            if self.scraper:
                self.scraper.close()
        except Exception as e:
            self.logger.debug(f"Error closing scraper: {e}")
            
    def stop(self):
        """Stop the scraper and clean up resources"""
        try:
            # Close scraper first
            self.close()
            
            # Then close browser
            if self.browser:
                self.browser.close()
                self.browser = None
                self.driver = None
                self.logger.info("Browser session closed")
        except Exception as e:
            self.logger.error(f"Error during scraper cleanup: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automated Facebook scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--pages", type=str, help="Path to pages file", default="pages.txt")
    parser.add_argument("--max-posts", type=int, default=100, help="Maximum posts per page")
    parser.add_argument("--no-screenshots", action="store_true", help="Disable post screenshots")
    parser.add_argument("--no-images", action="store_true", help="Disable image downloads")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scraper = AutoScraper(
        headless=args.headless,
        max_posts=args.max_posts,
        take_screenshots=not args.no_screenshots,
        download_images=not args.no_images,
        pages_file=args.pages
    )
    
    try:
        if scraper.start():
            success = scraper.scrape_pages()
            print("Scraping completed successfully" if success else "Some pages failed to scrape")
    finally:
        scraper.close()
