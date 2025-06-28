#!/usr/bin/env python
"""
Facebook Comment Fix Tool

This script checks the problem with comment scraping and fixes specific issues:
1. Verifies the database schema and connection
2. Provides a robust approach to extract and save comments from specific posts
3. Can be used both for debugging and as a comment fixer utility
"""

import sys
import logging
import os
import time
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR, DEBUG_DIR, IMAGES_DIR
from db.models import FacebookPost, PostComment

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
except ImportError:
    print("Error: Selenium not installed. Please run: pip install selenium webdriver-manager")
    sys.exit(1)

try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("Warning: Webdriver-manager not available. Will use local Firefox driver.")

# Configure logging
LOGS_DIR.mkdir(exist_ok=True)
DEBUG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'comment_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CommentFixer:
    """Tool to fix comment extraction and saving issues"""
    
    def __init__(self, headless=False):
        """Initialize the comment fixer"""
        self.headless = headless
        self.driver = None
        self.db = DatabaseManager()
        
    def setup_driver(self):
        """Initialize Firefox driver with optimized settings"""
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
                self.save_debug_info("login_success")
                return True
            else:
                logger.warning("Login not confirmed after waiting")
                print("\n❌ Login not confirmed after waiting. Please try again.")
                return False
                
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            print(f"Login error: {e}")
            return False
    
    def _check_login_status(self):
        """Check if we're logged in to Facebook"""
        try:
            # Look for elements that indicate we're logged in
            login_indicators = [
                "//div[@role='navigation']//a[@aria-label='Home']",
                "//div[@data-pagelet='LeftRail']",
                "//div[@role='banner']//a[@aria-label='Home']",
                "//div[@aria-label='Create']"
            ]
            
            for selector in login_indicators:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    return True
            
            return False
        except:
            return False
    
    def extract_comments(self, post_url, post_id):
        """Extract comments from a specific post URL"""
        if not self.driver:
            self.start()
        
        try:
            logger.info(f"Navigating to post to extract comments: {post_url}")
            self.driver.get(post_url)
            time.sleep(5)  # Wait for page to load
            
            # Save debug info to analyze the page structure
            self.save_debug_info(f"comments_page_{post_id}")
            
            # Expand all comments
            self._expand_comments()
            
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
            successful_selector = None
            
            for selector in comment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    comment_elements = elements
                    successful_selector = selector
                    logger.info(f"Found {len(elements)} comments using selector: {selector}")
                    break
            
            if not comment_elements:
                logger.info(f"No comments found for post {post_id}")
                return []
            
            logger.info(f"Found {len(comment_elements)} comments for post {post_id} using selector: {successful_selector}")
            
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
                    
                    # Skip if we couldn't get both author and text
                    if not author or not text:
                        logger.warning(f"Skipping comment with incomplete data: author='{author}', text='{text}'")
                        continue
                    
                    # Build comment data
                    comment_data = {
                        'post_id': post_id,
                        'author': author,
                        'text': text,
                        'likes': 0,  # Default value
                        'comment_time': datetime.now(),  # Facebook doesn't show exact comment times easily
                        'extracted_at': datetime.now()
                    }
                    
                    comments.append(comment_data)
                    
                except Exception as e:
                    logger.warning(f"Error extracting a comment: {e}")
            
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments from post {post_id}: {e}")
            return []
    
    def _expand_comments(self):
        """Expand all comments and replies"""
        try:
            print("Expanding comments and replies...")
            # Take debug screenshot at start
            self.save_debug_info("before_expand_comments")
            
            # Track clicks for reporting
            total_clicks = 0
            max_attempts = 10  # Maximum number of attempts to expand comments
            
            # Loop multiple times to make sure we expand all nested levels
            for attempt in range(max_attempts):
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
                            except:
                                pass
                
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
                            except:
                                pass
                
                # If no clicks were made in this round, we might be done
                if current_clicks == 0:
                    if attempt >= 2:  # Make sure we've made at least 3 attempts
                        break
                
                # Scroll down a bit to load more content
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
            logger.info(f"Comment expansion completed with {total_clicks} total clicks")
            
        except Exception as e:
            logger.error(f"Error expanding comments: {e}")
    
    def save_comments_to_database(self, comments):
        """Save comments to the database directly"""
        if not comments:
            logger.info("No comments to save")
            return 0
        
        saved_count = 0
        try:
            with self.db.session_scope() as session:
                for comment_data in comments:
                    post_id = comment_data.get('post_id')
                    
                    # Check if post exists in database
                    post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                    if not post:
                        logger.warning(f"Post {post_id} not found in database, skipping comment")
                        continue
                    
                    # Check if this comment already exists (avoid duplicates)
                    existing_comment = session.query(PostComment).filter_by(
                        post_id=post_id,
                        author=comment_data.get('author'),
                        text=comment_data.get('text')
                    ).first()
                    
                    if existing_comment:
                        logger.info(f"Comment by {comment_data.get('author')} already exists, skipping")
                        continue
                    
                    # Create new comment
                    comment = PostComment(
                        post_id=post_id,
                        author=comment_data.get('author'),
                        text=comment_data.get('text'),
                        comment_time=comment_data.get('comment_time', datetime.now()),
                        likes=comment_data.get('likes', 0),
                        extracted_at=datetime.now()
                    )
                    
                    # Add to session
                    session.add(comment)
                    saved_count += 1
                    
                # Session will be committed automatically when exiting the context manager
            
            logger.info(f"Successfully saved {saved_count} new comments to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving comments to database: {e}")
            return 0
    
    def get_posts_without_comments(self, limit=10):
        """Get posts that don't have any comments but should have (comments_count > 0)"""
        try:
            with self.db.session_scope() as session:
                # Find posts with comments_count > 0 but no actual comments
                posts = session.query(FacebookPost).filter(
                    FacebookPost.comments_count > 0
                ).all()
                
                posts_without_comments = []
                for post in posts:
                    # Check if this post has any comments
                    comment_count = session.query(PostComment).filter_by(
                        post_id=post.post_id
                    ).count()
                    
                    if comment_count == 0:
                        posts_without_comments.append(post)
                
                # Return up to the limit
                return posts_without_comments[:limit]
                
        except Exception as e:
            logger.error(f"Error getting posts without comments: {e}")
            return []
    
    def fix_missing_comments(self, post_limit=10):
        """Fix posts that are missing comments"""
        if not self.driver:
            self.start()
            
        # Make sure we're logged in
        if not self._check_login_status():
            if not self.manual_login():
                logger.error("Not logged in to Facebook")
                return False
        
        # Get posts without comments
        posts_to_fix = self.get_posts_without_comments(post_limit)
        
        if not posts_to_fix:
            logger.info("No posts found that need comment fixing")
            print("No posts found that need comment fixing")
            return True
        
        logger.info(f"Found {len(posts_to_fix)} posts that need comment fixing")
        print(f"Found {len(posts_to_fix)} posts that need comment fixing")
        
        total_comments_saved = 0
        fixed_posts = 0
        
        # Process each post
        for post in posts_to_fix:
            try:
                logger.info(f"Fixing comments for post {post.post_id}")
                print(f"Fixing comments for post {post.post_id}")
                
                if not post.post_url:
                    logger.warning(f"Post {post.post_id} has no URL, skipping")
                    continue
                
                # Extract comments for this post
                comments = self.extract_comments(post.post_url, post.post_id)
                
                if comments:
                    # Save comments to database
                    saved_count = self.save_comments_to_database(comments)
                    if saved_count > 0:
                        fixed_posts += 1
                        total_comments_saved += saved_count
                        print(f"✓ Saved {saved_count} comments for post {post.post_id}")
                
                # Sleep a bit to avoid overloading
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error fixing comments for post {post.post_id}: {e}")
                print(f"✗ Error fixing comments for post {post.post_id}: {e}")
        
        logger.info(f"Fixed {fixed_posts}/{len(posts_to_fix)} posts, saving {total_comments_saved} comments")
        print(f"Fixed {fixed_posts}/{len(posts_to_fix)} posts, saving {total_comments_saved} comments")
        
        return fixed_posts > 0

    def print_comment_statistics(self):
        """Print statistics about comments in the database"""
        try:
            with self.db.session_scope() as session:
                total_posts = session.query(FacebookPost).count()
                total_comments = session.query(PostComment).count()
                
                # Posts with comments
                posts_with_comments = session.query(FacebookPost).join(PostComment).distinct().count()
                
                # Posts that should have comments but don't
                posts_missing_comments_count = session.query(FacebookPost).filter(
                    FacebookPost.comments_count > 0,
                    ~FacebookPost.post_id.in_(
                        session.query(PostComment.post_id).distinct()
                    )
                ).count()
                
                print("\n" + "="*60)
                print("COMMENT STATISTICS")
                print("="*60)
                print(f"Total posts in database: {total_posts}")
                print(f"Total comments in database: {total_comments}")
                print(f"Posts with comments: {posts_with_comments}")
                print(f"Posts missing comments: {posts_missing_comments_count}")
                print("="*60)
                
                return {
                    "total_posts": total_posts,
                    "total_comments": total_comments,
                    "posts_with_comments": posts_with_comments,
                    "posts_missing_comments": posts_missing_comments_count
                }
                
        except Exception as e:
            logger.error(f"Error getting comment statistics: {e}")
            print(f"Error getting comment statistics: {e}")
            return None

def main():
    """Main function"""
    print("\n" + "="*80)
    print("FACEBOOK COMMENT FIXER")
    print("="*80)
    print("This tool will check for posts that should have comments")
    print("but don't, and attempt to fix them by scraping the comments again.")
    print("="*80)
    
    # Initialize fixer
    fixer = CommentFixer(headless=False)
    
    try:
        # Print current statistics
        print("\n[1/4] Checking current comment statistics...")
        fixer.print_comment_statistics()
        
        # Initialize database if needed
        print("\n[2/4] Verifying database connection and schema...")
        fixer.db.init_db()
        if not fixer.db.health_check():
            print("Database health check failed. Please fix database issues first.")
            return 1
        
        # Start browser
        print("\n[3/4] Starting browser and fixing missing comments...")
        result = fixer.fix_missing_comments(post_limit=10)
        
        # Print statistics after fixing
        print("\n[4/4] Updated comment statistics:")
        fixer.print_comment_statistics()
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in comment fixer: {e}")
        print(f"Error: {e}")
        return 1
    
    finally:
        # Always close the browser
        fixer.close()

if __name__ == "__main__":
    sys.exit(main())
