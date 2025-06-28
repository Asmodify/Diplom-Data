#!/usr/bin/env python
"""
Enhanced Comment Scraper for Facebook
Focuses on extracting all comments from Facebook posts
"""

import sys
import logging
import argparse
import time
import re
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR, DEBUG_DIR
from db.models import FacebookPost, PostComment
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

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
    """Enhanced scraper focused on extracting all comments from Facebook posts"""
    def __init__(self, headless=False, debug=False):
        """Initialize the comment scraper"""
        self.headless = headless
        self.driver = None
        self.db = DatabaseManager()
        self.wait_time = 10  # Default wait time in seconds
        
        # Set debug logging if requested
        if debug:
            logger.setLevel(logging.DEBUG)
            # Also set handler levels
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        
    def setup_driver(self):
        """Initialize Firefox driver with optimized settings"""
        logger.info("Setting up Firefox driver...")
        try:
            # Configure Firefox options
            options = FirefoxOptions()
            options.set_preference("dom.webnotifications.enabled", False)  # Disable notifications
            options.headless = self.headless  # Set headless mode based on parameter
            
            # Try with WebDriver Manager if available
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = webdriver.firefox.service.Service(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            else:
                # Fallback to local driver if WebDriver Manager is not available
                driver = webdriver.Firefox(options=options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            logger.info("Firefox browser set up successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Error setting up Firefox browser: {e}")
            # Save detailed error information
            error_log_path = DEBUG_DIR / f"browser_error_{int(time.time())}.txt"
            with open(error_log_path, "w") as f:
                f.write(f"Error setting up browser: {str(e)}\n")
                
            raise RuntimeError(f"Could not initialize Firefox browser: {e}")
    
    def start(self):
        """Start the browser session"""
        if not self.driver:
            self.driver = self.setup_driver()
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser closed")
    
    def save_page_source(self, filename_prefix):
        """Save current page source and screenshot for debugging"""
        if not self.driver:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML
        html_path = DEBUG_DIR / f"{filename_prefix}_{timestamp}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
              # Save screenshot
        screenshot_path = DEBUG_DIR / f"{filename_prefix}_{timestamp}.png"
        self.driver.save_screenshot(str(screenshot_path))
        logger.info(f"Saved debug info: {html_path.name} and {screenshot_path.name}")
        
    def manual_login(self):
        """Perform manual login process with verification"""
        if not self.driver:
            self.start()
            
        try:
            # Navigate to Facebook
            logger.info("Navigating to Facebook for login...")
            self.driver.get("https://www.facebook.com")
            
            # Clear any cookies banner if present
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Cookie')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    time.sleep(1)
            except Exception:
                pass
                
            time.sleep(2)
            
            # Display manual login instructions
            print("\n" + "="*80)
            print("MANUAL LOGIN REQUIRED")
            print("="*80)
            print("1. Log in to Facebook with your credentials in the browser window")
            print("2. Complete any security checks or CAPTCHAs if prompted")
            print("3. Make sure you see your newsfeed or profile page to confirm successful login")
            print("4. Return to this terminal when logged in")
            print("5. Type 'done' and press Enter to continue")
            print("="*80)
            
            # Wait for user confirmation
            user_input = ""
            while user_input.lower() != 'done':
                user_input = input("When you're logged in completely, type 'done': ")
                
                if user_input.lower() == 'help':
                    print("\n- Make sure you can see your Facebook newsfeed or profile")
                    print("- If you're having trouble, try manually navigating to facebook.com/home.php")
                    print("- Complete all security checks (SMS code, CAPTCHA, etc.)")
                    print("- Type 'done' when you can see your own profile or newsfeed\n")
            
            # Verify login was successful
            try:
                # Multiple ways to check if login was successful
                selectors = [
                    "//div[@aria-label='Your profile' or @aria-label='Create' or @aria-label='Account']",
                    "//div[contains(@aria-label, 'Notifications')]",
                    "//span[contains(text(), 'Friend') or contains(text(), 'Home') or contains(text(), 'Watch')]",
                    "//input[@placeholder='Search Facebook' or @aria-label='Search Facebook']"
                ]
                
                login_verified = False
                for selector in selectors:
                    try:
                        wait = WebDriverWait(self.driver, 3)
                        elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                        if elements:
                            login_verified = True
                            break
                    except:
                        continue
                
                if not login_verified:
                    # Try another check - look for logout link
                    if "log out" in self.driver.page_source.lower() or "logout" in self.driver.page_source.lower():
                        login_verified = True
                
                if login_verified:
                    logger.info("Login verified successfully")
                    print("\n✅ Login verified successfully!")
                else:
                    logger.warning("Login could not be verified, but continuing anyway")
                    print("\n⚠️ Login could not be verified automatically, but continuing anyway.")
                    print("   If you encounter issues, please restart and ensure login is complete.")
            except Exception as e:
                logger.warning(f"Error verifying login: {e}")
                print("\n⚠️ Login verification encountered an issue, continuing anyway.")
            
            # Save debug info
            self.save_page_source("login_success_manual")
            
            # Navigate to Facebook homepage to ensure we're in a known state
            try:
                self.driver.get("https://www.facebook.com/")
                time.sleep(3)  # Wait for homepage to load
            except:
                pass
                
            print("\nProceeding with comment scraping...")
            return True
            
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            print(f"\n❌ Login process encountered an error: {e}")
            print("Please try again or check the logs for details.")
            return False
            
    def expand_all_comments(self):
        """Click all 'View more comments' and 'Reply' buttons to expand all comments"""
        if not self.driver:
            return
            
        try:
            # Track clicks for reporting purposes
            total_clicks = 0
            max_attempts = 10  # Increased from 5 to handle very lengthy comment threads
            
            # Loop multiple times to make sure we expand all nested levels
            for attempt in range(max_attempts):
                current_clicks = 0
                
                # A more comprehensive list of possible selectors for expanding comments
                view_more_selectors = [
                    "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View previous comments')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View') and contains(text(), 'more comment')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'previous comments')]/ancestor::*[@role='button']",
                    "//div[@role='button' and contains(., 'View more comments')]",
                    "//div[@role='button' and contains(., 'View previous comments')]",
                    # Sometimes Facebook uses aria-label for these buttons
                    "//*[@aria-label='View more comments']",
                    "//*[@aria-label='View previous comments']"
                ]
                
                # Try each selector to find view more buttons
                for selector in view_more_selectors:
                    more_comments_buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    if more_comments_buttons:
                        logger.info(f"Found {len(more_comments_buttons)} 'View more comments' buttons with selector: {selector}")
                        for button in more_comments_buttons:
                            try:
                                # Scroll to button first to ensure it's in view
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                # Click the button
                                self.driver.execute_script("arguments[0].click();", button)
                                current_clicks += 1
                                total_clicks += 1
                                # Wait for comments to load - important for pages with many comments
                                time.sleep(2)
                            except Exception as e:
                                logger.warning(f"Failed to click 'View more' button: {e}")
                                continue
                
                # Find and click all "View replies" and similar buttons to expand nested comments
                reply_selectors = [
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                    "//span[contains(text(), 'View') and contains(text(), 'repl')]/parent::div[@role='button']",
                    "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                    "//a[contains(text(), 'View') and contains(text(), 'repl')]",
                    # Some variations seen on Facebook
                    "//span[contains(text(), 'Reply') or contains(text(), 'replies')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(text(), 'replies')]"
                ]
                
                for selector in reply_selectors:
                    reply_buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    if reply_buttons:
                        logger.info(f"Found {len(reply_buttons)} reply expansion buttons with selector: {selector}")
                        for button in reply_buttons:
                            try:
                                # Scroll to button first to ensure it's in view
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                # Click the button
                                self.driver.execute_script("arguments[0].click();", button)
                                current_clicks += 1
                                total_clicks += 1
                                # Wait for replies to load
                                time.sleep(1.5)
                            except Exception as e:
                                logger.warning(f"Failed to click reply button: {e}")
                                continue
                
                # Expand long comments with "See more" buttons
                see_more_selectors = [
                    "//div[@role='button' and contains(text(), 'See more')]",
                    "//span[text()='See more']/ancestor::div[@role='button']",
                    "//div[contains(@class, 'see_more_link') or contains(@id, 'see_more')]"
                ]
                
                for selector in see_more_selectors:
                    see_more_buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    if see_more_buttons:
                        logger.info(f"Found {len(see_more_buttons)} 'See more' buttons with selector: {selector}")
                        for button in see_more_buttons:
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.3)
                                self.driver.execute_script("arguments[0].click();", button)
                                current_clicks += 1
                                total_clicks += 1
                                time.sleep(0.5)
                            except Exception as e:
                                logger.warning(f"Failed to click 'See more' button: {e}")
                                continue
                
                # Scroll to load more content
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
                # If we didn't find any new buttons to click, we might be done
                if current_clicks == 0:
                    # One more check - scroll to the bottom to ensure all content is loaded
                    if attempt == max_attempts - 2:  # On second-to-last attempt
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(3)  # Give it time to load
                    else:
                        logger.info(f"No new buttons found on attempt {attempt+1}/{max_attempts}, may be finished expanding")
                        if attempt >= 2:  # Only exit early if we've done at least 3 attempts
                            break
            
            logger.info(f"Completed comment expansion with {total_clicks} total clicks")
            
        except Exception as e:
            logger.error(f"Error while expanding comments: {e}")
    
    def extract_comments_from_page(self):
        """Extract all comments from the current post page"""
        if not self.driver:
            return []
            
        comments = []
        try:
            # First expand all comments and replies
            self.expand_all_comments()
              # Find all comment elements - comprehensive selectors to handle Facebook's changing UI
            comment_selectors = [
                "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
                "//div[@data-testid='comment-root']",
                "//div[contains(@class, 'commentable_item')]",
                "//div[contains(@id, 'comment_')]",
                "//div[@role='article' and contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'UFICommentContent')]",
                "//div[contains(@class, '_3-8y')]" # Another common Facebook comment class
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    logger.info(f"Found {len(elements)} comment elements with selector: {selector}")
                    comment_elements.extend(elements)
            
            # Remove duplicates (in case multiple selectors matched the same elements)
            comment_elements = list(set(comment_elements))
            logger.info(f"Found {len(comment_elements)} unique comment elements")
            
            for comment in comment_elements:
                try:                    # Extract comment author - try multiple possible selectors
                    author = "Unknown User"  # Default if extraction fails
                    author_selectors = [
                        ".//a[contains(@class, 'UFIComment') or @role='link' or contains(@href, 'facebook.com')]",
                        ".//a[contains(@class, 'UFICommentActorName')]",
                        ".//span[contains(@class, 'UFICommentActorName')]",
                        ".//span[@class='fwb']//a",
                        ".//h3//a | .//h3//span",
                        ".//a[contains(@href, '/user/')]",
                        ".//a[contains(@aria-label, 'Comment by')]"
                    ]
                    
                    for selector in author_selectors:
                        try:
                            author_elements = comment.find_elements(By.XPATH, selector)
                            if author_elements:
                                author = author_elements[0].text
                                if author and len(author.strip()) > 0:
                                    break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue
                    
                    # Extract comment text - try multiple possible selectors
                    text = ""
                    text_selectors = [
                        ".//div[contains(@class, 'UFICommentBody') or @data-ad-comet-preview='message']",
                        ".//span[@data-testid='comment-text']",
                        ".//div[contains(@class, 'UFICommentContent')]//span",
                        ".//div[contains(@dir, 'auto') and not(contains(@class, 'UFICommentActorName'))]",
                        ".//span[contains(@class, '_3l3x')]",
                        ".//div[@data-testid='comment-content']"
                    ]
                    
                    for selector in text_selectors:
                        try:
                            text_elements = comment.find_elements(By.XPATH, selector)
                            if text_elements:
                                # Combine all text from matching elements
                                parts = [el.text for el in text_elements if el.text]
                                text = " ".join(parts)
                                if text and len(text.strip()) > 0:
                                    break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue
                      # Try to extract likes using multiple selectors and formats
                    likes = 0
                    try:
                        like_selectors = [
                            # Direct like count spans/divs
                            ".//span[contains(@class, 'UFICommentLikeButton')]",
                            ".//span[contains(text(), 'Like')]",
                            ".//div[contains(@class, '_1r_8') and contains(@role, 'button')]",  # Common like button class
                            
                            # Reaction counts
                            ".//div[contains(@class,'UFICommentReactionCount')]",
                            ".//div[contains(@data-testid, 'UFI2ReactionsCount')]",
                            ".//div[contains(@class, '_1lbq')]",  # Another common reaction count class
                            
                            # Text indicating likes
                            ".//*[contains(text(), ' like') or contains(text(), ' reaction')]",
                            
                            # Thumbs up icon's parent, which might have counts
                            ".//div[.//i[contains(@class, 'like')]]"
                        ]
                        
                        for selector in like_selectors:
                            like_elements = comment.find_elements(By.XPATH, selector)
                            if like_elements:
                                for like_elem in like_elements:
                                    # Try getting from aria-label (common for reaction buttons)
                                    likes_text = like_elem.get_attribute('aria-label')
                                    
                                    # If aria-label didn't work, try the element's text
                                    if not likes_text:
                                        likes_text = like_elem.text
                                    
                                    if likes_text and ('like' in likes_text.lower() or 'reaction' in likes_text.lower()):
                                        # Extract numbers using regex
                                        likes_matches = re.findall(r'\d+', likes_text)
                                        if likes_matches:
                                            likes = int(likes_matches[0])
                                            break
                                
                                if likes > 0:
                                    break
                                    
                    except Exception as e:
                        logger.debug(f"Failed to extract likes count: {e}")
                        pass
                      # Extract time (approximate with parsing for common formats)
                    comment_time = datetime.now()
                    try:
                        time_selectors = [
                            ".//abbr",
                            ".//a[contains(@class, 'UFISutroCommentTimestamp')]",
                            ".//span[contains(@class, 'UFICommentTimestamp')]",
                            ".//a[contains(@class, 'timestamp')]",
                            ".//span[contains(@class, 'timestamp')]",
                            ".//span[contains(@data-testid, 'timestamp')]",
                            ".//a[contains(@href, '/comment/')]//span[contains(text(), ' ')]"  # Often holds timestamps
                        ]
                        
                        for selector in time_selectors:
                            time_elements = comment.find_elements(By.XPATH, selector)
                            if time_elements:
                                time_text = time_elements[0].text
                                if time_text:
                                    # Try to parse common Facebook time formats
                                    now = datetime.now()
                                    
                                    # Handle "X minutes/hours ago" format
                                    if "min" in time_text or "hr" in time_text or "sec" in time_text or "just now" in time_text.lower():
                                        # Very recent - keep current datetime
                                        pass
                                    
                                    # Handle "Yesterday/Today at HH:MM" format
                                    elif "yesterday" in time_text.lower():
                                        from datetime import timedelta
                                        comment_time = now - timedelta(days=1)
                                    
                                    # Handle "Month Day at HH:MM" format (e.g., "June 20 at 14:20")
                                    elif "at" in time_text and any(month in time_text.lower() for month in 
                                                                ["january", "february", "march", "april", "may", "june", 
                                                                "july", "august", "september", "october", "november", "december"]):
                                        # Extract just the year from current time and combine with the month/day info
                                        # This is an approximation since we don't have the full timestamp
                                        comment_time = now.replace(day=now.day, month=now.month)  # Approximation
                                    
                                    # Handle "Month Day, Year" format
                                    elif any(month in time_text.lower() for month in 
                                            ["january", "february", "march", "april", "may", "june", 
                                            "july", "august", "september", "october", "november", "december"]):
                                        # Contains a month name, likely an older comment
                                        # This is just an approximation as parsing specific dates would need more complex logic
                                        comment_time = now.replace(year=now.year-1)  # Default to last year as approximation
                                    
                                    # Log what we found
                                    logger.debug(f"Comment timestamp text: '{time_text}', parsed as: {comment_time}")
                                    break
                    except Exception as e:
                        logger.debug(f"Failed to parse comment timestamp: {e}")
                        # Keep default current time
                    
                    # Add to comments list
                    comments.append({
                        'author': author,
                        'text': text,
                        'likes': likes,
                        'comment_time': comment_time
                    })
                    
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
            
            logger.info(f"Successfully extracted {len(comments)} comments")
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
            self.save_page_source("comment_extraction_error")
            return comments
    
    def update_post_comments(self, post_id, comments):
        """Save or update comments for a post in the database"""
        if not comments:
            logger.info(f"No comments to save for post {post_id}")
            return
            
        try:
            with self.db.session_scope() as session:
                # Get the post
                post = session.query(FacebookPost).filter(
                    FacebookPost.post_id == post_id
                ).first()
                
                if not post:
                    logger.error(f"Post {post_id} not found in database")
                    return
                
                # Add each comment
                for comment_data in comments:
                    # Check if comment already exists based on author and text
                    existing_comment = session.query(PostComment).filter(
                        PostComment.post_id == post_id,
                        PostComment.author == comment_data['author'],
                        PostComment.text == comment_data['text']
                    ).first()
                    
                    if existing_comment:
                        # Update existing comment
                        existing_comment.likes = comment_data['likes']
                    else:
                        # Create new comment
                        new_comment = PostComment(
                            post_id=post_id,
                            author=comment_data['author'],
                            text=comment_data['text'],
                            comment_time=comment_data['comment_time'],
                            likes=comment_data['likes'],
                            extracted_at=datetime.now()
                        )
                        session.add(new_comment)
                
            logger.info(f"Saved {len(comments)} comments for post {post_id}")
            
        except Exception as e:
            logger.error(f"Error saving comments to database: {e}")
    def scrape_post_comments(self, post_id, post_url):
        """Scrape all comments for a specific post"""
        if not self.driver:
            self.start()
            
        try:
            # Navigate to post URL
            logger.info(f"Navigating to post: {post_url}")
            self.driver.get(post_url)
            
            # Wait for page to load with better wait strategy
            try:
                # Wait for main content to appear
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='main'] | //div[@id='content']"))
                )
                logger.info("Post page loaded")
            except TimeoutException:
                logger.warning("Timeout waiting for post page to load, continuing anyway")
            
            # Initial wait for comments to load
            time.sleep(3)
            
            # Try to switch to permalink view if on timeline view (gives better comment access)
            try:
                # Check if we're on a timeline view by looking for date links that might lead to permalink
                date_links = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, '/permalink/') or contains(@href, '/photo.php?') or contains(@href, '/posts/')]"
                )
                
                # If we found potential permalink and we're not already on a permalink URL
                if date_links and not any(x in post_url for x in ['/permalink/', '/photo.php?', '/posts/']):
                    for link in date_links:
                        try:
                            permalink_url = link.get_attribute('href')
                            if permalink_url and ('permalink' in permalink_url or 'posts' in permalink_url or 'photo.php' in permalink_url):
                                logger.info(f"Switching to permalink view: {permalink_url}")
                                self.driver.get(permalink_url)
                                time.sleep(4)  # Wait for permalink to load
                                break
                        except:
                            continue
            except Exception as e:
                logger.debug(f"Error checking for permalink view: {e}")
            
            # Save debug info of the page state
            self.save_page_source(f"post_{post_id}")
            
            # Scroll through the page to ensure all content is loaded
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
            
            # Extract all comments
            comments = self.extract_comments_from_page()
            
            # If we found very few comments, try an alternative approach
            if len(comments) < 3:
                logger.info("Few comments found, trying alternative extraction approach")
                
                # Try clicking on comments count link if present
                try:
                    comment_links = self.driver.find_elements(By.XPATH, 
                        "//a[contains(text(), 'comment') or contains(text(), 'Comment')] | " +
                        "//span[contains(text(), 'comment') or contains(text(), 'Comment')] | " +
                        "//div[@data-testid='UFI2CommentsCount/root']"
                    )
                    
                    if comment_links:
                        logger.info("Found comment count link, attempting to click")
                        for link in comment_links:
                            try:
                                self.driver.execute_script("arguments[0].click();", link)
                                time.sleep(5)  # Wait for comments to expand
                                break
                            except:
                                continue
                        
                        # Try extraction again after clicking
                        comments = self.extract_comments_from_page()
                except Exception as e:
                    logger.debug(f"Error in alternative comment extraction: {e}")
            
            # Take a screenshot of the final state with comments
            screenshot_path = DEBUG_DIR / f"post_{post_id}_with_comments.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Save comments to database
            self.update_post_comments(post_id, comments)
            
            return len(comments)
            
        except Exception as e:
            logger.error(f"Error scraping comments for post {post_id}: {e}")
            self.save_page_source(f"post_error_{post_id}")
            return 0
    
    def get_posts_without_comments(self, limit=10):
        """Get posts that have no comments or few comments"""
        try:
            with self.db.session_scope() as session:
                # Query posts that have URLs and are ordered by fewest comments
                query = session.query(
                    FacebookPost,
                    session.query(PostComment).filter(PostComment.post_id == FacebookPost.post_id).count().label('comment_count')
                ).filter(
                    FacebookPost.post_url.isnot(None)
                ).order_by('comment_count')
                
                posts = query.limit(limit).all()
                
                return [(post.post_id, post.post_url, post.page_name, comment_count) for post, comment_count in posts]
                
        except Exception as e:
            logger.error(f"Error getting posts without comments: {e}")
            return []
    
    def run(self, post_ids=None, limit=20):
        """Main execution function"""
        try:
            # Start browser
            self.start()
            
            # Perform manual login
            if not self.manual_login():
                logger.error("Manual login failed")
                return False
            
            # If specific post IDs provided, scrape those
            if post_ids:
                posts_to_scrape = []
                with self.db.session_scope() as session:
                    for post_id in post_ids:
                        post = session.query(FacebookPost).filter(
                            FacebookPost.post_id == post_id
                        ).first()
                        
                        if post and post.post_url:
                            # Count existing comments
                            comment_count = session.query(PostComment).filter(
                                PostComment.post_id == post_id
                            ).count()
                            posts_to_scrape.append((post.post_id, post.post_url, post.page_name, comment_count))
                        else:
                            logger.warning(f"Post ID {post_id} not found or has no URL")
            else:
                # Otherwise get posts with few/no comments
                posts_to_scrape = self.get_posts_without_comments(limit=limit)
            
            if not posts_to_scrape:
                logger.warning("No posts found to scrape comments from")
                return True
                
            # Scrape comments for each post
            total_comments = 0
            for post_id, post_url, page_name, existing_count in posts_to_scrape:
                logger.info(f"Scraping comments for post {post_id} from {page_name} (current comments: {existing_count})")
                comments_found = self.scrape_post_comments(post_id, post_url)
                total_comments += comments_found
                logger.info(f"Found {comments_found} comments for post {post_id}")
                time.sleep(2)  # Small delay between posts
                
            logger.info(f"Comment scraping completed. Scraped {total_comments} comments from {len(posts_to_scrape)} posts")
            return True
            
        except Exception as e:
            logger.error(f"Error in comment scraper: {e}")
            return False
            
        finally:
            # Always close browser
            self.close()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Facebook Comment Scraper - Enhanced Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape comments from posts with fewest comments (up to 20 posts)
  python comment_scraper.py
  
  # Scrape comments from specific post IDs
  python comment_scraper.py --post-ids 123456789 987654321
  
  # Scrape up to 50 posts with fewest comments
  python comment_scraper.py --limit 50
  
  # Run in headless mode (browser not visible)
  python comment_scraper.py --headless
        """
    )
    
    parser.add_argument('--post-ids', nargs='+', metavar='ID',
                        help='List of specific post IDs to scrape comments from')
                        
    parser.add_argument('--limit', type=int, default=20, metavar='N',
                        help='Maximum number of posts to scrape comments from (default: 20)')
                        
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode (no visible browser)')
                        
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging (more verbose output)')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Ensure directories exist
    LOGS_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    
    # Print banner
    print("\n" + "="*80)
    print("FACEBOOK COMMENT SCRAPER - ENHANCED VERSION")
    print("="*80)
    print("This tool scrapes ALL comments from Facebook posts")
    print("You will need to log in manually to Facebook")
    print("="*80)
    
    # Print settings
    print("\nSETTINGS:")
    if args.post_ids:
        print(f"- Targeting {len(args.post_ids)} specific post(s): {', '.join(args.post_ids[:3])}{'...' if len(args.post_ids) > 3 else ''}")
    else:
        print(f"- Targeting up to {args.limit} posts with fewest comments")
    print(f"- Running in {'headless' if args.headless else 'visible browser'} mode")
    print(f"- Logs will be saved to: {LOGS_DIR}")
    print(f"- Debug files will be saved to: {DEBUG_DIR}")
    print("="*80 + "\n")
    
    # Test database connection first
    try:
        from db.database import DatabaseManager
        db = DatabaseManager()
        # Quick connection test
        with db.session_scope() as session:
            session.execute("SELECT 1")
        print("✅ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check your database settings in db/config.py")
        return 1
      # Initialize and run scraper
    scraper = None  # Initialize to None for safety in finally block
    
    try:
        # Create scraper instance
        scraper = CommentScraper(headless=args.headless, debug=args.debug)
        
        # Show instructions for manual login
        print("IMPORTANT: When the browser opens, you will need to:")
        print("1. Log in with your Facebook credentials")
        print("2. Complete any security checks or CAPTCHAs if prompted")
        print("3. Return to this window and type 'done' when ready\n")
        
        input("Press Enter to start the browser...")
        
        # Run the scraper
        success = scraper.run(post_ids=args.post_ids, limit=args.limit)
        
        if success:
            print("\n" + "="*80)
            print("✅ Comment scraping completed successfully!")
            print("="*80)
            
            # Print summary from database
            try:
                with scraper.db.session_scope() as session:
                    post_count = session.query(FacebookPost).count()
                    comment_count = session.query(PostComment).count()
                    print(f"\nDatabase summary:")
                    print(f"- Total posts: {post_count}")
                    print(f"- Total comments: {comment_count}")
            except Exception:
                pass
            
            return 0
        else:
            print("\n❌ Comment scraping failed!")
            print("Check the logs for more details.")
            return 1
    
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        print("Shutting down gracefully, please wait...")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Unhandled exception in main")
        return 1
    
    finally:
        if scraper:
            try:
                print("Closing browser...")
                scraper.close()
            except Exception:
                pass
            
        print("\nDone.")
        print(f"Check logs for details: {LOGS_DIR / 'comment_scraper.log'}")

if __name__ == "__main__":
    sys.exit(main())
