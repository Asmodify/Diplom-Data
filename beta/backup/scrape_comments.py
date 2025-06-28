#!/usr/bin/env python
"""
Enhanced Facebook Comment Scraper
This script specifically focuses on improved comment extraction from Facebook posts
"""

import sys
import os
import logging
import time
import re
from datetime import datetime
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostComment, PostImage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
except ImportError:
    print("Error: Selenium not available. Please run: pip install selenium")
    sys.exit(1)

try:
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    print("Error: Webdriver-manager not available. Please run: pip install webdriver-manager")
    sys.exit(1)

class CommentScraper:
    """Enhanced Comment Scraper for Facebook posts"""
    
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.db = DatabaseManager()
        self.debug_dir = os.path.join(ROOT_DIR, "debug")
        
        # Create debug directory if it doesn't exist
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def setup_browser(self):
        """Set up Firefox browser with appropriate settings"""
        try:
            logger.info("Setting up Firefox driver...")
            options = FirefoxOptions()
            
            if self.headless:
                options.add_argument("--headless")
                
            # Add preferences to improve performance and avoid detection
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("privacy.trackingprotection.enabled", False)
            options.set_preference("browser.cache.disk.enable", True)
            options.set_preference("browser.cache.memory.enable", True)
            options.set_preference("media.volume_scale", "0.0")  # Mute audio
            
            # Set user agent to avoid detection
            options.set_preference("general.useragent.override", 
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36")
            
            # Set up Firefox driver with service
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            
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

    def login_to_facebook(self, prompt_user=True):
        """Log in to Facebook"""
        try:
            self.driver.get("https://www.facebook.com/")
            logger.info("Navigated to Facebook login page")
            
            # Check if already logged in by looking for the Facebook search bar
            search_box = self.driver.find_elements(By.XPATH, "//input[@aria-label='Search Facebook' or @placeholder='Search Facebook']")
            
            if search_box:
                logger.info("Already logged in to Facebook")
                return True
            
            if prompt_user:
                print("\n" + "="*80)
                print("MANUAL LOGIN REQUIRED")
                print("="*80)
                print("1. Log in to Facebook with your credentials in the browser window")
                print("2. Complete any security checks if prompted")
                print("3. Return to this terminal when logged in")
                print("4. Type 'done' and press Enter to continue")
                print("="*80)
                
                print("Please log in to Facebook and type 'done' when finished...")
                user_input = input("After logging in, type 'done' here: ")
                
                if user_input.strip().lower() == 'done':
                    # Wait a moment for the page to update after login
                    time.sleep(3)
                    
                    # Verify login status by reloading the page
                    self.driver.get("https://www.facebook.com/")
                    time.sleep(3)  # Wait for page to load
                    
                    # Take screenshot for verification
                    self.take_debug_screenshot("login_verification")
                    
                    # Check for login indicators
                    search_box = self.driver.find_elements(By.XPATH, "//input[@aria-label='Search Facebook' or @placeholder='Search Facebook']")
                    if search_box:
                        logger.info("Successfully logged in to Facebook")
                        print("✅ Login successful! Proceeding...")
                        return True
                    else:
                        print("❌ Login verification failed. Please try again.")
                        return False
            
            # If we reach here, login failed or user canceled
            print("❌ Failed to log in to Facebook")
            return False
            
        except Exception as e:
            logger.error(f"Error during Facebook login: {e}")
            return False
            
    def take_debug_screenshot(self, name_prefix):
        """Take a screenshot for debugging purposes"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.debug_dir, f"{name_prefix}_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            
            # Also save page source for HTML analysis
            html_path = os.path.join(self.debug_dir, f"{name_prefix}_{timestamp}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                
            logger.info(f"Saved debug files: {screenshot_path} and {html_path}")
            return screenshot_path
        except Exception as e:
            logger.warning(f"Failed to take debug screenshot: {e}")
            return None

    def scrape_comments_from_post(self, post_url, post_id=None, expected_count=None):
        """
        Scrape comments from a Facebook post
        
        Args:
            post_url (str): URL of the post to scrape comments from
            post_id (str, optional): ID of the post. Will be extracted from URL if not provided
            expected_count (int, optional): Expected number of comments to validate extraction
            
        Returns:
            list: List of comment dictionaries
        """
        if not post_id:
            # Try to extract post ID from URL
            post_id = self.extract_post_id_from_url(post_url)
            
        if not post_id:
            post_id = f"unknown_{int(time.time())}"
            
        logger.info(f"Scraping comments for post: {post_id}")
        print(f"Scraping comments for post: {post_id}")
        print(f"Post URL: {post_url}")
        
        if expected_count is not None:
            print(f"Expected comment count: {expected_count}")
            
        try:
            # Navigate to the post
            self.driver.get(post_url)
            time.sleep(5)  # Wait for page to load
            
            # Take screenshot of the post before expanding comments
            self.take_debug_screenshot(f"post_{post_id}_before_comments")
            
            # First check if there are any comments at all
            comment_indicators = self.driver.find_elements(By.XPATH, 
                "//span[contains(text(), 'comment') or contains(text(), 'Comment')]")
            
            has_comments = False
            for indicator in comment_indicators:
                if re.search(r'\d+\s*comment', indicator.text.lower()):
                    has_comments = True
                    break
                    
            if not has_comments:
                print("No comments found on this post")
                return []
                
            # Try to find comments section and click to expand
            comment_section_selectors = [
                "//span[contains(text(), 'comment') or contains(text(), 'Comment')]/ancestor::div[@role='button']",
                "//a[contains(text(), 'comment')]",
                "//a[contains(@href, 'comment')]",
                "//div[@data-testid='UFI2CommentsList']",
            ]
            
            # Try to click on the comments section to expand it
            for selector in comment_section_selectors:
                try:
                    comment_sections = self.driver.find_elements(By.XPATH, selector)
                    for section in comment_sections:
                        if section.is_displayed() and section.is_enabled():
                            try:
                                self.driver.execute_script("arguments[0].click();", section)
                                logger.info(f"Clicked on comment section using selector: {selector}")
                                time.sleep(3)  # Wait for comments to expand
                                break
                            except Exception as e:
                                logger.warning(f"Failed to click on comment section: {e}")
                except Exception as e:
                    logger.warning(f"Error with comment section selector '{selector}': {e}")
                    
            # Take screenshot after expanding comment section
            self.take_debug_screenshot(f"post_{post_id}_expanded_comments")
            
            # Now expand all comments
            self.expand_all_comments(expected_count)
            
            # Take another screenshot after fully expanding
            self.take_debug_screenshot(f"post_{post_id}_all_comments_expanded")
            
            # Extract comments
            comments = self.extract_comments(post_id)
            
            # Validate count if expected count was provided
            if expected_count is not None and len(comments) < expected_count:
                logger.warning(f"Expected {expected_count} comments but found only {len(comments)}")
                print(f"⚠️ Warning: Expected {expected_count} comments but found only {len(comments)}")
                
            print(f"✅ Extracted {len(comments)} comments from post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error scraping comments from post {post_id}: {e}")
            print(f"❌ Error scraping comments: {e}")
            self.take_debug_screenshot(f"error_comments_{post_id}")
            return []

    def extract_post_id_from_url(self, url):
        """Try to extract post ID from URL"""
        try:
            # Try to find standard post ID patterns
            patterns = [
                r'\/posts\/(\w+)',
                r'\/permalink\.php\?story_fbid=(\w+)',
                r'fbid=(\w+)',
                r'\/photo\.php\?fbid=(\w+)',
                r'\/video\.php\?v=(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
                    
            # If no pattern matches, use a hash of the URL
            return f"post_{hash(url) % 10000}"
            
        except Exception:
            return None

    def expand_all_comments(self, expected_count=None):
        """Expand all comments and replies on a post"""
        try:
            print("Expanding all comments and replies...")
            
            # Max expansion attempts
            max_attempts = 20 if expected_count and expected_count > 50 else 10
            max_clicks = 100 if expected_count and expected_count > 50 else 50
            
            # Track total clicks
            total_clicks = 0
            
            # Multiple rounds of expansion to get all levels of comments
            for attempt in range(max_attempts):
                if total_clicks >= max_clicks:
                    logger.info(f"Reached maximum click limit ({max_clicks})")
                    break
                
                current_clicks = 0
                
                # 1. Expand "View more comments" buttons
                view_more_selectors = [
                    "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View previous comments')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View more comments')]",
                    "//div[@role='button' and contains(., 'View previous comments')]",
                    "//div[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]",
                    "//span[contains(text(), 'View') and contains(text(), 'comment')]/ancestor::*[1]",
                    "//a[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]",
                    "//a[contains(@class, 'UFIPagerLink')]",
                    "//div[contains(@class, 'UFIPagerLink')]"
                ]
                
                for selector in view_more_selectors:
                    try:
                        more_buttons = self.driver.find_elements(By.XPATH, selector)
                        
                        if more_buttons:
                            logger.info(f"Found {len(more_buttons)} 'View more comments' buttons with selector: {selector}")
                            
                            for button in more_buttons:
                                try:
                                    if button.is_displayed() and button.is_enabled():
                                        # Scroll to button
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                        time.sleep(1)
                                        
                                        # Click using JavaScript (more reliable)
                                        self.driver.execute_script("arguments[0].click();", button)
                                        current_clicks += 1
                                        total_clicks += 1
                                        
                                        print(f"Clicked 'View more comments' button ({total_clicks}/{max_clicks})")
                                        time.sleep(3)  # Wait for comments to load
                                        
                                        # Break after each click to re-evaluate DOM changes
                                        break
                                except Exception as e:
                                    logger.warning(f"Error clicking 'View more comments' button: {e}")
                    except Exception as e:
                        logger.warning(f"Error with selector '{selector}': {e}")
                
                # 2. Expand "View replies" buttons
                reply_selectors = [
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                    "//a[contains(text(), 'View') and contains(text(), 'repl')]",
                    "//a[contains(@class, 'UFIReplyList')]",
                    "//div[contains(@class, 'UFIReplyList')]"
                ]
                
                for selector in reply_selectors:
                    try:
                        reply_buttons = self.driver.find_elements(By.XPATH, selector)
                        
                        if reply_buttons:
                            logger.info(f"Found {len(reply_buttons)} 'View replies' buttons with selector: {selector}")
                            
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
                                        
                                        print(f"Clicked 'View replies' button ({total_clicks}/{max_clicks})")
                                        time.sleep(2)  # Wait for replies to load
                                        
                                        # Break after each click to re-evaluate DOM changes
                                        break
                                except Exception as e:
                                    logger.warning(f"Error clicking 'View replies' button: {e}")
                    except Exception as e:
                        logger.warning(f"Error with selector '{selector}': {e}")
                
                # Stop if we didn't click anything in this round
                if current_clicks == 0:
                    logger.info("No more expandable comments or replies found")
                    break
                    
                # Scroll down to load all comments
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
            logger.info(f"Finished expanding comments with {total_clicks} clicks")
            return True
            
        except Exception as e:
            logger.error(f"Error expanding comments: {e}")
            return False

    def extract_comments(self, post_id):
        """Extract all comments from the current page"""
        try:
            # Try different comment selectors for different Facebook layouts
            comment_selectors = [
                "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'comments-comment-item')]",
                "//div[contains(@data-testid, 'UFI2Comment')]",
                "//div[@data-testid='comment']",
                "//div[@role='article' and contains(@class, 'comment')]",
                "//div[contains(@class, 'commentable_item')]",
                "//div[contains(@class, 'comment') and .//span[@dir='auto']]",
                "//div[contains(@class, '_4eek')]",  # Classic FB comments
                "//div[contains(@data-testid, 'comment-root')]"  # New FB comments (2025)
            ]
            
            all_comments = []
            successful_selector = None
            
            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(By.XPATH, selector)
                    
                    if comment_elements:
                        logger.info(f"Found {len(comment_elements)} comments using selector: {selector}")
                        print(f"Found {len(comment_elements)} comments using selector: {selector}")
                        
                        # Process each comment
                        for i, comment_elem in enumerate(comment_elements):
                            try:
                                comment_data = self._extract_comment_data(comment_elem, post_id)
                                if comment_data:
                                    all_comments.append(comment_data)
                                    if (i+1) % 10 == 0:
                                        print(f"Processed {i+1} comments...")
                            except Exception as e:
                                logger.warning(f"Error extracting data from comment {i}: {e}")
                        
                        successful_selector = selector
                        break
                except Exception as e:
                    logger.warning(f"Error with comment selector '{selector}': {e}")
            
            if not all_comments:
                logger.warning("No comments found with any selector")
                print("No comments found with any selector")
                
            return all_comments
            
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
            return []

    def _extract_comment_data(self, comment_element, post_id):
        """Extract data from a comment element"""
        try:
            # Extract author with multiple selectors for different layouts
            author = "Unknown"
            author_selectors = [
                ".//a[contains(@class, 'UFIComment') or @role='link' or contains(@href, 'facebook.com')]",
                ".//span[contains(@class, 'actor') or contains(@class, 'user')]",
                ".//h3[contains(@class, 'actor')]",
                ".//a[contains(@class, 'actor')]",
                ".//a[@data-hovercard]", 
                ".//strong",
                ".//span[contains(@class, 'fcg')]",
                ".//a[@class='_6qw4']"  # New Facebook comment author class
            ]
            
            for selector in author_selectors:
                try:
                    author_elements = comment_element.find_elements(By.XPATH, selector)
                    if author_elements and author_elements[0].text:
                        author = author_elements[0].text
                        break
                except:
                    pass
            
            # Extract comment text with multiple selectors
            text = ""
            text_selectors = [
                ".//div[contains(@class, 'UFICommentBody') or @data-ad-comet-preview='message']",
                ".//div[@data-testid='comment-content']",
                ".//div[contains(@class, 'comment-content')]",
                ".//div[contains(@class, 'commentText')]",
                ".//span[@dir='auto']",
                ".//div[contains(@class, 'userContent')]",
                ".//div[contains(@data-testid, 'comment-text')]"  # New Facebook comment text
            ]
            
            for selector in text_selectors:
                try:
                    text_elements = comment_element.find_elements(By.XPATH, selector)
                    if text_elements and text_elements[0].text:
                        text = text_elements[0].text
                        break
                except:
                    pass
            
            # Skip if we couldn't extract useful data
            if not text or text.strip() == "":
                return None
                
            # Extract likes
            likes = 0
            try:
                likes_elements = comment_element.find_elements(By.XPATH, 
                    ".//span[contains(@class, 'UFICommentLikeButton') or contains(text(), 'Like')]")
                for likes_element in likes_elements:
                    likes_text = likes_element.get_attribute('aria-label') or likes_element.text
                    if likes_text and 'like' in likes_text.lower():
                        likes_match = re.search(r'(\d+)', likes_text)
                        if likes_match:
                            likes = int(likes_match.group(1))
            except:
                pass
            
            # Build comment data
            return {
                'post_id': post_id,
                'author': author,
                'text': text,
                'likes': likes,
                'comment_time': datetime.now(),  # Facebook doesn't show exact times easily
                'extracted_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error extracting comment data: {e}")
            return None

    def save_comments_to_database(self, comments):
        """Save extracted comments to database"""
        if not comments:
            return 0
            
        try:
            saved_count = 0
            with self.db.session_scope() as session:
                for comment_data in comments:
                    # Check if comment already exists
                    existing = session.query(PostComment).filter_by(
                        post_id=comment_data['post_id'],
                        author=comment_data['author'],
                        text=comment_data['text']
                    ).first()
                    
                    if not existing:
                        # Create new comment
                        comment = PostComment(
                            post_id=comment_data['post_id'],
                            author=comment_data['author'],
                            text=comment_data['text'],
                            likes=comment_data['likes'],
                            comment_time=comment_data['comment_time'],
                            extracted_at=comment_data['extracted_at']
                        )
                        session.add(comment)
                        saved_count += 1
                        
                # Update post's comment count
                if saved_count > 0 and comments[0]['post_id']:
                    post = session.query(FacebookPost).filter_by(
                        post_id=comments[0]['post_id']
                    ).first()
                    
                    if post:
                        post.comments_count = saved_count
                
            logger.info(f"Saved {saved_count} new comments to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving comments to database: {e}")
            return 0

    def process_posts_without_comments(self, max_posts=5):
        """Process posts that don't have comments yet"""
        try:
            print(f"Finding posts without comments (max: {max_posts})...")
            
            # Setup browser if not already done
            if not self.driver:
                if not self.setup_browser():
                    print("Failed to set up browser")
                    return False
            
            # Login to Facebook
            if not self.login_to_facebook():
                print("Failed to log in to Facebook")
                return False
                
            # Get posts from database that have URLs but no comments
            with self.db.session_scope() as session:
                posts = session.query(FacebookPost).outerjoin(
                    PostComment, FacebookPost.post_id == PostComment.post_id
                ).filter(
                    FacebookPost.post_url.isnot(None)
                ).group_by(
                    FacebookPost.id
                ).order_by(FacebookPost.id.desc()).limit(max_posts).all()
                
                if not posts:
                    print("No posts found that need comment extraction")
                    return True
                    
                print(f"Found {len(posts)} posts to process")
                
                total_comments = 0
                for i, post in enumerate(posts, 1):
                    print(f"\n{'-'*50}")
                    print(f"Processing post {i}/{len(posts)}: {post.post_id}")
                    print(f"URL: {post.post_url}")
                    print(f"{'-'*50}")
                    
                    # Extract expected comment count
                    expected_count = post.comments_count if post.comments_count and post.comments_count > 0 else None
                    
                    # Scrape comments
                    comments = self.scrape_comments_from_post(
                        post_url=post.post_url,
                        post_id=post.post_id,
                        expected_count=expected_count
                    )
                    
                    if comments:
                        saved_count = self.save_comments_to_database(comments)
                        total_comments += saved_count
                        print(f"✅ Saved {saved_count} new comments for post {post.post_id}")
                    else:
                        print(f"No comments found or extracted for post {post.post_id}")
                
                print(f"\n{'='*50}")
                print(f"COMMENT EXTRACTION SUMMARY")
                print(f"{'='*50}")
                print(f"Processed {len(posts)} posts")
                print(f"Extracted and saved {total_comments} new comments")
                print(f"{'='*50}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing posts: {e}")
            print(f"❌ Error: {e}")
            return False
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed")
                except:
                    pass

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Comment Scraper')
    parser.add_argument('--max-posts', type=int, default=5,
                      help='Maximum number of posts to process (default: 5)')
    parser.add_argument('--headless', action='store_true',
                      help='Run browser in headless mode (no UI)')
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("FACEBOOK COMMENT SCRAPER")
    print("="*80)
    print("This script will extract comments from Facebook posts")
    print(f"Max posts to process: {args.max_posts}")
    print(f"Headless mode: {'Yes' if args.headless else 'No'}")
    print("="*80 + "\n")
    
    scraper = CommentScraper(headless=args.headless)
    
    try:
        success = scraper.process_posts_without_comments(max_posts=args.max_posts)
        
        if success:
            print("\n✅ Comment extraction completed successfully")
            return 0
        else:
            print("\n❌ Comment extraction failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Unhandled error: {e}")
        logger.exception("Unhandled exception:")
        return 1
        
    finally:
        if scraper.driver:
            try:
                scraper.driver.quit()
                print("Browser closed")
            except:
                pass

if __name__ == "__main__":
    sys.exit(main())
