"""
Post Scraper v2.0
==================
Comprehensive post and comment extraction combining ALL features from:
- beta/scraper/post_scraper.py
- Scraper0.1/scraper/post_scraper.py (1139 lines)

Features:
- Robust modal detection (role="dialog", aria-modal)
- Multiple click strategies (element.click, JS click, ActionChains)
- click_comment_button() with 3 fallback strategies (label/icon/position)
- BeautifulSoup HTML parsing for comment extraction
- Mobile fallback scraping
- Debug HTML saving on failures
- Modal scrolling for loading more comments
- Comment deduplication
- Screenshot capture
- Post metadata extraction
"""

import os
import re
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False
    BeautifulSoup = None

try:
    import dateparser
    HAS_DATEPARSER = True
except ImportError:
    HAS_DATEPARSER = False

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Remove unwanted text and normalize whitespace."""
    if not text:
        return ""
    # Remove common paywall messages
    paywall_messages = [
        "Та эрхээ сунгаж үзвэрээ үзнэ үү!",
        "You must log in to continue",
        "Log in to Facebook",
    ]
    for msg in paywall_messages:
        text = text.replace(msg, "")
    return text.strip()


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Make string safe for use as filename."""
    if not name:
        return "unnamed"
    # Remove/replace invalid characters
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.replace('=', '_').replace('?', '_').replace('&', '_')
    # Truncate
    if len(name) > max_length:
        name = name[:max_length]
    return name


