from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class EdgeFacebookScraper:
    """Edge-based Facebook scraper with improved selectors and BeautifulSoup parsing"""
    def __init__(self, email: str = "", password: str = "", max_posts: int = 100,
                 take_screenshots: bool = True, download_images: bool = True):
        """
        Initialize the Edge-based Facebook scraper
        
        Args:
            email: Facebook login email (optional for manual login)
            password: Facebook login password (optional for manual login)
            max_posts: Maximum number of posts to scrape
            take_screenshots: Whether to capture screenshots
            download_images: Whether to download images
        """
        self.email = email
        self.password = password
        self.driver = None
        self.max_posts = max_posts
        self.take_screenshots = take_screenshots
        self.download_images = download_images
        self.screenshots_dir = Path("screenshots")
        self.images_dir = Path("images")
        
        # Create directories if they don't exist
        if self.take_screenshots:
            self.screenshots_dir.mkdir(exist_ok=True)
        if self.download_images:
            self.images_dir.mkdir(exist_ok=True)
            
    def initialize_driver(self):
        """Initialize the Edge webdriver with anti-detection measures"""
        try:
            options = webdriver.EdgeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            self.driver = webdriver.Edge(options=options)
            # Mask webdriver presence
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("EdgeDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize EdgeDriver: {e}")
            return False
            
    def simulate_human_typing(self, element, text: str):
        """Simulate human-like typing patterns with random delays"""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
                if random.random() < 0.1:  # 10% chance of longer pause
                    time.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.error(f"Error during typing simulation: {e}")
            raise
                
    def verify_login(self) -> bool:
        """Verify if user is logged in to Facebook"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Try different elements that indicate successful login
            selectors = [
                '[aria-label="Home"]',
                '[aria-label="Facebook"]',
                '[role="main"]',
                '[role="feed"]',
                'div[role="navigation"]',
                'div[aria-label="Facebook"]',
                'div[aria-label="Menu"]',
                'div[data-pagelet="Stories"]'
            ]
            
            # Check if we're on login page
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "welcome" in current_url:
                logger.debug("On login page, not logged in")
                return False
                
            # Try each selector
            for selector in selectors:
                try:
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if element.is_displayed():
                        logger.info(f"Found login indicator: {selector}")
                        return True
                except Exception:
                    continue
                    
            # Final check for login button
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="royal_login_button"]')
                if login_button.is_displayed():
                    return False
            except:
                if "facebook.com" in current_url:
                    logger.info("No login button found and on Facebook - assuming logged in")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error verifying login: {e}")
            return False
            
    def manual_login(self) -> bool:
        """Handle manual login with progress indication"""
        if not self.driver:
            self.initialize_driver()
            
        try:
            self.driver.get("https://www.facebook.com")
            
            print("\n" + "="*80)
            print(" "*30 + "MANUAL LOGIN REQUIRED")
            print("="*80)
            print("1. Log in to Facebook with your credentials in the browser window")
            print("2. Complete any security checks if prompted")
            print("3. Return to this terminal when logged in")
            print("4. Type 'done' when you're finished (the scraper will verify login)")
            print("="*80 + "\n")
            
            max_attempts = 60
            attempt = 0
            
            while attempt < max_attempts:
                if self.verify_login():
                    print("\nLogin detected automatically!")
                    logger.info("Login successful - auto-detected")
                    return True
                    
                import sys, select
                if select.select([sys.stdin], [], [], 0)[0]:
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == "done":
                        print("\nVerifying login...")
                        time.sleep(2)
                        if self.verify_login():
                            print("Login successful!")
                            logger.info("Login successful - user confirmed")
                            return True
                        else:
                            print("\nLogin verification failed. Please check if you're properly logged in.")
                            print("Type 'done' when ready, or wait for auto-detection.")
                            
                time.sleep(1)
                attempt += 1
                
                if attempt % 10 == 0:
                    print(f"Waiting for login... ({int((max_attempts-attempt)/2)} seconds remaining)")
                    
            print("\nLogin timeout reached. Please try again.")
            return False
            
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            print(f"Failed to log in to Facebook: {e}")
            return False
            
    def login(self) -> bool:
        """Login to Facebook with error handling"""
        try:
            logger.info("Attempting to log in to Facebook...")
            self.driver.get("https://www.facebook.com/login")
            
            if not self.email or not self.password:
                return self.manual_login()
                
            # Automated login with provided credentials
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            self.simulate_human_typing(email_input, self.email)
            
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "pass"))
            )
            self.simulate_human_typing(password_input, self.password)
            
            # Click login button with human-like movement
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            ActionChains(self.driver)\
                .move_to_element(login_button)\
                .pause(random.uniform(0.2, 0.4))\
                .click()\
                .perform()
                
            # Wait longer for login to complete and verify
            time.sleep(15)
            
            return True
                
        except Exception as e:
            logger.error(f"Login failed with error: {e}")
            return False
        
    def navigate_to_profile(self, profile_url: str):
        """Navigate to a Facebook profile or page"""
        try:
            # Make sure we have a full URL
            if not profile_url.startswith('http'):
                if 'profile.php?id=' in profile_url:
                    profile_url = f"https://www.facebook.com/{profile_url}"
                else:
                    profile_url = f"https://www.facebook.com/{profile_url}"
                    
            logger.info(f"Navigating to: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(4)  # Wait for page load
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {profile_url}: {e}")
            return False
        
    def slow_scroll(self, step: int = 500):
        """Scroll the page slowly with human-like behavior"""
        try:
            # Random scroll speed
            actual_step = step + random.randint(-50, 50)
            self.driver.execute_script(f"window.scrollBy(0, {actual_step});")
            # Random wait between scrolls
            time.sleep(random.uniform(1.5, 2.5))
        except Exception as e:
            logger.error(f"Error during scroll: {e}")
        
    def extract_posts_with_bs(self) -> List[Dict[str, Any]]:
        """Extract posts data using BeautifulSoup with improved selectors"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            posts_data = []
            
            # Updated class selector for posts
            posts = soup.find_all("div", {"class": "x1n2onr6 x1ja2u2z"})
            
            logger.info(f"Found {len(posts)} potential posts")
            
            for idx, post in enumerate(posts, 1):
                try:
                    # Extract post text
                    message_elements = post.find_all("div", {"data-ad-preview": "message"})
                    post_text = " ".join([msg.get_text(strip=True) for msg in message_elements])
                    
                    # Extract engagement metrics with better error handling
                    likes_element = post.select_one("span.xt0b8zv.x1jx94hy.xrbpyxo.xl423tq > span > span")
                    likes = likes_element.get_text(strip=True) if likes_element else None
                    
                    comments_element = post.select("div > div > span > div > div > div > span > span.html-span ")
                    comments = comments_element[0].text if comments_element else None
                    
                    shares_element = post.select("div > div > span > div > div > div > span > span.html-span ")
                    shares = shares_element[1].text if len(shares_element) > 1 else None
                    
                    time_element = post.select_one("div.xu06os2.x1ok221b > span > div > span > span > a > span")
                    post_time = time_element.get_text(strip=True) if time_element else None
                    
                    # Get post URL if available
                    post_url = None
                    url_element = post.select_one("div.xu06os2.x1ok221b > span > div > span > span > a")
                    if url_element and 'href' in url_element.attrs:
                        post_url = url_element['href']
                        if not post_url.startswith('http'):
                            post_url = f"https://www.facebook.com{post_url}"
                    
                    # Extract images if enabled
                    images = []
                    if self.download_images:
                        img_elements = post.select("img[src*='scontent']")
                        for img in img_elements:
                            if 'src' in img.attrs:
                                images.append({
                                    'url': img['src'],
                                    'alt': img.get('alt', ''),
                                    'downloaded_at': datetime.now().isoformat()
                                })
                    
                    # Take screenshot if enabled
                    screenshot_path = None
                    if self.take_screenshots and idx <= self.max_posts:
                        try:
                            post_elem = self.driver.find_elements(By.CLASS_NAME, "x1n2onr6.x1ja2u2z")[idx-1]
                            screenshot = post_elem.screenshot_as_png
                            screenshot_path = self.screenshots_dir / f"post_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            with open(screenshot_path, 'wb') as f:
                                f.write(screenshot)
                        except Exception as e:
                            logger.warning(f"Failed to capture screenshot for post {idx}: {e}")
                    
                    post_data = {
                        "post_text": post_text,
                        "likes": likes,
                        "comments": comments,
                        "shares": shares,
                        "post_time": post_time,
                        "post_url": post_url,
                        "images": images,
                        "screenshot_path": str(screenshot_path) if screenshot_path else None,
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    posts_data.append(post_data)
                    logger.debug(f"Extracted data for post {idx}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting post {idx} data: {e}")
                    continue
                    
            return posts_data
            
        except Exception as e:
            logger.error(f"Error during post extraction: {e}")
            return []
        
    def remove_duplicates(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on content"""
        seen = set()
        unique_data = []
        for data in data_list:
            # Create a tuple of key fields for comparison
            key_data = (
                data['post_text'],
                data['post_time'],
                data['post_url']
            )
            if key_data not in seen:
                seen.add(key_data)
                unique_data.append(data)
        return unique_data
        
    def scrape_posts(self, profile_url: str, max_posts: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape posts from a Facebook profile or page
        
        Args:
            profile_url: URL of the Facebook profile/page
            max_posts: Optional override for maximum posts to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        if max_posts is not None:
            self.max_posts = max_posts
            
        all_posts = []
        retry_count = 0
        max_retries = 3
        
        try:
            if not self.navigate_to_profile(profile_url):
                return []
            
            while len(all_posts) < self.max_posts and retry_count < max_retries:
                try:
                    posts = self.extract_posts_with_bs()
                    all_posts.extend(posts)
                    all_posts = self.remove_duplicates(all_posts)
                    logger.info(f"Extracted {len(all_posts)} unique posts so far.")
                    
                    if len(all_posts) >= self.max_posts:
                        break
                        
                    if not posts:  # No new posts found
                        retry_count += 1
                        logger.debug(f"No new posts found (attempt {retry_count}/{max_retries})")
                    else:
                        retry_count = 0  # Reset retry count if we found posts
                        
                    self.slow_scroll()
                    
                except Exception as e:
                    logger.error(f"Error during scraping: {e}")
                    retry_count += 1
                    
            return all_posts[:self.max_posts]
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}")
            return []
            
    def print_posts(self, posts_data: List[Dict[str, Any]]):
        """Print scraped posts data in a formatted way"""
        for idx, post in enumerate(posts_data, start=1):
            print(f"\nPost {idx}:")
            print("-" * 50)
            print(f"Text: {post['post_text']}")
            print(f"Likes: {post['likes']}")
            print(f"Comments: {post['comments']}")
            print(f"Shares: {post['shares']}")
            print(f"Time Posted: {post['post_time']}")
            if post['post_url']:
                print(f"URL: {post['post_url']}")
            if post['images']:
                print(f"Images: {len(post['images'])} found")
            if post['screenshot_path']:
                print(f"Screenshot saved: {post['screenshot_path']}")
            print("-" * 50)
            
    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
