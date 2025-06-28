#!/usr/bin/env python
"""
Fix script for Facebook comments scraping issues
This script contains improvements to the comment extraction functionality
"""

import sys
import os
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from sqlalchemy import func

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostComment

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

class CommentFixer:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.db = DatabaseManager()
        self.setup_browser()
        
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
                user_input = input("After logging in, type 'done' here:")
                
                if user_input.strip().lower() == 'done':
                    # Verify login status
                    self.driver.get("https://www.facebook.com/")
                    search_box = self.driver.find_elements(By.XPATH, "//input[@aria-label='Search Facebook' or @placeholder='Search Facebook']")
                    
                    if search_box:
                        logger.info("Successfully logged in to Facebook")
                        print("✅ Login successful! Proceeding...")
                        return True
            
            # If we reach here, login failed or user canceled
            print("❌ Failed to log in to Facebook")
            return False
            
        except Exception as e:
            logger.error(f"Error during Facebook login: {e}")
            return False
    
    def extract_comments_for_post(self, post):
        """Extract comments for a single post"""
        if not post.post_url:
            logger.warning(f"Post {post.post_id} has no URL, skipping comment extraction")
            return 0
            
        try:
            print(f"Extracting comments for post {post.post_id}")
            logger.info(f"Navigating to post URL: {post.post_url}")
            
            # Navigate to the post URL
            self.driver.get(post.post_url)
            time.sleep(5)  # Wait for page to load
            
            # Take screenshot for debugging
            debug_dir = os.path.join(ROOT_DIR, "debug")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            screenshot_path = os.path.join(debug_dir, f"comment_extraction_{post.post_id}.png")
            self.driver.save_screenshot(screenshot_path)
            
            # Expand comments
            expanded = self._expand_comments()
            if not expanded:
                logger.warning(f"Failed to expand comments for post {post.post_id}")
                
            # Take another screenshot after expansion
            screenshot_path = os.path.join(debug_dir, f"after_expand_{post.post_id}.png")
            self.driver.save_screenshot(screenshot_path)
            
            # Try multiple comment selector patterns to find comments
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
            
            comment_elements = []
            successful_selector = None
            
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} comments using selector: {selector}")
                        print(f"Found {len(elements)} comments using selector: {selector}")
                        comment_elements = elements
                        successful_selector = selector
                        break
                except Exception as e:
                    logger.warning(f"Error with selector '{selector}': {e}")
            
            if not comment_elements:
                logger.info(f"No comments found for post {post.post_id}")
                print(f"No comments found for post {post.post_id}")
                return 0
                
            print(f"Processing {len(comment_elements)} comments for post {post.post_id}")
            
            # Process comments
            comments_saved = 0
            for i, comment_elem in enumerate(comment_elements):
                try:
                    # Extract comment data using new selectors
                    comment_data = self._extract_comment_data(comment_elem, post.post_id)
                    
                    if comment_data:
                        # Save comment to database
                        with self.db.session_scope() as session:
                            # Check if comment exists
                            existing = session.query(PostComment).filter_by(
                                post_id=post.post_id,
                                author=comment_data['author'],
                                text=comment_data['text']
                            ).first()
                            
                            if not existing:
                                new_comment = PostComment(
                                    post_id=post.post_id,
                                    author=comment_data['author'],
                                    text=comment_data['text'],
                                    likes=comment_data['likes'],
                                    comment_time=comment_data['comment_time'],
                                    extracted_at=datetime.now()
                                )
                                session.add(new_comment)
                                comments_saved += 1
                                
                                if comments_saved % 5 == 0:
                                    print(f"  Saved {comments_saved} comments so far...")
                except Exception as e:
                    logger.error(f"Error processing comment {i}: {e}")
            
            print(f"✅ Successfully saved {comments_saved} comments for post {post.post_id}")
            return comments_saved
            
        except Exception as e:
            logger.error(f"Error extracting comments for post {post.post_id}: {e}")
            return 0
    
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
                logger.warning(f"Comment has no text, skipping")
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
    
    def _expand_comments(self):
        """Expand all comments and replies"""
        try:
            print("Expanding comments and replies...")
            
            # Track clicks for reporting
            total_clicks = 0
            max_attempts = 5  # Maximum number of attempts to expand comments
            max_clicks = 30  # Limit clicks to avoid infinite loops
            
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
                        logger.info(f"Found {len(more_buttons)} 'View more comments' buttons with selector: {selector}")
                        
                        for button in more_buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    # Scroll to button to make it clickable
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                    time.sleep(1)
                                    
                                    # Click using JavaScript to avoid ElementClickInterceptedException
                                    self.driver.execute_script("arguments[0].click();", button)
                                    
                                    current_clicks += 1
                                    total_clicks += 1
                                    logger.info(f"Clicked 'View more comments' button ({total_clicks}/{max_clicks})")
                                    time.sleep(3)  # Wait for more comments to load
                                    
                                    # Break after each successful click to re-find buttons
                                    break
                            except Exception as e:
                                logger.warning(f"Error clicking 'View more comments' button: {e}")
                
                # Try to expand comment replies
                reply_selectors = [
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                    "//div[contains(text(), 'View') and contains(text(), 'repl')]",
                    "//a[contains(text(), 'View') and contains(text(), 'repl')]"
                ]
                
                for selector in reply_selectors:
                    reply_buttons = self.driver.find_elements(By.XPATH, selector)
                    if reply_buttons:
                        logger.info(f"Found {len(reply_buttons)} 'View replies' buttons with selector: {selector}")
                        
                        for button in reply_buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    # Scroll to button
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                    time.sleep(1)
                                    
                                    # Click using JavaScript
                                    self.driver.execute_script("arguments[0].click();", button)
                                    
                                    current_clicks += 1
                                    total_clicks += 1
                                    logger.info(f"Clicked 'View replies' button ({total_clicks}/{max_clicks})")
                                    time.sleep(2)  # Wait for replies to load
                                    
                                    # Break after each successful click to re-find buttons
                                    break
                            except Exception as e:
                                logger.warning(f"Error clicking 'View replies' button: {e}")
                
                if current_clicks == 0:
                    logger.info("No more expandable comments found")
                    break
                    
            logger.info(f"Finished expanding comments, made {total_clicks} clicks")
            return True
        
        except Exception as e:
            logger.error(f"Error expanding comments: {e}")
            return False
    
    def fix_comments_for_posts(self, max_posts=10):
        """Fix comments for posts that have missing comments"""
        if not self.login_to_facebook():
            print("Failed to log in to Facebook, cannot proceed")
            return False
            
        try:
            # Get posts from database
            with self.db.session_scope() as session:
                # Get posts that have a URL but no comments
                posts = session.query(FacebookPost).outerjoin(
                    PostComment, FacebookPost.post_id == PostComment.post_id
                ).group_by(FacebookPost.id).having(
                    func.count(PostComment.id) == 0
                ).filter(
                    FacebookPost.post_url.isnot(None)
                ).order_by(
                    FacebookPost.id.desc()
                ).limit(max_posts).all()
                
                if not posts:
                    print("No posts found that need comment fixing")
                    return True
                    
                print(f"Found {len(posts)} posts that need comment fixing")
                
                total_comments_fixed = 0
                for i, post in enumerate(posts, 1):
                    print(f"\nProcessing post {i}/{len(posts)}: {post.post_id}")
                    comments_fixed = self.extract_comments_for_post(post)
                    total_comments_fixed += comments_fixed
                    
                    # Update post with comments_count
                    if comments_fixed > 0:
                        post.comments_count = comments_fixed
                        session.commit()
                
                print(f"\n✅ Fixed comments for {len(posts)} posts, added {total_comments_fixed} comments")
                return True
                
        except Exception as e:
            logger.error(f"Error fixing comments: {e}")
            return False
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

