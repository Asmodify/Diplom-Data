#!/usr/bin/env python
"""
Enhanced Facebook Post and Comment Scraper
Intelligently handles post screenshots and comment extraction:
1. Screenshots posts with their likes, author, and timestamp
2. Detects if posts have comments
3. For posts with comments, navigates to post page and extracts comments
4. Handles pagination and limits for posts with many comments
5. Captures all comment replies
"""

import sys
import os
import re
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

# Import project modules
from db.database import DatabaseManager
from db.config import LOGS_DIR, DEBUG_DIR, IMAGES_DIR
from db.models import FacebookPost, PostImage, PostComment

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
    from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. Please install selenium package.")

try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("Warning: Webdriver-manager not available. Will use local Firefox driver.")

# Configure logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'smart_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FacebookEventListener(AbstractEventListener):
    """Event listener for Selenium actions to help with debugging"""
    
    def before_navigate_to(self, url, driver):
        logger.debug(f"Navigating to: {url}")
        
    def after_navigate_to(self, url, driver):
        logger.debug(f"Navigated to: {url}")
        
    def before_click(self, element, driver):
        logger.debug(f"Clicking element: {element.get_attribute('outerHTML')[:100]}...")
        
    def after_click(self, element, driver):
        logger.debug("Clicked element")
        
    def on_exception(self, exception, driver):
        logger.warning(f"Exception occurred: {exception}")