class PostScraper:
    """
    Comprehensive Facebook post and comment scraper.
    
    Features:
    - Multiple modal opening strategies
    - Robust comment extraction with BeautifulSoup
    - Mobile fallback for comments
    - Deduplication
    - Debug HTML saving
    """
    
    def __init__(self, browser_manager, config=None):
        """
        Initialize PostScraper.
        
        Args:
            browser_manager: BrowserManager instance
            config: Configuration object (uses defaults if None)
        """
        self.browser = browser_manager
        self.driver = browser_manager.driver
        self.wait = browser_manager.wait
        
        if config is None:
            from config import get_config
            config = get_config()
        self.config = config
        
        # Directories
        self.data_dir = Path(config.database.data_dir)
        self.debug_dir = self.data_dir / 'debug'
        self.screenshots_dir = self.data_dir / 'screenshots'
        self.comments_dir = self.data_dir / 'comments'
        
        # Create directories
        for d in [self.debug_dir, self.screenshots_dir, self.comments_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Database manager (initialized lazily)
        self._db = None
        
    @property
    def db(self):
        """Lazy load database manager."""
        if self._db is None:
            try:
                from db.database import DatabaseManager
                self._db = DatabaseManager()
            except Exception as e:
                logger.warning(f"Database not available: {e}")
        return self._db
        
    # =========================================================================
    # SCROLLING METHODS
    # =========================================================================
    
    def scroll_page(self, scrolls: int = 20, pause: float = 2.0, min_new_posts: int = 2):
        """
        Scroll page to load more content.
        
        Args:
            scrolls: Maximum number of scroll attempts
            pause: Pause between scrolls (seconds)
            min_new_posts: Minimum new posts to continue scrolling
        """
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(scrolls):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(pause)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.debug(f"Page height unchanged after scroll {i+1}, stopping")
                return
            last_height = new_height
            
    def scroll_until_posts(self, selectors: List[str], max_scrolls: int = 30, pause: float = 2.0) -> bool:
        """
        Scroll until at least one post is found.
        
        Args:
            selectors: CSS selectors to look for
            max_scrolls: Maximum scroll attempts
            pause: Pause between scrolls
            
        Returns:
            bool: Whether posts were found
        """
        for i in range(max_scrolls):
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return True
                    
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(pause)
            
        return False
        
    def slow_scroll(self, step: int = 500, pause: float = 2.0):
        """Scroll page slowly by given pixel amount."""
        self.driver.execute_script(f"window.scrollBy(0, {step});")
        time.sleep(pause)
        
    def scroll_container(self, container: WebElement, amount: int = 200, pause: float = 0.5):
        """Scroll within a container element."""
        self.driver.execute_script("arguments[0].scrollBy(0, arguments[1]);", container, amount)
        time.sleep(pause)
        
    # =========================================================================
    # MODAL HANDLING (from Scraper0.1)
    # =========================================================================
    
    def find_modal(self) -> Optional[WebElement]:
        """
        Find the current modal/dialog element.
        
        Returns:
            WebElement or None
        """
        modal_selectors = [
            'div[role="dialog"]',
            'div[aria-modal="true"]',
            'div[aria-label*="Post"]',
            'div[aria-label="Comments"]',
        ]
        
        for selector in modal_selectors:
            try:
                modal = self.driver.find_element(By.CSS_SELECTOR, selector)
                if modal.is_displayed():
                    return modal
            except NoSuchElementException:
                continue
                
        return None
        
    def close_modal(self) -> bool:
        """
        Close the current modal dialog.
        
        Returns:
            bool: Whether modal was closed successfully
        """
        try:
            # Strategy 1: Press Escape
            body = self.driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            
            # Check if modal closed
            if not self.find_modal():
                return True
                
            # Strategy 2: Click close button
            close_selectors = [
                'div[aria-label="Close"]',
                'div[aria-label="close"]',
                'button[aria-label="Close"]',
                'svg[aria-label="Close"]',
                '[data-testid="close-button"]',
            ]
            
            for selector in close_selectors:
                try:
                    close_btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in close_btns:
                        if btn.is_displayed():
                            btn.click()
                            time.sleep(0.5)
                            if not self.find_modal():
                                return True
                except Exception:
                    continue
                    
            logger.warning("Modal may not have closed properly")
            return False
            
        except Exception as e:
            logger.error(f"Error closing modal: {e}")
            return False
            
    def click_comment_button(self) -> bool:
        """
        Robustly click the comment button for a post.
        Uses 3 fallback strategies from Scraper0.1:
        1. By label text ("Comment", etc.)
        2. By SVG icon
        3. By position (middle button)
        
        Returns:
            bool: Whether comment button was clicked
        """
        try:
            # Find modal first
            modal = self.find_modal()
            if not modal:
                logger.warning("No modal found for comment button click")
                return False
                
            # Find footer area (where Like/Comment/Share buttons are)
            footer = self._find_modal_footer(modal)
            if not footer:
                logger.info("No footer found for comment button - post may have no comments")
                self._save_debug_html(modal.get_attribute("outerHTML"), "modal_no_footer")
                return False
                
            # Get all buttons in footer
            buttons = footer.find_elements(By.XPATH, ".//div[@role='button']")
            
            # Strategy 1: By label/text
            comment_btn = self._find_button_by_label(buttons, 
                ['comment', 'сэтгэгдэл', 'write a comment', 'leave a comment'])
            
            # Strategy 2: By SVG icon
            if not comment_btn:
                comment_btn = self._find_button_by_svg(buttons, ['comment'])
                
            # Strategy 3: By position (usually middle button of 3)
            if not comment_btn:
                comment_btn = self._find_button_by_position(buttons)
                
            if comment_btn:
                return self._click_with_fallback(comment_btn)
                
            logger.warning("Could not find comment button with any strategy")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking comment button: {e}")
            return False
            
    def _find_modal_footer(self, modal: WebElement) -> Optional[WebElement]:
        """Find the footer/toolbar area of a modal."""
        footer_selectors = [
            'footer',
            'div[role="toolbar"]',
            'div[aria-label*="actions"]',
            'div[aria-label*="Footer"]',
            'div[role="group"]',
        ]
        
        for selector in footer_selectors:
            try:
                footers = modal.find_elements(By.CSS_SELECTOR, selector)
                for footer in footers:
                    # Look for footer with 3-5 buttons (Like, Comment, Share pattern)
                    buttons = footer.find_elements(By.XPATH, ".//div[@role='button']")
                    if 2 < len(buttons) < 6:
                        return footer
            except Exception:
                continue
                
        return None
        
    def _find_button_by_label(self, buttons: List[WebElement], labels: List[str]) -> Optional[WebElement]:
        """Find button by text label or aria-label."""
        for btn in buttons:
            try:
                text = btn.text.strip().lower()
                aria = (btn.get_attribute("aria-label") or "").lower()
                if any(label in text or label in aria for label in labels):
                    return btn
            except Exception:
                continue
        return None
        
    def _find_button_by_svg(self, buttons: List[WebElement], keywords: List[str]) -> Optional[WebElement]:
        """Find button by SVG icon attributes."""
        for btn in buttons:
            try:
                svg = btn.find_element(By.XPATH, ".//svg")
                aria = (svg.get_attribute("aria-label") or "").lower()
                data_testid = (svg.get_attribute("data-testid") or "").lower()
                if any(kw in aria or kw in data_testid for kw in keywords):
                    return btn
            except Exception:
                continue
        return None
        
    def _find_button_by_position(self, buttons: List[WebElement]) -> Optional[WebElement]:
        """Find middle button (usually Comment in Like/Comment/Share)."""
        if len(buttons) >= 3:
            return buttons[len(buttons) // 2]
        elif len(buttons) == 2:
            return buttons[1]  # Might be Comment if only 2 buttons
        return None
        
    def _click_with_fallback(self, element: WebElement) -> bool:
        """Click element with multiple fallback strategies."""
        try:
            # Scroll into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(0.2)
            
            # Strategy 1: Direct click
            try:
                element.click()
                time.sleep(0.3)
                return True
            except (ElementClickInterceptedException, ElementNotInteractableException):
                pass
                
            # Strategy 2: JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(0.3)
                return True
            except Exception:
                pass
                
            # Strategy 3: ActionChains
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
                time.sleep(0.3)
                return True
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"All click strategies failed: {e}")
            
        return False
        
    # =========================================================================
    # COMMENT EXTRACTION (from Scraper0.1)
    # =========================================================================
    
    def extract_comments(self, post_id: str, max_comments: int = 50) -> List[Dict[str, Any]]:
        """
        Extract comments from current modal with all strategies.
        
        Args:
            post_id: Post identifier
            max_comments: Maximum number of comments to extract
            
        Returns:
            List of comment dictionaries
        """
        # Try modal extraction first
        comments = self._extract_modal_comments(post_id, max_comments)
        
        # Fall back to mobile scraping if needed
        if not comments and self.config.scraping.use_mobile_fallback:
            logger.info(f"Trying mobile fallback for post {post_id}")
            comments, _ = self._scrape_comments_mobile(post_id, max_comments)
            
        return comments
        
    def _extract_modal_comments(self, post_id: str, max_comments: int = 50) -> List[Dict[str, Any]]:
        """
        Extract comments from modal using BeautifulSoup.
        
        Args:
            post_id: Post identifier
            max_comments: Maximum comments to extract
            
        Returns:
            List of comment dictionaries
        """
        if not HAS_BEAUTIFULSOUP:
            logger.warning("BeautifulSoup not available, using fallback extraction")
            return self._extract_comments_selenium(post_id, max_comments)
            
        comments = []
        seen_texts = set()
        
        try:
            # Find modal
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, "//div[@role='dialog' or @aria-modal='true']"
                ))
            )
            
            # Find scrollable area
            scrollable = self._find_scrollable_container(modal)
            if not scrollable:
                scrollable = modal
                
            # Scroll and extract
            last_height = 0
            scroll_attempts = 0
            
            while len(comments) < max_comments and scroll_attempts < 30:
                # Scroll
                self.driver.execute_script("arguments[0].scrollBy(0, 200);", scrollable)
                time.sleep(0.5)
                
                # Check for "no comments" message
                if self._check_no_comments(modal):
                    logger.info(f"No comments message detected for post {post_id}")
                    break
                    
                # Parse with BeautifulSoup
                soup = BeautifulSoup(modal.get_attribute('innerHTML'), 'html.parser')
                
                # Extract comments using multiple selectors
                new_comments = self._extract_comments_from_soup(soup, seen_texts, post_id)
                comments.extend(new_comments)
                
                if len(comments) >= max_comments:
                    break
                    
                # Click "View more comments" if present
                self._click_view_more_comments(scrollable)
                
                # Check if scroll made progress
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollTop;", scrollable
                )
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        logger.info(f"Scroll stopped progressing for post {post_id}")
                        break
                else:
                    scroll_attempts = 0
                    last_height = new_height
                    
            logger.info(f"Extracted {len(comments)} comments from modal for post {post_id}")
            
        except TimeoutException:
            logger.warning(f"Modal not found for post {post_id}")
        except Exception as e:
            logger.error(f"Error extracting modal comments for post {post_id}: {e}")
            self._save_debug_html(self.driver.page_source, f"modal_error_{post_id}")
            
        return comments[:max_comments]
        
    def _extract_comments_from_soup(self, soup: BeautifulSoup, seen: set, post_id: str) -> List[Dict]:
        """Extract comments from BeautifulSoup parsed HTML."""
        comments = []
        
        # Facebook comment selectors
        comment_selectors = [
            {'aria-label': 'Comment'},
            {'role': 'article'},
            {'data-testid': 'comment'},
        ]
        
        for attrs in comment_selectors:
            for elem in soup.find_all(['div', 'article'], attrs=attrs):
                text = elem.get_text(separator=' ', strip=True)
                text = clean_text(text)
                
                if text and text not in seen and len(text) > 5:
                    # Extract author if possible
                    author = None
                    author_elem = elem.find('a', href=re.compile(r'/profile|/user'))
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        
                    comment = {
                        'post_id': post_id,
                        'author': author,
                        'text': text,
                        'extracted_at': datetime.now().isoformat(),
                    }
                    comments.append(comment)
                    seen.add(text)
                    logger.debug(f"[Comment] {text[:100]}...")
                    
        return comments
        
    def _extract_comments_selenium(self, post_id: str, max_comments: int = 50) -> List[Dict]:
        """Fallback comment extraction using pure Selenium."""
        comments = []
        seen = set()
        
        comment_selectors = [
            "//div[@aria-label='Comment']",
            "//div[@role='article' and contains(@class, 'comment')]",
            "//div[contains(@data-testid, 'comment')]",
        ]
        
        for selector in comment_selectors:
            elements = self.driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if len(comments) >= max_comments:
                    break
                try:
                    text = clean_text(elem.text)
                    if text and text not in seen and len(text) > 5:
                        comments.append({
                            'post_id': post_id,
                            'author': None,
                            'text': text,
                            'extracted_at': datetime.now().isoformat(),
                        })
                        seen.add(text)
                except StaleElementReferenceException:
                    continue
                    
        return comments
        
    def _scrape_comments_mobile(self, post_id: str, max_comments: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """
        Mobile fallback for comment scraping (from Scraper0.1).
        
        Returns:
            Tuple of (comments list, screenshot path)
        """
        comments = []
        screenshot_path = None
        
        try:
            if not HAS_BEAUTIFULSOUP:
                return [], None
                
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Mobile comment selectors
            comment_blocks = soup.find_all('div', {'data-sigil': 'comment'})
            if not comment_blocks:
                comment_blocks = soup.find_all('div', class_=re.compile(r'comment'))
                
            for block in comment_blocks[:max_comments]:
                author = block.find('h3')
                text_elem = block.find('div', {'data-sigil': 'comment-body'})
                if not text_elem:
                    text_elem = block.find('span')
                    
                comment = {
                    'post_id': post_id,
                    'author': author.text.strip() if author else None,
                    'text': clean_text(text_elem.text if text_elem else block.text),
                    'extracted_at': datetime.now().isoformat(),
                }
                comments.append(comment)
                
            if not comments:
                # Save fallback HTML for debugging
                html_file = self._save_debug_html(
                    self.driver.page_source, f"mobile_fallback_{post_id}"
                )
                comments = [{
                    'post_id': post_id,
                    'text': 'NO_COMMENTS_FOUND_MOBILE',
                    'fallback_html_file': html_file,
                }]
                
        except Exception as e:
            logger.error(f"Mobile comment scrape failed: {e}")
            html_file = self._save_debug_html(
                self.driver.page_source, f"mobile_error_{post_id}"
            )
            comments = [{
                'post_id': post_id,
                'text': f'ERROR_MOBILE_SCRAPE: {e}',
                'fallback_html_file': html_file,
            }]
            
        return comments, screenshot_path
        
    def _find_scrollable_container(self, modal: WebElement) -> Optional[WebElement]:
        """Find scrollable container within modal."""
        for candidate in modal.find_elements(By.XPATH, ".//*"):
            try:
                overflow = candidate.value_of_css_property("overflow-y")
                height = candidate.size.get("height", 0)
                if overflow in ("auto", "scroll") and height > 200:
                    return candidate
            except Exception:
                continue
        return None
        
    def _check_no_comments(self, modal: WebElement) -> bool:
        """Check if modal shows "no comments" message."""
        no_comment_messages = [
            "Сэтгэгдэл хараахан алга",
            "No comments yet",
            "Be the first to comment",
        ]
        try:
            modal_text = modal.text
            return any(msg in modal_text for msg in no_comment_messages)
        except Exception:
            return False
            
    def _click_view_more_comments(self, container: WebElement):
        """Click "View more comments" buttons if present."""
        view_more_selectors = [
            ".//div[@role='button' and contains(text(), 'View more comments')]",
            ".//div[@role='button' and contains(text(), 'See more comments')]",
            ".//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
        ]
        
        for selector in view_more_selectors:
            try:
                buttons = container.find_elements(By.XPATH, selector)
                for btn in buttons[:3]:
                    try:
                        btn.click()
                        time.sleep(0.5)
                    except Exception:
                        continue
            except Exception:
                continue
                
    # =========================================================================
    # POST SCRAPING
    # =========================================================================
    
    def scrape_post(self, post_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single post.
        
        Args:
            post_url: URL of the post
            
        Returns:
            Post data dictionary or None
        """
        try:
            self.driver.get(post_url)
            self.wait.until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Wait for content to load
            time.sleep(2)
            
            # Find content
            content = self._extract_post_content()
            post_id = self._extract_post_id_from_url(post_url)
            
            return {
                'url': post_url,
                'post_id': post_id,
                'content': content,
                'scraped_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.warning(f"Failed to scrape post {post_url}: {e}")
            return None
            
    def scrape_posts_on_page(self, page_url: str, max_posts: int = 10) -> int:
        """
        Scrape posts from a Facebook page.
        
        Args:
            page_url: URL of the Facebook page
            max_posts: Maximum number of posts to scrape
            
        Returns:
            Number of posts scraped
        """
        if not self.browser.navigate_to(page_url):
            logger.error(f"Failed to navigate to {page_url}")
            return 0
            
        # Wait for main content
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]'))
            )
        except TimeoutException:
            logger.error(f"Page main content not found: {page_url}")
            return 0
            
        scraped = 0
        post_idx = 0
        
        while scraped < max_posts:
            try:
                # Re-fetch posts to avoid stale element issues
                posts = self.driver.find_elements(By.XPATH, "//div[@role='article']")
                if post_idx >= len(posts):
                    # Try scrolling to load more
                    self.slow_scroll()
                    posts = self.driver.find_elements(By.XPATH, "//div[@role='article']")
                    if post_idx >= len(posts):
                        logger.info("No more posts found")
                        break
                        
                post_elem = posts[post_idx]
                post_id = self._extract_post_id_from_element(post_elem)
                
                if not post_id:
                    post_idx += 1
                    continue
                    
                # Extract comments using modal-first approach
                comments = self._extract_comments_modal_first(post_elem, post_id)
                
                # Save comments
                if comments:
                    self._save_comments(comments, post_id)
                    if self.db:
                        self.db.save_comments(comments, post_id)
                        
                scraped += 1
                post_idx += 1
                logger.info(f"Scraped post {post_id}: {len(comments)} comments")
                
            except StaleElementReferenceException:
                logger.warning("Stale element, re-fetching posts")
                post_idx += 1
                continue
            except Exception as e:
                logger.error(f"Error scraping post at index {post_idx}: {e}")
                self.close_modal()
                post_idx += 1
                continue
                
        logger.info(f"Scraped {scraped} posts from {page_url}")
        return scraped
        
    def _extract_comments_modal_first(self, post_elem: WebElement, post_id: str) -> List[Dict]:
        """
        Open modal and extract comments.
        
        Args:
            post_elem: Post element
            post_id: Post identifier
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        modal_opened = False
        
        try:
            # Try multiple strategies to open modal
            modal_opened = self._open_post_modal(post_elem)
            
            if modal_opened:
                # Wait for modal to load
                time.sleep(1)
                
                # Click comment button if needed
                self.click_comment_button()
                
                # Extract comments
                comments = self.extract_comments(
                    post_id, 
                    self.config.scraping.max_comments_per_post
                )
                
        except Exception as e:
            logger.warning(f"Modal extraction failed for post {post_id}: {e}")
            
        finally:
            if modal_opened:
                self.close_modal()
                time.sleep(0.5)
                
        return comments
        
    def _open_post_modal(self, post_elem: WebElement) -> bool:
        """
        Open modal for a post using multiple strategies.
        
        Returns:
            bool: Whether modal was opened
        """
        strategies = [
            # Strategy 1: Click timestamp link
            lambda e: self._click_timestamp(e),
            # Strategy 2: Click comment button
            lambda e: self._click_comment_area(e),
            # Strategy 3: Click post container
            lambda e: self._click_post_body(e),
            # Strategy 4: Click video button (for video posts)
            lambda e: self._click_video_button(e),
        ]
        
        for strategy in strategies:
            try:
                if strategy(post_elem):
                    # Verify modal opened
                    time.sleep(1)
                    if self.find_modal():
                        return True
            except Exception:
                continue
                
        return False
        
    def _click_timestamp(self, post_elem: WebElement) -> bool:
        """Click timestamp link to open post modal."""
        selectors = [
            ".//a[contains(@href, '/posts/')]",
            ".//a[contains(@href, '/videos/')]",
            ".//a[contains(@href, '/photos/')]",
            ".//abbr/ancestor::a",
        ]
        for selector in selectors:
            try:
                link = post_elem.find_element(By.XPATH, selector)
                link.click()
                return True
            except NoSuchElementException:
                continue
        return False
        
    def _click_comment_area(self, post_elem: WebElement) -> bool:
        """Click comment area to open modal."""
        selectors = [
            ".//div[@aria-label='Leave a comment']",
            ".//div[@aria-label='Comment']",
            ".//span[contains(text(), 'Comment')]/ancestor::div[@role='button']",
        ]
        for selector in selectors:
            try:
                btn = post_elem.find_element(By.XPATH, selector)
                btn.click()
                return True
            except NoSuchElementException:
                continue
        return False
        
    def _click_post_body(self, post_elem: WebElement) -> bool:
        """Click post body to open modal."""
        try:
            post_elem.click()
            return True
        except Exception:
            return False
            
    def _click_video_button(self, post_elem: WebElement) -> bool:
        """Click video play button to open modal."""
        selectors = [
            ".//div[contains(@aria-label, 'Play video')]",
            ".//div[contains(@aria-label, 'Watch')]",
            ".//div[@role='button']//video/ancestor::div[@role='button']",
        ]
        for selector in selectors:
            try:
                btn = post_elem.find_element(By.XPATH, selector)
                btn.click()
                return True
            except NoSuchElementException:
                continue
        return False
        
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _extract_post_content(self) -> str:
        """Extract main post content text."""
        content_selectors = [
            'div[data-ad-preview="message"]',
            'div[data-ad-comet-preview="message"]',
            '[data-testid="post_message"]',
            'div[dir="auto"]',
        ]
        
        for selector in content_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                return clean_text(elem.text)
            except NoSuchElementException:
                continue
                
        return ""
        
    def _extract_post_id_from_url(self, url: str) -> str:
        """Extract post ID from URL."""
        patterns = [
            r'/posts/(\d+)',
            r'/videos/(\d+)',
            r'/photos/.*?/(\d+)',
            r'story_fbid=(\d+)',
            r'id=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return sanitize_filename(url.split('/')[-1])
        
    def _extract_post_id_from_element(self, elem: WebElement) -> Optional[str]:
        """Extract post ID from element attributes."""
        try:
            # Try data attributes
            for attr in ['data-ft', 'data-post-id', 'id']:
                value = elem.get_attribute(attr)
                if value:
                    # Extract numeric ID if present
                    match = re.search(r'(\d{10,})', value)
                    if match:
                        return match.group(1)
                    return sanitize_filename(value)
                    
            # Try finding link with post ID
            links = elem.find_elements(By.XPATH, ".//a[contains(@href, '/posts/')]")
            for link in links:
                href = link.get_attribute('href')
                if href:
                    post_id = self._extract_post_id_from_url(href)
                    if post_id:
                        return post_id
                        
        except Exception:
            pass
            
        return f"unknown_{int(time.time())}"
        
    def _save_comments(self, comments: List[Dict], post_id: str):
        """Save comments to JSON file."""
        try:
            filename = self.comments_dir / f"{sanitize_filename(post_id)}_comments.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(comments)} comments to {filename}")
        except Exception as e:
            logger.error(f"Failed to save comments: {e}")
            
    def _save_debug_html(self, html: str, prefix: str) -> str:
        """Save HTML for debugging."""
        try:
            filename = self.debug_dir / f"{prefix}_{int(time.time())}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            return str(filename)
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
            return ""
            
    def take_screenshot(self, element: WebElement = None, filename: str = None) -> Optional[str]:
        """
        Take screenshot of element or page.
        
        Args:
            element: Element to screenshot (page if None)
            filename: Output filename
            
        Returns:
            Path to screenshot or None
        """
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
                
            filepath = self.screenshots_dir / filename
            
            if element:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", element
                )
                time.sleep(0.2)
                element.screenshot(str(filepath))
            else:
                self.driver.save_screenshot(str(filepath))
                
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