def main():
    """Main function"""
    print("\n" + "="*80)
    print("FACEBOOK COMMENT FIXER")
    print("="*80)
    print("This script will attempt to extract missing comments from Facebook posts")
    print("="*80 + "\n")
    
    # Parse command line arguments if needed
    import argparse
    parser = argparse.ArgumentParser(description='Facebook Comment Fixer')
    parser.add_argument('--max-posts', type=int, default=10,
                      help='Maximum number of posts to fix (default: 10)')
    parser.add_argument('--headless', action='store_true',
                      help='Run browser in headless mode (no UI)')
    args = parser.parse_args()
    
    print(f"Will attempt to fix comments for up to {args.max_posts} posts")
    print(f"Headless mode: {'Yes' if args.headless else 'No'}")
    
    # Initialize comment fixer
    fixer = CommentFixer(headless=args.headless)
    
    # Fix comments
    try:
        success = fixer.fix_comments_for_posts(max_posts=args.max_posts)
        if success:
            print("\n✅ Comments fixing process completed successfully")
            return 0
        else:
            print("\n❌ Failed to fix comments")
            return 1
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 130
    finally:
        if fixer.driver:
            try:
                fixer.driver.quit()
                print("Browser closed")
            except:
                pass

if __name__ == "__main__":
    sys.exit(main())