class SmartFacebookScraper:
    """
    Enhanced Facebook scraper with intelligent comment handling
    """
    def __init__(self, headless=False, wait_time=300, download_images=True, 
                 take_screenshots=True, max_comments=50, use_cookies=True):
        """
        Initialize the scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            wait_time (int): Maximum time to wait for manual login (seconds)
            download_images (bool): Whether to download images from posts
            take_screenshots (bool): Whether to take screenshots of posts
            max_comments (int): Maximum number of comments to extract per post (0 = all)
            use_cookies (bool): Whether to use cookies for login
        """
        self.driver = None
        self.headless = headless
        self.wait_time = wait_time
        self.download_images = download_images
        self.take_screenshots = take_screenshots
        self.max_comments = max_comments
        self.use_cookies = use_cookies
        self.logged_in = False
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Create required directories
        IMAGES_DIR.mkdir(exist_ok=True)
        DEBUG_DIR.mkdir(exist_ok=True)
    
    def start(self):
        """Start the browser session"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium is not available. Please install the selenium package.")
            return False
        
        try:
            logger.info("Setting up Firefox driver...")
            options = FirefoxOptions()
            
            if self.headless:
                options.add_argument("--headless")
                
            # Add preferences to improve performance and avoid detection
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("media.volume_scale", "0.0")  # Mute audio
            
            # Set user agent to avoid detection
            options.set_preference("general.useragent.override", 
                                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36")
            
            # Set up Firefox driver
            service = FirefoxService(GeckoDriverManager().install() if WEBDRIVER_MANAGER_AVAILABLE else "geckodriver")
            driver = webdriver.Firefox(service=service, options=options)
            
            # Add event listener for better debugging
            self.driver = EventFiringWebDriver(driver, FacebookEventListener())
            
            # Set window size and position
            self.driver.set_window_size(1366, 768)
            self.driver.set_window_position(0, 0)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(60)
            
            logger.info("Firefox browser set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Firefox driver: {e}")
            return False
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
    
    def manual_login(self):
        """
        Perform manual login to Facebook
        
        Returns:
            bool: Whether login was successful
        """
        if not self.driver:
            self.start()
            
        if not self.driver:
            logger.error("Browser not available for login")
            return False
        
        try:
            # Navigate to Facebook
            logger.info("Navigating to Facebook login page...")
            self.driver.get("https://www.facebook.com/")
            
            # Check if already logged in
            if self._check_login_status():
                logger.info("Already logged in to Facebook")
                self.logged_in = True
                return True
                
            print("\n" + "="*80)
            print("MANUAL LOGIN REQUIRED")
            print("="*80)
            print("1. Log in to Facebook with your credentials in the browser window")
            print("2. Complete any security checks if prompted")
            print("3. Return to this terminal when logged in")
            print("4. Type 'done' and press Enter to continue (or wait for auto-detection)")
            print("="*80)
            
            # Set up wait for login
            wait = WebDriverWait(self.driver, self.wait_time)
            
            # Either wait for user input or automatic detection
            print("Please log in to Facebook and type 'done' when finished...")
            user_input = input("After logging in, type 'done' here: ")
            
            # ALWAYS ASSUME LOGIN IS SUCCESSFUL IF USER TYPES 'DONE'
            if user_input.strip().lower() == 'done':
                # Force logged in status to true regardless of detection
                self.logged_in = True
                print("✅ Login accepted! Proceeding...")
                
                # Save debug info
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = DEBUG_DIR / f"login_success_manual_{timestamp}.png"
                html_path = DEBUG_DIR / f"login_success_manual_{timestamp}.html"
                
                # Try to save debug information
                try:
                    self.driver.save_screenshot(str(screenshot_path))
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.info(f"Saved debug info: {screenshot_path.name} and {html_path.name}")
                except Exception as e:
                    logger.warning(f"Could not save debug info: {e}")
                
                # Still try auto detection but don't rely on it for success
                login_detected = self._check_login_status()
                if not login_detected:
                    logger.warning("Automated login verification failed, but continuing anyway as requested")
                    print("⚠️ Note: Automated verification couldn't detect login, but proceeding as requested")
                
                return True
            else:
                logger.warning("Manual login canceled or invalid input")
                return False
        
        except Exception as e:
            logger.error(f"Error during Facebook login: {e}")
            return False
    
    def _check_login_status(self):
        """
        Check if we're logged in to Facebook
        
        Returns:
            bool: Whether we're logged in
        """
        try:
            # Look for elements that only appear when logged in (using multiple detection methods)
            # Method 1: Search box
            search_box = self.driver.find_elements(By.XPATH, "//input[@aria-label='Search Facebook' or @placeholder='Search Facebook']")
            
            # Method 2: Profile link
            profile_link = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/me/') or contains(@href, '/profile.php')]")
            
            # Method 3: Feed elements
            feed_elements = self.driver.find_elements(By.XPATH, "//div[@role='feed' or @data-pagelet='Feed']")
            
            # Method 4: Check for logout button/link
            logout_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'Log Out') or contains(text(), 'Logout')]")
            
            # Method 5: Check for typical elements in the Facebook header when logged in
            header_elements = self.driver.find_elements(By.XPATH, "//div[@role='navigation' or @aria-label='Facebook']")
            
            # Method 6: Check for cookies/storage that indicate login
            # This assumes the Facebook login cookie is present
            facebook_cookies = self.driver.get_cookies()
            has_login_cookie = any('c_user' in cookie.get('name', '') for cookie in facebook_cookies)
            
            # Consider logged in if ANY of these elements are found
            is_logged_in = bool(search_box or profile_link or feed_elements or logout_elements or header_elements or has_login_cookie)
            
            if is_logged_in:
                logger.info("Login status check: User is logged in")
                # Take a screenshot for debug purposes
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                DEBUG_DIR.mkdir(exist_ok=True)
                screenshot_path = DEBUG_DIR / f"login_verified_{timestamp}.png"
                self.driver.save_screenshot(str(screenshot_path))
            else:
                logger.warning("Login status check: User is NOT logged in")
                
            return is_logged_in
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def navigate_to_page(self, page_name):
        """
        Navigate to a Facebook page
        
        Args:
            page_name (str): Name of the Facebook page
            
        Returns:
            bool: Whether navigation was successful
        """
        if not self.driver:
            logger.error("Browser not initialized")
            return False
            
        if not self.logged_in and not self._check_login_status():
            logger.error("Not logged in to Facebook")
            return False
            
        try:
            logger.info(f"Navigating to page: {page_name}")
            
            # Handle both page names and full URLs
            if page_name.startswith("http"):
                url = page_name
            else:
                url = f"https://www.facebook.com/{page_name}"
                
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check if page exists by looking for page content
            content = self.driver.find_elements(By.XPATH, "//div[@role='main']")
            if not content:
                logger.warning(f"Page content not found: {page_name}")
                return False
                
            logger.info(f"Successfully navigated to page: {page_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to page {page_name}: {e}")
            return False
    
    def scroll_page_for_posts(self, max_posts=10):
        """
        Scroll through a Facebook page to load posts
        
        Args:
            max_posts (int): Maximum number of posts to load (0 = all)
            
        Returns:
            list: List of post elements found
        """
        if not self.driver:
            logger.error("Browser not initialized")
            return []
            
        try:
            # Find post elements
            post_selectors = [
                "//div[@role='article' and @aria-labelledby]",
                "//div[contains(@class, 'userContentWrapper')]",
                "//div[contains(@class, '_5pcr')]",
                "//div[contains(@class, '_4-u2 _4-u8')]",
                "//div[contains(@class, 'post_container')]"
            ]
            
            post_elements = []
            for selector in post_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    post_elements = elements
                    break
                    
            if not post_elements:
                logger.warning("No posts found with any selector")
                return []
                
            # Limit the number of posts
            if max_posts > 0 and len(post_elements) >= max_posts:
                return post_elements[:max_posts]
                
            # If we need more posts, scroll to load more
            attempts = 0
            max_attempts = 20 if max_posts == 0 else min(10, max_posts)
            
            while (max_posts == 0 or len(post_elements) < max_posts) and attempts < max_attempts:
                # Scroll down to load more posts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Wait for posts to load
                
                # Find posts again
                for selector in post_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements and len(elements) > len(post_elements):
                        post_elements = elements
                        logger.info(f"Found {len(post_elements)} posts so far...")
                        break
                        
                # Stop if no new posts were loaded
                if attempts > 0 and len(post_elements) == prev_count:
                    break
                    
                prev_count = len(post_elements)
                attempts += 1
                
            logger.info(f"Finished scrolling, found {len(post_elements)} posts")
            
            # Limit the number of posts again
            if max_posts > 0:
                return post_elements[:max_posts]
                
            return post_elements
            
        except Exception as e:
            logger.error(f"Error scrolling for posts: {e}")
            return []
    
    def extract_post_data(self, post_element, page_name):
        """
        Extract data from a Facebook post element
        
        Args:
            post_element: Selenium WebElement for the post
            page_name (str): Name of the Facebook page
            
        Returns:
            dict: Post data dictionary or None if extraction failed
        """
        if not post_element:
            return None
            
        try:
            # Extract post ID or generate a unique ID
            post_id_attr = post_element.get_attribute("id")
            post_id = post_id_attr if post_id_attr else f"unknown_{int(time.time())}_{hash(post_element.text) % 10000}"
            
            # Take screenshot if enabled
            screenshot_path = None
            if self.take_screenshots:
                timestamp = int(time.time())
                img_dir = IMAGES_DIR / page_name / "screenshots"
                img_dir.mkdir(exist_ok=True, parents=True)
                
                screenshot_path = img_dir / f"post_{post_id}_{timestamp}.png"
                
                # Scroll to post and take screenshot
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
                time.sleep(1)
                post_element.screenshot(str(screenshot_path))
                
                logger.info(f"Saved post screenshot to {screenshot_path.name}")
            
            # Extract post URL
            post_url = None
            url_elements = post_element.find_elements(By.XPATH, ".//a[contains(@href, '/posts/') or contains(@href, '/photo.php') or contains(@href, '/permalink.php')]")
            for url_element in url_elements:
                href = url_element.get_attribute("href")
                if href and ("posts" in href or "photo.php" in href or "permalink.php" in href or "videos" in href):
                    post_url = href
                    break
            
            # Extract post text
            post_text = ""
            text_selectors = [
                ".//div[@data-ad-preview='message']",
                ".//div[contains(@class, 'userContent')]",
                ".//div[contains(@data-testid, 'post_message')]",
                ".//div[@dir='auto']"
            ]
            
            for selector in text_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                if elements:
                    post_text = elements[0].text
                    break
            
            # Extract post time
            post_time = datetime.now()
            time_selectors = [
                ".//a/span[@class='timestampContent']",
                ".//a[contains(@class, 'timestamp')]",
                ".//abbr",
                ".//a//span[contains(text(), 'hr') or contains(text(), 'min') or contains(text(), 'now')]"
            ]
            
            for selector in time_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                if elements and elements[0].text:
                    # We're just capturing current time for now
                    # A more sophisticated parsing of Facebook's relative time would go here
                    break
            
            # Extract author/poster
            author = page_name
            author_selectors = [
                ".//a[contains(@class, 'actor-link')]",
                ".//span[contains(@class, 'fwb')]//a",
                ".//h3[contains(@class, 'actor')]//a",
                ".//a[contains(@href, '/groups/') or contains(@href, '/pages/')]"
            ]
            
            for selector in author_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                if elements:
                    author = elements[0].text
                    break
            
            # Extract likes, comments, shares counts
            likes = 0
            comments_count = 0
            shares = 0
            
            # Look for likes count
            likes_selectors = [
                ".//span[contains(text(), 'Like') or contains(text(), 'like')]/following-sibling::span",
                ".//a[contains(@aria-label, 'reaction')]",
                ".//span[contains(@class, 'like_def')]/span"
            ]
            
            for selector in likes_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                for element in elements:
                    likes_text = element.get_attribute("aria-label") or element.text
                    if likes_text:
                        likes_match = re.search(r'(\d+)', likes_text)
                        if likes_match:
                            likes = int(likes_match.group(1))
                            break
            
            # Look for comments count
            comment_selectors = [
                ".//a[contains(text(), 'comment') or contains(text(), 'Comment')]",
                ".//span[contains(text(), 'comment') or contains(text(), 'Comment')]"
            ]
            
            for selector in comment_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text
                    comment_match = re.search(r'(\d+)\s*comment', text.lower())
                    if comment_match:
                        comments_count = int(comment_match.group(1))
                        break
            
            # Look for shares count
            shares_selectors = [
                ".//a[contains(text(), 'share') or contains(text(), 'Share')]",
                ".//span[contains(text(), 'share') or contains(text(), 'Share')]"
            ]
            
            for selector in shares_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text
                    shares_match = re.search(r'(\d+)\s*share', text.lower())
                    if shares_match:
                        shares = int(shares_match.group(1))
                        break
            
            # Build post data dictionary
            post_data = {
                'post_id': post_id,
                'page_name': page_name,
                'post_url': post_url,
                'post_text': post_text,
                'post_time': post_time,
                'author': author,
                'likes': likes,
                'shares': shares,
                'comments_count': comments_count,
                'screenshot_path': str(screenshot_path) if screenshot_path else None,
                'extracted_at': datetime.now()
            }            
            logger.info(f"Extracted post data: ID={post_id}, Likes={likes}, Comments={comments_count}, Images={1 if screenshot_path else 0}")
            return post_data
            
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None
    
    def has_comments(self, post_element):
        """
        Check if a post has comments
        
        Args:
            post_element: Selenium WebElement for the post
            
        Returns:
            tuple: (bool, int) - Whether the post has comments and how many
        """
        try:
            if not post_element:
                return False, 0
                
            # List of selectors to try in order of reliability
            comment_selectors = [
                # Best: Direct comment count indicators
                ".//span[contains(text(), 'comment') or contains(text(), 'Comment')]",
                ".//a[contains(text(), 'comment') or contains(text(), 'Comment')]",
                ".//div[contains(@class, 'comment-count')]",
                
                # Fallback: Comment action buttons/links
                ".//a[contains(@href, 'comment')]",
                ".//div[@role='button' and contains(., 'Comment')]",
                
                # Last resort: Comment containers
                ".//div[contains(@class, 'UFIList')]",
                ".//div[contains(@class, 'commentable_item')]",
                ".//div[@data-testid='UFI2CommentsList']"
            ]
            
            for selector in comment_selectors:
                elements = post_element.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        text = element.text.lower() if element.text else ""
                        if text:
                            # First try to get exact count
                            count_match = re.search(r'(\d+)\s*comment', text)
                            if count_match:
                                count = int(count_match.group(1))
                                logger.info(f"Found {count} comments via count indicator")
                                return True, count
                                
                            # Check for presence of comments without count
                            if "comment" in text:
                                # If text just says "comment" (singular), assume 1
                                if text == "comment":
                                    return True, 1
                                # If multiple/other, return True with 0 (unknown count)
                                return True, 0
                    except Exception as e:
                        logger.debug(f"Error checking comment element: {e}")
                        continue
            
            # No comment indicators found
            return False, 0
            
        except Exception as e:
            logger.error(f"Error checking if post has comments: {e}")
            return False, 0
    def extract_comments(self, post_data, max_retries=3):
        """
        Extract comments from a post URL with robust handling
        - Validates post URL and comment presence
        - Implements retry logic for navigation and extraction
        - Uses dynamic waits for loading
        - Handles pagination and nested replies
        - Limits to maximum comments per post
        
        Args:
            post_data (dict): Post data dictionary with URL and ID
            max_retries (int): Maximum number of retries for failed operations
            
        Returns:
            list: List of comment dictionaries
        """
        if not post_data or not post_data.get('post_url'):
            logger.warning("No post URL provided for comment extraction")
            return []
            
        try:
            post_id = post_data['post_id']
            post_url = post_data['post_url']
            expected_count = post_data.get('comments_count', 0)
            
            # Validate post has comments
            has_comments_check = post_data.get('has_comments', False)
            if not has_comments_check and expected_count == 0:
                logger.info(f"Post {post_id} appears to have no comments, skipping")
                print(f"Post {post_id} has no comments, skipping extraction")
                return []
                
            # Start extraction process
            logger.info(f"Starting comment extraction for post: {post_id}")
            print(f"📄 Starting comment extraction for post: {post_id}")
            print(f"🔗 Post URL: {post_url}")
            print(f"💬 Expected comments: {expected_count}")
            
            # Store current URL to restore later
            original_url = self.driver.current_url
            
            # Implement retry logic for navigation and extraction
            for attempt in range(max_retries):
                try:
                    print("🌐 Navigating to post page...")
                    self.driver.get(post_url)
                    
                    # Wait for page load with multiple indicators
                    wait = WebDriverWait(self.driver, 10)
                    loaded = False
                    
                    # Try different load indicators
                    load_conditions = [
                        EC.presence_of_element_located((By.XPATH, "//div[@role='main']")),
                        EC.presence_of_element_located((By.XPATH, "//div[@role='article']")),
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'userContentWrapper')]"))
                    ]
                    
                    for condition in load_conditions:
                        try:
                            wait.until(condition)
                            loaded = True
                            break
                        except TimeoutException:
                            continue
                    
                    if not loaded:
                        if attempt == max_retries - 1:
                            logger.error("Post page failed to load after all retries")
                            return []
                        continue
                    
                    # Take debug screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    DEBUG_DIR.mkdir(exist_ok=True)
                    screenshot_path = DEBUG_DIR / f"comments_start_{post_id}_{timestamp}.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    
                    # Scroll to comments section
                    print("📜 Scrolling to comments section...")
                    self._scroll_to_comments_section()
                    time.sleep(2)  # Wait for any animations
                    
                    # Check if comments section is visible
                    comment_section_visible = False
                    comment_section_selectors = [
                        "//div[@role='article' and contains(@aria-label, 'comment')]",
                        "//div[@data-testid='comment']",
                        "//div[contains(@class, 'UFIList')]"
                    ]
                    
                    for selector in comment_section_selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            if elements:
                                comment_section_visible = True
                                break
                        except:
                            continue
                    
                    if not comment_section_visible:
                        if attempt == max_retries - 1:
                            logger.warning("Comments section not found after all retries")
                            return []
                        continue
                    
                    # Expand comments with limit
                    print("🔄 Expanding comments (max 50)...")
                    self._expand_comments_limited(max_comments=50)
                    time.sleep(2)  # Wait for expansion
                    
                    # Take screenshot after expansion
                    screenshot_path = DEBUG_DIR / f"comments_expanded_{post_id}_{timestamp}.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    
                    # Extract comments
                    comments = self._extract_comment_elements(post_id, max_comments=50)
                    if comments:
                        return comments
                        
                    # If we got here but found no comments, try the next attempt
                    
                except Exception as e:
                    logger.warning(f"Error during extraction attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        logger.error("Failed to extract comments after all retries")
                        return []
                    time.sleep(3)
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting comments for post {post_data.get('post_id', 'unknown')}: {e}")
            print(f"❌ Error extracting comments: {e}")
            return []
    
    def _scroll_to_comments_section(self, max_attempts=3):
        """
        Scroll down to ensure comments section is visible
        Uses a progressive scroll strategy with validation
        """
        try:
            logger.info("Scrolling to find comments section")
            
            # Progressive scroll strategy
            for attempt in range(max_attempts):
                # First try small scroll jumps
                for i in range(3):
                    scroll_amount = 300 * (attempt + 1)  # Increase scroll amount with each attempt
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(0.5)  # Short pause between scrolls
                
                # Look for comments section with multiple selectors
                comments_section_selectors = [
                    "//div[@role='article' and contains(@aria-label, 'comment')]",
                    "//div[@data-testid='comment']",
                    "//div[contains(@class, 'UFIList')]",
                    "//div[contains(@class, 'commentable_item')]",
                    "//div[@aria-label='Comment']",
                    "//div[contains(@class, 'comments')]",
                    "//div[contains(text(), 'comment')]/ancestor::div[@role='article']"
                ]
                
                found_comments = False
                for selector in comments_section_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                # Try smooth scroll to element
                                self.driver.execute_script("""
                                    arguments[0].scrollIntoView({
                                        behavior: 'smooth',
                                        block: 'center'
                                    });
                                """, element)
                                time.sleep(1)  # Wait for scroll animation
                                
                                # Validate element is now in viewport
                                in_viewport = self.driver.execute_script("""
                                    var elem = arguments[0];
                                    var rect = elem.getBoundingClientRect();
                                    return (
                                        rect.top >= 0 &&
                                        rect.left >= 0 &&
                                        rect.bottom <= window.innerHeight &&
                                        rect.right <= window.innerWidth
                                    );
                                """, element)
                                
                                if in_viewport:
                                    logger.info("Successfully found and scrolled to comments section")
                                    found_comments = True
                                    break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                        
                if found_comments:
                    return True
                    
                if attempt < max_attempts - 1:
                    logger.debug(f"Comments not found, trying larger scroll (attempt {attempt + 1})")
                    # Try a larger scroll before next attempt
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
            
            logger.warning("Could not find comments section after all attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error scrolling to comments section: {e}")
            return False
    def _expand_comments_limited(self, max_comments=50):
        """
        Expand comments with intelligent limiting and robust error handling
        - Tracks actual comment counts
        - Uses smart retry logic for failed clicks
        - Validates successful expansions
        - Handles both main comments and replies
        
        Args:
            max_comments (int): Maximum number of comments to expand
        """
        try:
            total_expanded = 0
            max_attempts = 15  # Maximum expansion attempts
            
            # Track comment count before expansion to validate progress
            initial_comments = self._count_visible_comments()
            logger.info(f"Starting with {initial_comments} visible comments")
            
            for attempt in range(max_attempts):
                if total_expanded >= max_comments:
                    logger.info(f"Reached comment limit ({max_comments}), stopping expansion")
                    print(f"🛑 Reached comment limit ({max_comments})")
                    break
                
                expansion_made = False
                current_comments = self._count_visible_comments()
                
                # First try to expand main comments
                view_more_selectors = [
                    "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View previous comments')]/ancestor::div[@role='button']", 
                    "//div[@role='button' and contains(., 'View more comments')]",
                    "//div[@role='button' and contains(., 'View previous comments')]",
                    "//span[contains(text(), 'View') and contains(text(), 'comment')]/ancestor::*[@role='button']",
                    "//a[contains(@class, 'UFIPagerLink')]",
                    "//div[contains(@class, 'UFIPagerLink')]"
                ]
                
                # Try each selector with retry logic
                for selector in view_more_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if not button.is_displayed() or not button.is_enabled():
                                continue
                                
                            # Scroll to button smoothly
                            self.driver.execute_script("""
                                arguments[0].scrollIntoView({
                                    behavior: 'smooth',
                                    block: 'center'
                                });
                            """, button)
                            time.sleep(0.5)
                            
                            # Try clicking with multiple methods
                            click_success = False
                            for click_method in [
                                lambda: button.click(),
                                lambda: self.driver.execute_script("arguments[0].click();", button),
                                lambda: webdriver.ActionChains(self.driver).move_to_element(button).click().perform()
                            ]:
                                try:
                                    click_method()
                                    
                                    # Wait for new comments with explicit wait
                                    try:
                                        WebDriverWait(self.driver, 5).until(
                                            lambda d: self._count_visible_comments() > current_comments
                                        )
                                        click_success = True
                                        break
                                    except TimeoutException:
                                        continue
                                        
                                except Exception as e:
                                    logger.debug(f"Click attempt failed: {e}")
                                    continue
                            
                            if click_success:
                                new_count = self._count_visible_comments()
                                added = new_count - current_comments
                                total_expanded += added
                                print(f"🔄 Expanded {added} more comments (total: {new_count})")
                                expansion_made = True
                                break
                    
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                # Then try to expand replies if we haven't hit limit
                if not expansion_made and total_expanded < max_comments:
                    reply_selectors = [
                        "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                        "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                        "//a[contains(@class, 'UFIReplyList')]",
                        "//div[contains(@class, 'UFIReplyList')]"
                    ]
                    
                    for selector in reply_selectors:
                        try:
                            buttons = WebDriverWait(self.driver, 2).until(
                                EC.presence_of_all_elements_located((By.XPATH, selector))
                            )
                            
                            for button in buttons[:3]:  # Limit reply expansions per iteration
                                if not button.is_displayed() or not button.is_enabled():
                                    continue
                                
                                # Try each click method
                                current_count = self._count_visible_comments()
                                click_success = False
                                
                                for click_method in [
                                    lambda: button.click(),
                                    lambda: self.driver.execute_script("arguments[0].click();", button),
                                    lambda: webdriver.ActionChains(self.driver).move_to_element(button).click().perform()
                                ]:
                                    try:
                                        self.driver.execute_script(
                                            "arguments[0].scrollIntoView({block: 'center'});", 
                                            button
                                        )
                                        time.sleep(0.5)
                                        click_method()
                                        
                                        # Validate new replies appeared
                                        try:
                                            WebDriverWait(self.driver, 3).until(
                                                lambda d: self._count_visible_comments() > current_count
                                            )
                                            new_count = self._count_visible_comments()
                                            added = new_count - current_count
                                            total_expanded += added
                                            print(f"🔄 Expanded {added} replies")
                                            click_success = True
                                            expansion_made = True
                                            break
                                        except TimeoutException:
                                            continue
                                            
                                    except Exception as e:
                                        logger.debug(f"Reply click failed: {e}")
                                        continue
                                
                                if click_success:
                                    break
                            
                            if expansion_made:
                                break
                                
                        except Exception as e:
                            logger.debug(f"Error expanding replies: {e}")
                            continue
                
                # If no expansion was made, we're done
                if not expansion_made:
                    logger.info("No more expandable comments found")
                    print("✅ No more comments to expand")
                    break
                
                # Small delay between iterations
                time.sleep(1)
            
            final_count = self._count_visible_comments()
            logger.info(f"Comment expansion complete. Started with {initial_comments}, ended with {final_count}")
            print(f"📊 Comment expansion summary:")
            print(f"   - Initial comments: {initial_comments}")
            print(f"   - Final comments: {final_count}")
            print(f"   - Total expanded: {total_expanded}")
            
        except Exception as e:
            logger.error(f"Error during comment expansion: {e}")
            print(f"⚠️ Error expanding comments: {str(e)}")
            
    def _count_visible_comments(self):
        """Helper method to count visible comments"""
        try:
            comment_selectors = [
                "//div[@role='article' and contains(@aria-label, 'comment')]",
                "//div[@data-testid='comment']",
                "//div[contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'comments-comment-item')]"
            ]
            
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    visible_elements = [e for e in elements if e.is_displayed()]
                    if visible_elements:
                        return len(visible_elements)
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            return 0
            
        except Exception as e:
            logger.error(f"Error counting comments: {e}")
            return 0
    def _extract_comment_elements(self, post_id, max_comments=50):
        """
        Extract comment data from expanded comment elements with robust handling
        - Uses multiple selectors for different Facebook layouts
        - Validates comment content before extraction
        - Handles stale elements and retries failed extractions
        - Provides detailed progress reporting
        
        Args:
            post_id: ID of the post
            max_comments: Maximum comments to extract
            
        Returns:
            list: List of comment dictionaries
        """
        try:
            # Multiple selectors for different Facebook layouts
            comment_selectors = [
                "//div[@role='article' and contains(@aria-label, 'comment')]",
                "//div[@data-testid='comment']", 
                "//div[contains(@class, 'comment') and .//span[@dir='auto']]",
                "//div[@aria-label='Comment']",
                "//div[contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'comments-comment-item')]",
                "//div[contains(@data-testid, 'UFI2Comment')]"
            ]
            
            # Try each selector with WebDriverWait
            wait = WebDriverWait(self.driver, 5)
            comment_elements = []
            successful_selector = None
            
            for selector in comment_selectors:
                try:
                    # Wait for comments to be present and visible
                    elements = wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    
                    # Filter for visible elements only
                    visible_elements = [e for e in elements if e.is_displayed()]
                    
                    if visible_elements:
                        comment_elements = visible_elements
                        successful_selector = selector
                        print(f"📋 Found {len(visible_elements)} visible comment elements")
                        logger.info(f"Found comments using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not comment_elements:
                print("⚠️ No comment elements found")
                return []
            
            # Take screenshot of found comments
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = DEBUG_DIR / f"comments_found_{post_id}_{timestamp}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Extract data from each comment
            comments = []
            retries = {}  # Track retry counts per comment
            
            for i, comment_elem in enumerate(comment_elements[:max_comments], 1):
                success = False
                retry_count = retries.get(id(comment_elem), 0)
                
                while not success and retry_count < 3:
                    try:
                        comment_data = self._extract_single_comment(comment_elem, post_id, i)
                        
                        if comment_data and self._validate_comment(comment_data):
                            # Add extraction timestamp
                            comment_data['extracted_at'] = datetime.now()
                            comments.append(comment_data)
                            success = True
                            
                            # Show progress
                            if i % 5 == 0 or i == len(comment_elements[:max_comments]):
                                print(f"📝 Extracted {i}/{min(len(comment_elements), max_comments)} comments...")
                            
                        else:
                            retry_count += 1
                            retries[id(comment_elem)] = retry_count
                            if retry_count < 3:
                                logger.debug(f"Retrying comment {i} (attempt {retry_count + 1})")
                                time.sleep(0.5)
                            
                    except StaleElementReferenceException:
                        # Element went stale, try to re-find it
                        try:
                            logger.debug(f"Re-finding stale comment element {i}")
                            comment_elem = wait.until(
                                EC.presence_of_element_located(
                                    (By.XPATH, f"({successful_selector})[{i}]")
                                )
                            )
                            retry_count += 1
                            retries[id(comment_elem)] = retry_count
                            if retry_count >= 3:
                                logger.warning(f"Failed to extract comment {i} after {retry_count} retries (stale element)")
                                break
                        except Exception as e:
                            logger.error(f"Error re-finding stale element: {e}")
                            break
                        
                    except Exception as e:
                        logger.warning(f"Error extracting comment {i}: {e}")
                        retry_count += 1
                        retries[id(comment_elem)] = retry_count
                        if retry_count >= 3:
                            logger.warning(f"Failed to extract comment {i} after {retry_count} retries")
                            break
                        time.sleep(0.5)
            
            # Report results
            if comments:
                logger.info(f"Successfully extracted {len(comments)} comments")
                failed = len(comment_elements[:max_comments]) - len(comments)
                if failed > 0:
                    logger.warning(f"Failed to extract {failed} comments")
                    print(f"⚠️ Note: {failed} comments could not be extracted")
            else:
                logger.warning("No comments were successfully extracted")
                print("❌ Failed to extract any comments")
            
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
            print(f"❌ Error during comment extraction: {str(e)}")
            return []
            
    def _validate_comment(self, comment_data):
        """
        Validate extracted comment data
        
        Args:
            comment_data: Dictionary containing comment data
            
        Returns:
            bool: Whether the comment data is valid
        """
        try:
            # Must have post_id
            if not comment_data.get('post_id'):
                return False
                
            # Must have either author or text (preferably both)
            has_author = bool(comment_data.get('author') and 
                            len(comment_data['author'].strip()) > 1)
            has_text = bool(comment_data.get('text') and 
                          len(comment_data['text'].strip()) > 1)
            
            if not (has_author or has_text):
                return False
            
            # If we have text, it should look reasonable
            if has_text:
                text = comment_data['text']
                # Check text isn't just punctuation/spaces
                if not any(c.isalnum() for c in text):
                    return False
                # Flag suspicious text
                if len(text) < 2 or text.count('\n') > 10:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating comment: {e}")
            return False
    
    def _extract_single_comment(self, comment_elem, post_id, comment_index):
        """Extract data from a single comment element"""
        try:
            # Extract author
            author = "Unknown"
            author_selectors = [
                ".//a[@role='link']//span",
                ".//h3//a",
                ".//strong",
                ".//span[contains(@class, 'fwb')]",
                ".//a[contains(@href, 'facebook.com')]"
            ]
            
            for selector in author_selectors:
                try:
                    author_elem = comment_elem.find_element(By.XPATH, selector)
                    if author_elem and author_elem.text.strip():
                        author = author_elem.text.strip()
                        break
                except:
                    continue
            
            # Extract comment text
            text = ""
            text_selectors = [
                ".//div[@dir='auto' and @style]",
                ".//span[@dir='auto']",
                ".//div[contains(@class, 'userContent')]",
                ".//div[@data-testid='comment-content']"
            ]
            
            for selector in text_selectors:
                try:
                    text_elem = comment_elem.find_element(By.XPATH, selector)
                    if text_elem and text_elem.text.strip():
                        text = text_elem.text.strip()
                        break
                except:
                    continue
            
            # If no text found, get all text and clean it
            if not text:
                try:
                    all_text = comment_elem.text
                    if author in all_text:
                        text = all_text.replace(author, "", 1).strip()
                    else:
                        text = all_text.strip()
                except:
                    text = ""
            
            # Skip if no meaningful text
            if not text or len(text) < 2:
                return None
            
            # Extract likes (optional)
            likes = 0
            try:
                like_elements = comment_elem.find_elements(By.XPATH, ".//span[contains(@aria-label, 'like') or contains(text(), 'Like')]")
                for elem in like_elements:
                    like_text = elem.get_attribute('aria-label') or elem.text
                    if like_text:
                        like_match = re.search(r'(\d+)', like_text)
                        if like_match:
                            likes = int(like_match.group(1))
                            break
            except:
                pass
            
            comment_data = {
                'post_id': post_id,
                'author': author,
                'text': text,
                'likes': likes,
                'comment_time': datetime.now(),
                'extracted_at': datetime.now()
            }
            
            return comment_data
        except Exception as e:
            logger.warning(f"Error extracting single comment: {e}")
            return None
    
    def _expand_comments(self, expected_count=0):
        """
        Expand all comments and replies
        
        Args:
            expected_count (int): Expected number of comments to find
        """
        try:
            print("Expanding comments and replies...")
            
            # Take debug screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = DEBUG_DIR / f"before_expand_comments_{timestamp}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Track clicks for reporting
            total_clicks = 0
            max_attempts = 10  # Maximum number of attempts to expand comments
            
            # Set click limit based on expected count or max_comments setting
            if expected_count > 0:
                estimated_clicks = expected_count // 10 + 5  # Rough estimate: about 10 comments per click plus some for replies
                max_clicks = min(estimated_clicks * 2, 50)  # Double to ensure we get enough, but cap at 50
            else:
                max_clicks = 30  # Default max clicks
            
            # Loop multiple times to make sure we expand all nested levels
            for attempt in range(max_attempts):
                if total_clicks >= max_clicks:
                    logger.info(f"Reached maximum click limit ({max_clicks}), stopping comment expansion")
                    break
                
                current_clicks = 0
                
                # First, try to expand "View more comments" buttons
                view_more_selectors = [
                    "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View previous comments')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View more comments')]",
                    "//div[@role='button' and contains(., 'View previous comments')]",
                    "//div[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]",
                    "//span[contains(text(), 'View') and contains(text(), 'comment')]/ancestor::*[1]",
                    "//div[contains(@class, 'UFIPagerLink')]",
                    "//a[contains(@class, 'UFIPagerLink')]",
                    "//a[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]"
                ]
                
                for selector in view_more_selectors:
                    try:
                        more_buttons = self.driver.find_elements(By.XPATH, selector)
                        if more_buttons:
                            for button in more_buttons:
                                try:
                                    if button.is_displayed() and button.is_enabled():
                                        # Scroll to button to make it clickable
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                        time.sleep(1)
                                        
                                        # Click using JavaScript to avoid ElementClickInterceptedException
                                        self.driver.execute_script("arguments[0].click();", button)
                                        current_clicks += 1
                                        total_clicks += 1
                                        
                                        logger.info(f"Clicked 'View more comments' button ({total_clicks}/{max_clicks})")
                                        time.sleep(2)  # Wait for comments to load
                                        
                                        # Break after each click to re-find buttons (DOM changes)
                                        break
                                except Exception as e:
                                    logger.warning(f"Error clicking 'View more comments' button: {e}")
                    except Exception as e:
                        logger.warning(f"Error with selector '{selector}': {e}")
                
                # Next, try to expand replies
                reply_selectors = [
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                    "//div[contains(text(), 'View') and contains(text(), 'repl')]",
                    "//a[contains(text(), 'View') and contains(text(), 'repl')]",
                    "//a[contains(@class, 'UFIReplyList')]",
                    "//div[contains(@class, 'UFIReplyList')]"
                ]
                
                for selector in reply_selectors:
                    try:
                        reply_buttons = self.driver.find_elements(By.XPATH, selector)
                        if reply_buttons:
                            for button in reply_buttons:
                                try:
                                    if button.is_displayed() and button.is_enabled():
                                        # Scroll to button
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                        time.sleep(1)
                                        
                                        # Click using JavaScript
                                        self.driver.execute_script("arguments[0].click();", button)
                                        current_clicks += 1
                                        total_clicks += 1
                                        
                                        logger.info(f"Clicked 'View replies' button ({total_clicks}/{max_clicks})")
                                        time.sleep(2)  # Wait for replies to load
                                        
                                        # Break after each click to re-find buttons
                                        break
                                except Exception as e:
                                    logger.warning(f"Error clicking 'View replies' button: {e}")
                    except Exception as e:
                        logger.warning(f"Error with selector '{selector}': {e}")
                
                # Stop if we didn't click anything in this round
                if current_clicks == 0:
                    logger.info("No more expandable comments or replies found")
                    break
                
                # Count existing comments to see if we have enough
                if expected_count > 0:
                    comment_selectors = [
                        "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
                        "//div[contains(@class, 'comments-comment-item')]",
                        "//div[contains(@data-testid, 'UFI2Comment')]",
                        "//div[@data-testid='comment']"
                    ]
                    
                    for selector in comment_selectors:
                        try:
                            comments = self.driver.find_elements(By.XPATH, selector)
                            if comments and len(comments) >= expected_count:
                                logger.info(f"Found {len(comments)} comments, which meets or exceeds expected count {expected_count}")
                                return
                        except:
                            pass
            
            logger.info(f"Finished expanding comments after {total_clicks} clicks")
            
        except Exception as e:
            logger.error(f"Error expanding comments: {e}")
    
    def save_post_to_database(self, post_data, images=None, comments=None):
        """
        Save post data to the database
        
        Args:
            post_data (dict): Post data dictionary
            images (list): List of image data dictionaries
            comments (list): List of comment data dictionaries
            
        Returns:
            bool: Whether the save was successful
        """
        try:
            # Make sure we have valid post data
            if not post_data or not post_data.get('post_id'):
                logger.warning("Invalid post data for database save")
                return False
            
            result = self.db.save_post(post_data, images, comments)
            
            if result:
                logger.info(f"Successfully saved post {post_data.get('post_id')} to database")
                return True
            else:
                logger.warning(f"Failed to save post {post_data.get('post_id')} to database")
                return False
                
        except Exception as e:
            logger.error(f"Error saving post to database: {e}")
            return False
    
    def smart_scrape_page(self, page_name, max_posts=10):
        """
        Intelligently scrape posts with smart handling of comments
        
        Args:
            page_name (str): Name or URL of the Facebook page
            max_posts (int): Maximum number of posts to scrape (0 = all)
            
        Returns:
            tuple: (posts_data, total_images, total_comments)
        """
        if not self.driver:
            self.start()
        
        if not self.driver:
            logger.error("Browser not initialized")
            return None
        
        try:
            # Make sure we're logged in
            if not self.logged_in and not self._check_login_status():
                if not self.manual_login():
                    logger.error("Not logged in to Facebook")
                    return None
            
            # Navigate to the page
            if not self.navigate_to_page(page_name):
                logger.error(f"Failed to navigate to page: {page_name}")
                return None
            
            # Scroll to load posts
            logger.info(f"Scrolling for posts on {page_name}...")
            post_elements = self.scroll_page_for_posts(max_posts)
            
            if not post_elements:
                logger.warning(f"No posts found on page: {page_name}")
                return None
            
            logger.info(f"Found {len(post_elements)} posts on {page_name}")
            
            # Process each post
            posts_data = []
            total_images = 0
            total_comments = 0
            
            for i, post_element in enumerate(post_elements, 1):
                logger.info(f"Processing post {i}/{len(post_elements)} from {page_name}")
                
                # First, check if post has comments
                has_comments_flag, comment_count = self.has_comments(post_element)
                
                # Extract basic post data
                post_data = self.extract_post_data(post_element, page_name)
                if not post_data:
                    continue
                
                # If post has comments and URL, extract them
                comments = []
                if has_comments_flag and post_data.get('post_url'):
                    print(f"Post has {comment_count} comments. Extracting...")
                    try:
                        # Store the expected count
                        post_data['comments_count'] = comment_count
                        
                        # Extract comments
                        comments = self.extract_comments(post_data)
                        print(f"  ✓ Found {len(comments)} comments")
                        
                        # Update post's comment count to match what we actually found
                        post_data['comments_count'] = len(comments)
                        total_comments += len(comments)
                    except Exception as e:
                        logger.error(f"Error in comment extraction: {e}")
                        print(f"  ❌ Error extracting comments: {e}")
                
                # Save post data to database
                saved = self.save_post_to_database(post_data, images=None, comments=comments)
                
                if saved:
                    logger.info(f"Post {post_data.get('post_id')} saved successfully")
                else:
                    logger.warning(f"Post {post_data.get('post_id')} could not be saved")
            
            return posts_data, total_images, total_comments
            
        except Exception as e:
            logger.error(f"Error scraping page {page_name}: {e}")
            return None

def read_pages_from_file(file_path):
    """Read Facebook page names from a file"""
    pages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove comments and whitespace
                line = line.split('#')[0].strip()
                if line:
                    pages.append(line)
        return pages
    except Exception as e:
        logger.error(f"Error reading pages from file {file_path}: {e}")
        return []

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Smart Facebook Scraper')
    parser.add_argument('--pages', nargs='+', help='List of Facebook page names to scrape')
    parser.add_argument('--pages-file', type=str, default='pages.txt',
                        help='File containing list of Facebook page names (one per line)')
    parser.add_argument('--max-posts', type=int, default=10,
                        help='Maximum number of posts to scrape per page (0 = all)')
    parser.add_argument('--max-comments', type=int, default=50,
                        help='Maximum number of comments to extract per post (0 = all)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no UI)')
    parser.add_argument('--no-images', action='store_true',
                        help='Do not download images')
    parser.add_argument('--no-screenshots', action='store_true',
                        help='Do not take screenshots of posts')
    parser.add_argument('--wait-time', type=int, default=300,
                        help='Maximum time to wait for manual login (seconds)')
    return parser.parse_args()

def main():
    """Main function"""
    # Check if Selenium is available
    if not SELENIUM_AVAILABLE:
        print("Error: Selenium is required but not installed.")
        print("Please run: pip install selenium webdriver-manager")
        return 1
        
    # Parse command line arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("SMART FACEBOOK SCRAPER")
    print("="*80)
    print("Features:")
    print("✓ Intelligent post detection and screenshot capture")
    print("✓ Comment detection and smart extraction")
    print("✓ Automatic post navigation for comment scraping")
    print("✓ Post metadata extraction (likes, shares, etc.)")
    print("✓ PostgreSQL database storage")
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
    print(f"Max comments per post: {args.max_comments if args.max_comments > 0 else 'All'}")
    print(f"Take screenshots: {'No' if args.no_screenshots else 'Yes'}")
    print(f"Headless mode: {'Yes' if args.headless else 'No'}")
    
    # Initialize scraper
    print("\nInitializing Facebook scraper...")
    scraper = SmartFacebookScraper(
        headless=args.headless,
        wait_time=args.wait_time,
        download_images=(not args.no_images),
        take_screenshots=(not args.no_screenshots),
        max_comments=args.max_comments
    )
    
    try:
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
                print(f"   - {images_count} images/screenshots captured")
                print(f"   - {comments_count} comments extracted")
            else:
                print(f"\n❌ Failed to scrape page: {page_name}")
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total pages scraped: {len(pages_to_scrape)}")
        print(f"Total posts scraped: {total_posts}")
        print(f"Total images/screenshots captured: {total_images}")
        print(f"Total comments extracted: {total_comments}")
        print("="*50)
        
        if total_comments == 0:
            print("\n⚠️ WARNING: No comments were extracted. Possible issues:")
            print("  1. Comments might be disabled or hidden on these pages/posts")
            print("  2. Facebook's layout might have changed")
            print("  3. Login session might not have proper access to comments")
        
        print("\n✅ Smart scraping completed successfully!")
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
