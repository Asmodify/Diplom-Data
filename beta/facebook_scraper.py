#!/usr/bin/env python
"""
Manual Login Facebook Scraper
Uses Firefox browser and allows for manual login
"""

import os
import re
import sys
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostImage, PostComment
from db.config import LOGS_DIR, IMAGES_DIR, DEBUG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'scraper_manual.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ManualLoginFacebookScraper:
    def __init__(self, headless=False):
        """Initialize the Facebook scraper with manual login option"""
        self.db = DatabaseManager()
        self.wait_time = 10
        self.headless = headless
        self.ensure_directories()
        self.setup_driver()
            
    def ensure_directories(self):
        """Create necessary directories"""
        base_dirs = ['logs', 'images', 'debug']
        for dir_name in base_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
            
    def setup_driver(self):
        """Initialize Firefox browser for scraping"""
        logger.info("Setting up Firefox browser...")
        try:
            # Configure Firefox options
            options = FirefoxOptions()
            options.set_preference("dom.webnotifications.enabled", False)  # Disable notifications
            
            # Only use headless mode if specified
            if self.headless:
                options.headless = True
                logger.info("Running in headless mode")
            else:
                logger.info("Running in visible browser mode for manual login")
            
            # Try with WebDriver Manager if available
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    logger.info("Using WebDriver Manager for Firefox setup")
                    service = FirefoxService(GeckoDriverManager().install())
                    self.driver = webdriver.Firefox(service=service, options=options)
                except Exception as e:
                    logger.warning(f"WebDriver Manager approach failed: {e}")
                    # Fall back to direct Firefox setup
                    logger.info("Falling back to direct Firefox setup")
                    self.driver = webdriver.Firefox(options=options)
            else:
                # Direct Firefox setup
                logger.info("WebDriver Manager not available, using direct Firefox setup")
                self.driver = webdriver.Firefox(options=options)
            
            logger.info("Firefox browser set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Firefox browser: {e}")
            # Save detailed error information
            error_log_path = DEBUG_DIR / f"browser_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_log_path, "w") as f:
                f.write(f"Error: {e}\n")
                  # Set driver to None to prevent further errors
            self.driver = None
            raise RuntimeError(f"Failed to set up Firefox browser: {e}")
    
    def manual_login(self, wait_time=600):
        """Prompt user to manually log in to Facebook"""
        logger.info("Starting manual login process...")
        
        # Navigate to Facebook login page
        self.driver.get("https://www.facebook.com")
        
        print("\n" + "="*80)
        print("MANUAL LOGIN REQUIRED - STRICT MODE")
        print("="*80)
        print("1. A Firefox browser window has opened to Facebook's login page")
        print("2. Log in to Facebook with your credentials")
        print("3. Make sure you complete the ENTIRE login process (security checks, etc.)")
        print("4. When you can see your Facebook feed/homepage, return to this terminal")
        print("5. Type 'done' and press Enter to continue (this is the ONLY way to continue)")
        print()
        print("NOTE: The script will ONLY continue after you type 'done' - no automatic detection")
        print("      Take your time to log in properly. No time limit for login.")
        print("="*80)
        
        # Wait for user confirmation - much simpler approach
        while True:
            user_input = input("\nWhen you're logged in completely, type 'done': ").strip().lower()
            if user_input == 'done':
                print("\nThank you! Continuing with scraping...")
                break
            elif user_input == 'quit' or user_input == 'exit':
                print("\nAborting login process...")
                return False
            else:
                print("Invalid input. Type 'done' when you've completed login or 'quit' to exit.")
        
        # Take a screenshot for confirmation
        self.save_debug_info("login_success_manual")
        
        # Wait a moment to ensure everything is loaded
        time.sleep(2)
        
        print("\nLogin confirmed! Proceeding with scraping...")
        return True

    def save_debug_info(self, prefix):
        """Save debug screenshots and HTML for troubleshooting"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        
        # Save screenshot
        try:
            screenshot_path = debug_dir / f"{prefix}_{timestamp}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Save HTML
            html_path = debug_dir / f"{prefix}_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                
            logger.info(f"Saved debug info: {screenshot_path} and {html_path}")
        except Exception as e:
            logger.error(f"Error saving debug info: {e}")

    def navigate_to_page(self, page_name):
        """Navigate to a Facebook page"""
        logger.info(f"Navigating to page: {page_name}")
        try:
            self.driver.get(f"https://www.facebook.com/{page_name}")
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
            )
            # Save debug info for this page
            self.save_debug_info(f"page_{page_name}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to page {page_name}: {e}")
            self.save_debug_info(f"error_{page_name}")
            return False

    def scroll_page(self, num_scrolls=5, scroll_pause=2):
        """Scroll down the page to load more posts"""
        logger.info(f"Scrolling page, {num_scrolls} scrolls")
        try:
            for i in range(num_scrolls):
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load more posts
                time.sleep(scroll_pause)
                
                # Log progress
                if i % 2 == 0:
                    logger.info(f"Scrolled {i+1}/{num_scrolls} times")
            
            return True
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
            return False

    def extract_post_id(self, url):
        """Extract post ID from URL"""
        if not url:
            return None
        
        # Try different patterns to extract post ID
        patterns = [
            r'\/posts\/(\d+)',
            r'\/story\.php\?story_fbid=(\d+)',
            r'fbid=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no patterns match, use the entire URL hash
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()

    def clean_url(self, url):
        """Clean Facebook URL by removing tracking parameters"""
        if not url:
            return url
        
        parsed = urlparse(url)
        if 'facebook.com' not in parsed.netloc:
            return url
            
        # Keep only essential parameters
        query = parse_qs(parsed.query)
        clean_query = {k: v[0] for k, v in query.items() if k in ['story_fbid', 'id']}
        
        # Rebuild URL
        from urllib.parse import urlencode
        clean_parsed = parsed._replace(query=urlencode(clean_query))
        return clean_parsed.geturl()

    def download_image(self, url, page_name, post_id):
        """Download image and save to local path"""
        if not url:
            return None, None
            
        try:
            logger.info(f"Downloading image: {url}")
            
            # Create directory for page if it doesn't exist
            image_dir = Path("images") / page_name
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename based on post ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"post_{post_id}_{timestamp}.jpg"
            local_path = str(image_dir / filename)
            
            # Download image
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                        
                logger.info(f"Image saved to: {local_path}")
                return local_path, filename
            else:
                logger.error(f"Failed to download image, status code: {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None, None

    def extract_comments(self, post_element):
        """Extract comments from post"""
        comments = []
        try:
            # Try to find the "View more comments" button and click it
            try:
                more_comments_btn = post_element.find_element(By.XPATH, 
                    ".//span[contains(text(), 'View more comments') or contains(text(), 'View all comments')]")
                self.driver.execute_script("arguments[0].click();", more_comments_btn)
                time.sleep(2)
            except Exception:
                # It's ok if this fails - just means there aren't more comments to load
                pass
                
            # Find all comment elements
            comment_elements = post_element.find_elements(By.CSS_SELECTOR, "div[role='article'][aria-label*='Comment']")
            
            for comment_el in comment_elements[:10]:  # Limit to 10 comments per post for efficiency
                try:
                    # Extract author name
                    author = comment_el.find_element(By.CSS_SELECTOR, "a[role='link']").text
                    
                    # Extract comment text
                    text_elements = comment_el.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
                    text = text_elements[0].text if text_elements else ""
                    
                    # Extract timestamp if available
                    try:
                        timestamp_element = comment_el.find_element(By.CSS_SELECTOR, "a[role='link'][href*='comment_id']")
                        timestamp_text = timestamp_element.text
                        comment_time = datetime.now()  # Default to current time
                    except:
                        timestamp_text = "Unknown"
                        comment_time = datetime.now()
                    
                    # Extract likes
                    try:
                        likes_element = comment_el.find_element(By.CSS_SELECTOR, "span[role='toolbar']")
                        likes_text = likes_element.text
                        likes = int(re.search(r'(\d+)', likes_text).group(1)) if re.search(r'(\d+)', likes_text) else 0
                    except:
                        likes = 0
                    
                    comment = PostComment(
                        author=author,
                        text=text,
                        comment_time=comment_time,
                        likes=likes,
                        extracted_at=datetime.now()
                    )
                    
                    comments.append(comment)
                except Exception as e:
                    logger.error(f"Error extracting comment: {e}")
                    continue
                    
            return comments
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
            return comments

    def extract_post_data(self, post_element, page_name):
        """Extract all data from a post element"""
        try:
            # Extract post link/URL
            try:
                timestamp_elements = post_element.find_elements(By.CSS_SELECTOR, "a[href*='/posts/']")
                if not timestamp_elements:
                    timestamp_elements = post_element.find_elements(By.CSS_SELECTOR, "a[href*='story_fbid=']")
                
                post_url = timestamp_elements[0].get_attribute("href") if timestamp_elements else None
                post_url = self.clean_url(post_url)
                post_id = self.extract_post_id(post_url)
            except Exception as e:
                logger.error(f"Error extracting post URL: {e}")
                post_url = None
                post_id = f"unknown_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Extract post text
            try:
                text_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-ad-comet-preview='message']")
                if not text_elements:
                    text_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-ad-preview='message']")
                post_text = text_elements[0].text if text_elements else ""
            except:
                post_text = ""
            
            # Extract timestamp
            try:
                if timestamp_elements:
                    timestamp_text = timestamp_elements[0].text
                    # Try to parse timestamp text or use current time
                    post_time = datetime.now()
                else:
                    post_time = datetime.now()
            except:
                post_time = datetime.now()
                
            # Extract author/poster name
            try:
                author_elements = post_element.find_elements(By.CSS_SELECTOR, "a[role='link'][tabindex='0'] strong span")
                author = author_elements[0].text if author_elements else page_name
            except:
                author = page_name
            
            # Extract engagement metrics (likes, shares)
            try:
                like_elements = post_element.find_elements(By.CSS_SELECTOR, "span[role='toolbar']")
                likes_text = like_elements[0].text if like_elements else "0"
                
                # Extract numbers from text
                likes_match = re.search(r'(\d+)', likes_text)
                likes = int(likes_match.group(1)) if likes_match else 0
                
                # Look for shares count
                shares_elements = post_element.find_elements(By.XPATH, ".//span[contains(text(), 'shares')]")
                shares_text = shares_elements[0].text if shares_elements else "0"
                shares_match = re.search(r'(\d+)', shares_text)
                shares = int(shares_match.group(1)) if shares_match else 0
            except Exception as e:
                logger.error(f"Error extracting engagement metrics: {e}")
                likes = 0
                shares = 0
            
            # Create post object
            post = FacebookPost(
                page_name=page_name,
                post_id=post_id,
                post_url=post_url,
                post_text=post_text,
                post_time=post_time,
                author=author,
                likes=likes,
                shares=shares,
                extracted_at=datetime.now()
            )
            
            # Extract images
            images = []
            try:
                img_elements = post_element.find_elements(By.CSS_SELECTOR, "img[src*='scontent']")
                
                for img in img_elements[:3]:  # Limit to first 3 images per post
                    img_url = img.get_attribute("src")
                    if img_url and "scontent" in img_url:
                        local_path, filename = self.download_image(img_url, page_name, post_id)
                        if local_path:
                            img = PostImage(
                                post_id=post_id,
                                original_url=img_url,
                                local_path=local_path,
                                filename=filename,
                                downloaded_at=datetime.now()
                            )
                            images.append(img)
            except Exception as e:
                logger.error(f"Error extracting images: {e}")
            
            # Extract comments
            comments = self.extract_comments(post_element)
            for comment in comments:
                comment.post_id = post_id
                
            # Return complete post data
            return {
                'post': post,
                'images': images,
                'comments': comments
            }
            
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None
            
    def scrape_page(self, page_name, max_posts=10):
        """Scrape posts from a specific page"""
        logger.info(f"Scraping page: {page_name}")
        
        if not self.navigate_to_page(page_name):
            logger.error(f"Failed to navigate to page: {page_name}")
            return False
        
        # Scroll to load more posts
        self.scroll_page(num_scrolls=5)  # Increased scroll count for more content
        
        # Find all post elements
        try:
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            logger.info(f"Found {len(post_elements)} post elements")
            
            # Process posts up to max_posts
            posts_processed = 0
            for post_element in post_elements[:max_posts]:
                try:
                    # Extract post data
                    post_data = self.extract_post_data(post_element, page_name)
                    
                    if post_data:
                        # Save to database
                        if self.db.save_post(post_data['post'], post_data['images'], post_data['comments']):
                            posts_processed += 1
                            logger.info(f"Processed post {posts_processed}/{max_posts}")
                            
                except Exception as e:
                    logger.error(f"Error processing post: {e}")
                    self.save_debug_info(f"post_error_{page_name}_{posts_processed}")
                    continue
                    
            logger.info(f"Finished scraping page {page_name}, processed {posts_processed} posts")
            return posts_processed > 0  # Return success only if we processed at least one post
            
        except Exception as e:
            logger.error(f"Error finding post elements: {e}")
            self.save_debug_info(f"page_error_{page_name}")
            return False

    def run(self, pages=None, max_posts_per_page=5, wait_time=240):
        """Run the scraper on multiple pages with manual login"""
        logger.info("Starting Facebook scraper with manual login and Firefox browser")
        
        # Login to Facebook manually
        if not self.manual_login(wait_time=wait_time):
            logger.error("Manual login failed or timed out, aborting")
            return False
        
        # Use pages from list or read from file
        if not pages:
            try:
                with open('pages.txt', 'r', encoding='utf-8') as f:
                    pages = [line.strip() for line in f if line.strip()]
            except Exception as e:
                logger.error(f"Error reading pages file: {e}")
                return False
                
        if not pages:
            logger.error("No pages to scrape!")
            return False
        
        # Process each page
        success_count = 0
        for page in pages:
            try:
                logger.info(f"Processing page: {page}")
                if self.scrape_page(page, max_posts=max_posts_per_page):
                    success_count += 1
                # Wait between pages to avoid rate limiting
                time.sleep(5)  # Increased wait time to be safer against detection
            except Exception as e:
                logger.error(f"Error processing page {page}: {e}")
                continue
        
        logger.info(f"Facebook scraping completed. Successfully scraped {success_count}/{len(pages)} pages")
        return success_count > 0  # Return success only if we processed at least one page

    def close(self):
        """Close the browser and clean up"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Scraper with Manual Login')
    parser.add_argument('--pages', nargs='+', help='List of Facebook page names to scrape')
    parser.add_argument('--pages-file', type=str, default='pages.txt',
                        help='File containing list of Facebook page names (one per line)')
    parser.add_argument('--max-posts', type=int, default=5,
                        help='Maximum number of posts to scrape per page')
    parser.add_argument('--wait-time', type=int, default=240,
                        help='Time to wait for manual login in seconds (default: 240)')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode (NOT recommended for manual login)')
    
    args = parser.parse_args()
    
    # Get pages to scrape
    pages = args.pages
    if not pages:
        try:
            with open(args.pages_file, 'r', encoding='utf-8') as f:
                pages = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error reading pages file: {e}")
            return 1
    
    if not pages:
        logger.error("No pages specified for scraping!")
        return 1
    
    # Initialize scraper (visible browser for manual login)
    scraper = ManualLoginFacebookScraper(headless=args.headless)
    
    try:
        # Run the scraper with custom wait time if specified
        success = scraper.run(pages=pages, max_posts_per_page=args.max_posts, wait_time=args.wait_time)
        if success:
            logger.info("✅ Scraping completed successfully")
            return 0
        else:
            logger.error("❌ Scraping failed")
            return 1
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return 1
    finally:
        # Clean up
        scraper.close()
    

if __name__ == "__main__":
    sys.exit(main())
