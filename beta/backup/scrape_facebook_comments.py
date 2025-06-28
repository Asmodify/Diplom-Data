#!/usr/bin/env python
"""
Facebook Comment Scraper
Focused script for scraping comments from Facebook posts already in the database
"""

import sys
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
import re

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR, DEBUG_DIR
from db.models import FacebookPost, PostComment

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'comment_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CommentScraper:
    """Facebook Comment Scraper"""
    
    def __init__(self, headless=False, comment_limit=0):
        """Initialize the scraper"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required but not installed. Please install selenium package.")
        
        self.headless = headless
        self.comment_limit = comment_limit  # 0 means all comments
        
        self.driver = None
        self.db = DatabaseManager()
        self.logged_in = False
        
        # Create directories
        LOGS_DIR.mkdir(exist_ok=True)
        DEBUG_DIR.mkdir(exist_ok=True)
    
    def setup_driver(self):
        """Initialize Firefox driver"""
        logger.info("Setting up Firefox driver...")
        
        try:
            # Configure Firefox options
            options = FirefoxOptions()
            options.set_preference("dom.webnotifications.enabled", False)  # Disable notifications
            options.headless = self.headless  # Set headless mode
            
            # Try with WebDriver Manager if available
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            else:
                # Fallback to local driver
                driver = webdriver.Firefox(options=options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            logger.info("Firefox browser set up successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Error setting up Firefox browser: {e}")
            # Save error log
            error_log_path = DEBUG_DIR / f"browser_error_{int(time.time())}.txt"
            with open(error_log_path, "w") as f:
                f.write(f"Error setting up browser: {str(e)}\n")
                
            print(f"Error setting up browser: {e}")
            print(f"Error details saved to {error_log_path}")
            return None
    
    def start(self):
        """Start the browser session"""
        if not self.driver:
            self.driver = self.setup_driver()
            if not self.driver:
                raise RuntimeError("Failed to initialize browser session")
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser closed")
    
    def save_debug_info(self, filename_prefix):
        """Save current page source and screenshot for debugging"""
        if not self.driver:
            return None, None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML
        html_path = DEBUG_DIR / f"{filename_prefix}_{timestamp}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        
        # Save screenshot
        screenshot_path = DEBUG_DIR / f"{filename_prefix}_{timestamp}.png"
        self.driver.save_screenshot(str(screenshot_path))
        
        logger.info(f"Saved debug info: {html_path.name} and {screenshot_path.name}")
        return html_path, screenshot_path
    
    def manual_login(self):
        """Perform manual login to Facebook"""
        if not self.driver:
            self.start()
            
        try:
            # Navigate to Facebook
            logger.info("Navigating to Facebook login page...")
            self.driver.get("https://www.facebook.com/")
            time.sleep(3)
            
            # Check if already logged in
            if self._check_login_status():
                logger.info("Already logged in to Facebook")
                print("\n✅ Already logged in to Facebook! Proceeding...")
                self.logged_in = True
                return True
            
            # Otherwise, display manual login instructions
            print("\n" + "="*80)
            print("MANUAL LOGIN REQUIRED")
            print("="*80)
            print("1. Log in to Facebook with your credentials in the browser window")
            print("2. Complete any security checks if prompted")
            print("3. Return to this terminal when logged in")
            print("4. Type 'done' and press Enter to continue")
            print("="*80)
            
            # Give user time to log in manually
            print("Please log in to Facebook and type 'done' when finished...")
            user_input = input("After logging in, type 'done' here: ").strip().lower()
            
            # Short pause to let any redirects/page loads complete
            time.sleep(5)
            
            # Final login check
            if self._check_login_status():
                logger.info("Successfully logged in to Facebook")
                print("\n✅ Login successful! Proceeding...")
                self.logged_in = True
                self.save_debug_info("login_success")
                return True
            else:
                logger.warning("Login not confirmed after waiting")
                print("\n❌ Login not confirmed after waiting. Please try again.")
                return False
                
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            print(f"\n❌ Error during login: {e}")
            return False
    
    def _check_login_status(self):
        """Check if currently logged in to Facebook"""
        try:
            # Look for elements that indicate logged-in state
            elements = self.driver.find_elements(By.XPATH, 
                "//div[@role='navigation'] | //div[@aria-label='Facebook'] | //div[contains(@class, 'userNav')]")
            
            # Also check for elements that indicate NOT logged in
            login_elements = self.driver.find_elements(By.XPATH, "//input[@name='email'] | //input[@name='pass']")
            
            return len(elements) > 0 and len(login_elements) == 0
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def expand_comments(self, limit=0):
        """Expand all comments and replies"""
        try:
            print("Expanding comments and replies...")
            # Take debug screenshot
            self.save_debug_info("before_expand_comments")
            
            # Track clicks for reporting
            total_clicks = 0
            max_attempts = 10  # Maximum number of attempts to expand comments
            max_clicks = 200 if limit == 0 else 50  # Limit clicks if we're only getting a sample
            
            # Loop multiple times to make sure we expand all nested levels
            for attempt in range(max_attempts):
                if total_clicks >= max_clicks:
                    logger.info(f"Reached maximum click limit ({max_clicks}), stopping comment expansion")
                    break
                
                current_clicks = 0
                
                # Try to expand more comments with updated selectors for 2025 Facebook
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
                    more_buttons = self.driver.find_elements(By.XPATH, selector)
                    if more_buttons:
                        for button in more_buttons[:5]:  # Limit to 5 buttons per selector to avoid infinite loops
                            try:
                                # Scroll to button
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                # Click button
                                self.driver.execute_script("arguments[0].click();", button)
                                current_clicks += 1
                                total_clicks += 1
                                time.sleep(2)  # Wait for comments to load
                                
                                if total_clicks >= max_clicks:
                                    break
                            except:
                                pass
                        
                        if total_clicks >= max_clicks:
                            break
                
                # Try to expand replies with updated selectors for 2025 Facebook
                reply_selectors = [
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                    "//a[contains(text(), 'View') and contains(text(), 'repl')]",
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/..",
                    "//span[contains(text(), 'Reply') or contains(text(), 'Replies')]/ancestor::div[@role='button']",
                    "//div[contains(@class, 'UFIReplyList')]//a[contains(text(), 'View')]"
                ]
                
                for selector in reply_selectors:
                    reply_buttons = self.driver.find_elements(By.XPATH, selector)
                    if reply_buttons:
                        for button in reply_buttons[:5]:  # Limit to 5 buttons per selector
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", button)
                                current_clicks += 1
                                total_clicks += 1
                                time.sleep(1.5)
                                
                                if total_clicks >= max_clicks:
                                    break
                            except:
                                pass
                        
                        if total_clicks >= max_clicks:
                            break
                
                # If no clicks were made in this round, we might be done
                if current_clicks == 0:
                    if attempt >= 2:  # Make sure we've made at least 3 attempts
                        break
                
                # Scroll down a bit to load more content
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
            logger.info(f"Comment expansion completed with {total_clicks} total clicks")
            self.save_debug_info("after_expand_comments")
            
        except Exception as e:
            logger.error(f"Error expanding comments: {e}")
            self.save_debug_info("error_expand_comments")
    
    def extract_comments(self, post_data):
        """Extract comments from a post"""
        if not post_data or not post_data.get('post_url'):
            return []
        
        try:
            # Navigate to post URL to get comments
            logger.info(f"Navigating to post to extract comments: {post_data['post_id']}")
            print(f"Navigating to post URL: {post_data['post_url']}")
            self.driver.get(post_data['post_url'])
            time.sleep(5)  # Wait for page to load
            
            # Expand comments
            self.expand_comments(self.comment_limit)
            
            # Save debug info to analyze the page structure
            self.save_debug_info(f"comments_page_{post_data['post_id']}")
            
            # Extract comments with updated selectors for 2025 Facebook layout
            comment_selectors = [
                "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'comments-comment-item')]",
                "//div[contains(@data-testid, 'UFI2Comment')]",
                "//div[@data-testid='comment']",
                "//div[@role='article' and contains(@class, 'comment')]",
                "//div[contains(@class, 'commentable_item')]"
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    comment_elements = elements
                    logger.info(f"Found comments using selector: {selector}")
                    print(f"Found {len(elements)} comments using selector: {selector}")
                    break
            
            if not comment_elements:
                logger.info(f"No comments found for post {post_data['post_id']}")
                print(f"No comments found for post {post_data['post_id']}")
                return []
            
            logger.info(f"Found {len(comment_elements)} comments for post {post_data['post_id']}")
            print(f"Found {len(comment_elements)} comments for post {post_data['post_id']}")
            
            # Process each comment
            comments = []
            for comment in comment_elements:
                try:
                    # Extract comment author with updated selectors
                    author = "Unknown"
                    author_selectors = [
                        ".//a[contains(@class, 'UFIComment') or @role='link' or contains(@href, 'facebook.com')]",
                        ".//span[contains(@class, 'author') or contains(@class, 'user')]",
                        ".//h3[contains(@class, 'actor')]",
                        ".//a[contains(@class, 'actor')]",
                        ".//a[@data-hovercard]", 
                        ".//strong"
                    ]
                    
                    for selector in author_selectors:
                        author_elements = comment.find_elements(By.XPATH, selector)
                        if author_elements and author_elements[0].text:
                            author = author_elements[0].text
                            break
                    
                    # Extract comment text with updated selectors
                    text = ""
                    text_selectors = [
                        ".//div[contains(@class, 'UFICommentBody') or @data-ad-comet-preview='message']",
                        ".//div[@data-testid='comment-content']",
                        ".//div[contains(@class, 'comment-content')]",
                        ".//div[contains(@class, 'commentText')]",
                        ".//span[@dir='auto']"
                    ]
                    
                    for selector in text_selectors:
                        text_elements = comment.find_elements(By.XPATH, selector)
                        if text_elements and text_elements[0].text:
                            text = text_elements[0].text
                            break
                    
                    # Skip empty comments
                    if not text:
                        continue
                    
                    # Extract likes
                    likes = 0
                    likes_elements = comment.find_elements(By.XPATH, 
                        ".//span[contains(@class, 'UFICommentLikeButton') or contains(text(), 'Like')]")
                    for likes_element in likes_elements:
                        likes_text = likes_element.get_attribute('aria-label') or likes_element.text
                        if likes_text and 'like' in likes_text.lower():
                            likes_match = re.search(r'(\d+)', likes_text)
                            if likes_match:
                                likes = int(likes_match.group(1))
                    
                    # Build comment data
                    comments.append({
                        'post_id': post_data['post_id'],
                        'author': author,
                        'text': text,
                        'likes': likes,
                        'comment_time': datetime.now(),  # Facebook doesn't show exact comment times easily
                        'extracted_at': datetime.now()
                    })
                    
                except Exception as e:
                    logger.warning(f"Error extracting a comment: {e}")
            
            print(f"Extracted {len(comments)} valid comments")
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments from post {post_data['post_id']}: {e}")
            self.save_debug_info(f"error_extracting_comments_{post_data['post_id']}")
            return []
    
    def save_comments(self, post_data, comments):
        """Save comments to the database"""
        if not comments:
            return False
        
        try:
            logger.info(f"Saving {len(comments)} comments for post {post_data['post_id']} to database")
            print(f"Saving {len(comments)} comments for post {post_data['post_id']} to database")
            
            # Debug first few comments
            for i, comment in enumerate(comments[:3]):
                if i < 3:  # Just log the first 3 comments
                    print(f"Comment {i+1}: {comment['author']} - {comment['text'][:30]}...")
            
            # Save to database
            result = self.db.save_post(post_data, [], comments)
            
            if result:
                logger.info(f"Successfully saved {len(comments)} comments for post {post_data['post_id']}")
                print(f"✅ Successfully saved {len(comments)} comments to database")
                return True
            else:
                logger.warning(f"Failed to save comments for post {post_data['post_id']}")
                print(f"❌ Failed to save comments to database")
                return False
                
        except Exception as e:
            logger.error(f"Error saving comments to database: {e}")
            print(f"❌ Error saving comments: {e}")
            return False
    
    def scrape_comments_for_post(self, post_data):
        """Scrape and save comments for a single post"""
        if not self.driver:
            self.start()
        
        try:
            # Make sure we're logged in
            if not self.logged_in and not self._check_login_status():
                if not self.manual_login():
                    logger.error("Not logged in to Facebook")
                    print("❌ Not logged in to Facebook. Cannot proceed.")
                    return False
            
            # Extract comments
            print(f"Extracting comments for post ID: {post_data['post_id']}")
            comments = self.extract_comments(post_data)
            
            if not comments:
                print(f"No comments found for post ID: {post_data['post_id']}")
                return False
            
            # Save comments to database
            return self.save_comments(post_data, comments)
            
        except Exception as e:
            logger.error(f"Error scraping comments for post {post_data['post_id']}: {e}")
            print(f"❌ Error: {e}")
            return False

def get_posts_from_database():
    """Get posts from the database"""
    try:
        db = DatabaseManager()
        posts = []
        
        with db.session_scope() as session:
            # Get latest posts with URLs but no comments
            posts_data = session.query(FacebookPost).filter(
                FacebookPost.post_url.isnot(None),
                FacebookPost.comments.any() == False  # No comments yet
            ).order_by(FacebookPost.extracted_at.desc()).limit(10).all()
            
            for post in posts_data:
                posts.append({
                    'post_id': post.post_id,
                    'page_name': post.page_name,
                    'post_url': post.post_url,
                    'post_text': post.post_text[:50] + '...' if post.post_text and len(post.post_text) > 50 else post.post_text
                })
        
        return posts
    except Exception as e:
        print(f"❌ Error getting posts from database: {e}")
        return []

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Facebook Comment Scraper')
    parser.add_argument('--post-id', type=str, help='Specific post ID to scrape comments for')
    parser.add_argument('--limit', type=int, default=0, help='Maximum number of comments to extract (0 = all)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (no UI)')
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
    
    # Initialize scraper
    print("\nInitializing Facebook Comment Scraper...")
    scraper = CommentScraper(
        headless=args.headless,
        comment_limit=args.limit
    )
    
    try:
        # Get posts to scrape
        if args.post_id:
            # Get specific post
            db = DatabaseManager()
            with db.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=args.post_id).first()
                
                if not post:
                    print(f"❌ Post with ID {args.post_id} not found in database")
                    return 1
                
                post_data = {
                    'post_id': post.post_id,
                    'page_name': post.page_name,
                    'post_url': post.post_url,
                    'post_text': post.post_text[:50] + '...' if post.post_text and len(post.post_text) > 50 else post.post_text
                }
                posts_to_scrape = [post_data]
        else:
            # Get posts with no comments yet
            posts_to_scrape = get_posts_from_database()
            
            if not posts_to_scrape:
                print("❌ No posts found in database without comments")
                return 1
        
        print(f"\nFound {len(posts_to_scrape)} posts to scrape for comments")
        
        # Perform manual login
        print("\nChecking login status...")
        if not scraper.manual_login():
            print("Login failed or was canceled. Cannot proceed.")
            return 1
        
        # Scrape comments for each post
        total_comments = 0
        success_count = 0
        
        for i, post in enumerate(posts_to_scrape, 1):
            print(f"\nProcessing post {i}/{len(posts_to_scrape)}: {post['post_id']}")
            print(f"URL: {post['post_url']}")
            print(f"Page: {post['page_name']}")
            print(f"Text: {post['post_text']}")
            
            if scraper.scrape_comments_for_post(post):
                success_count += 1
                # Count actual comments saved
                db = DatabaseManager()
                with db.session_scope() as session:
                    comment_count = session.query(PostComment).filter_by(post_id=post['post_id']).count()
                    total_comments += comment_count
            
            # Sleep between posts to avoid overloading
            if i < len(posts_to_scrape):
                print(f"Sleeping for 5 seconds before next post...")
                time.sleep(5)
        
        # Print summary
        print("\n" + "="*50)
        print("COMMENT SCRAPING SUMMARY")
        print("="*50)
        print(f"Posts processed: {len(posts_to_scrape)}")
        print(f"Posts with comments saved: {success_count}")
        print(f"Total comments extracted: {total_comments}")
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
