"""
Post Scraper v2.0 - Robust Facebook post extraction.

Combines the best features from beta and Scraper0.1:
- Detailed post data extraction (Scraper0.1's 1139-line approach)
- Comment modal handling (Scraper0.1)
- Screenshot capture (Scraper0.1)
- Session recovery integration (beta)
- Improved error handling and logging
"""

import logging
import time
import random
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

logger = logging.getLogger(__name__)


@dataclass
class Post:
    """Represents a scraped Facebook post."""
    post_id: str
    page_name: str
    content: str
    post_url: str
    timestamp: Optional[str] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    scraped_at: datetime = field(default_factory=datetime.now)
    comment_list: List[Dict[str, Any]] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'post_id': self.post_id,
            'page_name': self.page_name,
            'content': self.content,
            'post_url': self.post_url,
            'timestamp': self.timestamp,
            'likes': self.likes,
            'comments': self.comments,
            'shares': self.shares,
            'scraped_at': self.scraped_at.isoformat(),
            'comment_list': self.comment_list,
            'media_urls': self.media_urls,
            'metadata': self.metadata
        }


class PostScraper:
    """
    Handles extraction of posts and comments from Facebook pages.
    
    Features:
    - Post content and metadata extraction
    - Comment modal handling
    - Reaction count parsing
    - Screenshot capture
    - Duplicate detection
    """
    
    def __init__(self, browser_manager, config=None):
        """
        Initialize post scraper.
        
        Args:
            browser_manager: BrowserManager instance
            config: Optional configuration object
        """
        from config import get_config
        
        self.browser = browser_manager
        self.config = config or get_config()
        self.scraping_config = self.config.scraping
        
        self.scraped_ids: set = set()
        self.stats = {
            'posts_found': 0,
            'posts_scraped': 0,
            'comments_scraped': 0,
            'errors': 0
        }
    
    # =========================================================================
    # Main Scraping Methods
    # =========================================================================
    
    def scrape_page_posts(
        self, 
        page_url: str, 
        max_posts: int = None,
        scrape_comments: bool = True
    ) -> List[Post]:
        """
        Scrape posts from a Facebook page.
        
        Args:
            page_url: URL of the Facebook page
            max_posts: Maximum number of posts to scrape (uses config default if None)
            scrape_comments: Whether to also scrape comments
            
        Returns:
            List of Post objects
        """
        max_posts = max_posts or self.scraping_config.min_posts_per_page
        posts = []
        
        logger.info(f"Starting to scrape posts from {page_url}")
        
        if not self.browser.navigate_to(page_url):
            logger.error(f"Failed to navigate to {page_url}")
            return posts
        
        time.sleep(3)
        
        # Extract page name
        page_name = self._extract_page_name()
        logger.info(f"Scraping page: {page_name}")
        
        # Scroll and collect posts
        scroll_attempts = 0
        max_scroll_attempts = self.scraping_config.max_scroll_attempts
        
        while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
            # Find post elements
            post_elements = self._find_post_elements()
            logger.debug(f"Found {len(post_elements)} post elements")
            
            for element in post_elements:
                if len(posts) >= max_posts:
                    break
                
                try:
                    post = self._extract_post(element, page_name, scrape_comments)
                    if post and post.post_id not in self.scraped_ids:
                        posts.append(post)
                        self.scraped_ids.add(post.post_id)
                        self.stats['posts_scraped'] += 1
                        logger.info(f"Scraped post {len(posts)}/{max_posts}: {post.post_id[:20]}...")
                except Exception as e:
                    logger.error(f"Error extracting post: {e}")
                    self.stats['errors'] += 1
            
            # Scroll for more posts
            if len(posts) < max_posts:
                scroll_count = self.browser.scroll(steps=3)
                if scroll_count < 2:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                
                time.sleep(random.uniform(1, 2))
        
        logger.info(f"Finished scraping {len(posts)} posts from {page_name}")
        return posts
    
    def _find_post_elements(self) -> List:
        """Find all post elements on the page."""
        driver = self.browser.driver
        
        selectors = [
            'div[data-pagelet^="FeedUnit"]',
            'div[role="article"]',
            'div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z',
            'div[class*="userContent"]',
            '[data-ad-preview="message"]'
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except Exception:
                continue
        
        return []
    
    def _extract_post(
        self, 
        element, 
        page_name: str,
        scrape_comments: bool = True
    ) -> Optional[Post]:
        """
        Extract data from a single post element.
        
        Args:
            element: WebElement containing the post
            page_name: Name of the Facebook page
            scrape_comments: Whether to scrape comments
            
        Returns:
            Post object or None if extraction failed
        """
        driver = self.browser.driver
        
        try:
            # Scroll element into view
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(0.5)
            
            # Extract post ID
            post_id = self._extract_post_id(element)
            if not post_id:
                return None
            
            # Skip if already scraped
            if post_id in self.scraped_ids:
                return None
            
            # Extract content
            content = self._extract_content(element)
            
            # Extract URL
            post_url = self._extract_post_url(element, post_id)
            
            # Extract timestamp
            timestamp = self._extract_timestamp(element)
            
            # Extract reactions (likes, comments, shares)
            likes, comments, shares = self._extract_reactions(element)
            
            # Extract media URLs
            media_urls = self._extract_media_urls(element)
            
            # Create post object
            post = Post(
                post_id=post_id,
                page_name=page_name,
                content=content,
                post_url=post_url,
                timestamp=timestamp,
                likes=likes,
                comments=comments,
                shares=shares,
                media_urls=media_urls
            )
            
            # Scrape comments if requested
            if scrape_comments and comments > 0:
                post.comment_list = self._scrape_post_comments(element, post_id)
            
            self.stats['posts_found'] += 1
            return post
            
        except StaleElementReferenceException:
            logger.debug("Element became stale during extraction")
            return None
        except Exception as e:
            logger.error(f"Error extracting post: {e}")
            return None
    
    # =========================================================================
    # Data Extraction Helpers
    # =========================================================================
    
    def _extract_page_name(self) -> str:
        """Extract the page name from the current page."""
        driver = self.browser.driver
        
        selectors = [
            'h1',
            '[role="heading"][aria-level="1"]',
            'div[data-pagelet="ProfileName"] span',
            'a[role="link"][tabindex="0"] span'
        ]
        
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) > 2:
                    return text
            except NoSuchElementException:
                continue
        
        # Fall back to URL
        try:
            url = driver.current_url
            match = re.search(r'facebook\.com/([^/?]+)', url)
            if match:
                return match.group(1)
        except Exception:
            pass
        
        return "Unknown Page"
    
    def _extract_post_id(self, element) -> Optional[str]:
        """Extract unique post ID from element."""
        driver = self.browser.driver
        
        try:
            # Try to find permalink
            link_selectors = [
                'a[href*="/posts/"]',
                'a[href*="/permalink/"]',
                'a[href*="/photos/"]',
                'a[href*="story_fbid"]',
                'a[href*="/watch/"]'
            ]
            
            for selector in link_selectors:
                try:
                    links = element.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href:
                            # Extract ID from URL
                            patterns = [
                                r'/posts/(\d+)',
                                r'/permalink/(\d+)',
                                r'story_fbid=(\d+)',
                                r'/photos/[^/]+/(\d+)',
                                r'/watch/\?v=(\d+)'
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, href)
                                if match:
                                    return match.group(1)
                except Exception:
                    continue
            
            # Fall back to element attributes
            for attr in ['data-story-id', 'data-ft', 'id']:
                try:
                    value = element.get_attribute(attr)
                    if value:
                        # Extract any numeric ID
                        match = re.search(r'(\d{10,})', value)
                        if match:
                            return match.group(1)
                except Exception:
                    continue
            
            # Generate hash-based ID as last resort
            try:
                content = element.text[:100] if element.text else ""
                import hashlib
                return hashlib.md5(content.encode()).hexdigest()[:16]
            except Exception:
                return None
                
        except Exception as e:
            logger.debug(f"Error extracting post ID: {e}")
            return None
    
    def _extract_content(self, element) -> str:
        """Extract text content from post."""
        content_selectors = [
            'div[data-ad-preview="message"]',
            'div[dir="auto"]',
            '[data-ad-comet-preview="message"]',
            'div.xdj266r',
            'span.x193iq5w'
        ]
        
        for selector in content_selectors:
            try:
                content_elements = element.find_elements(By.CSS_SELECTOR, selector)
                texts = []
                for el in content_elements:
                    text = el.text.strip()
                    if text and len(text) > 10:
                        texts.append(text)
                if texts:
                    return max(texts, key=len)
            except Exception:
                continue
        
        # Fall back to full element text
        try:
            return element.text.strip()[:2000]
        except Exception:
            return ""
    
    def _extract_post_url(self, element, post_id: str) -> str:
        """Extract or construct post URL."""
        try:
            link_selectors = [
                'a[href*="/posts/"]',
                'a[href*="/permalink/"]'
            ]
            for selector in link_selectors:
                try:
                    link = element.find_element(By.CSS_SELECTOR, selector)
                    href = link.get_attribute('href')
                    if href and 'facebook.com' in href:
                        return href.split('?')[0]
                except NoSuchElementException:
                    continue
        except Exception:
            pass
        
        # Construct from post ID
        page_name = self._extract_page_name()
        return f"https://www.facebook.com/{page_name}/posts/{post_id}"
    
    def _extract_timestamp(self, element) -> Optional[str]:
        """Extract post timestamp."""
        time_selectors = [
            'a[href*="/posts/"] span',
            'abbr[data-utime]',
            'span[id*="jsc"] a',
            'a[role="link"] span[aria-labelledby]'
        ]
        
        for selector in time_selectors:
            try:
                time_elements = element.find_elements(By.CSS_SELECTOR, selector)
                for el in time_elements:
                    text = el.text.strip()
                    if self._is_timestamp_text(text):
                        return text
                    
                    # Check title/aria-label
                    for attr in ['title', 'aria-label']:
                        attr_value = el.get_attribute(attr)
                        if attr_value and self._is_timestamp_text(attr_value):
                            return attr_value
            except Exception:
                continue
        
        return None
    
    def _is_timestamp_text(self, text: str) -> bool:
        """Check if text looks like a timestamp."""
        if not text:
            return False
        text = text.lower()
        patterns = [
            r'\d{1,2}[:/]\d{2}',
            r'(minute|hour|day|week|month|year|hr|min)s?\s*(ago)?',
            r'(yesterday|today|just now)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
        ]
        return any(re.search(p, text) for p in patterns)
    
    def _extract_reactions(self, element) -> Tuple[int, int, int]:
        """Extract like, comment, and share counts."""
        likes = 0
        comments = 0
        shares = 0
        
        try:
            # Find reaction section
            reaction_selectors = [
                'div[role="button"] span',
                'span.x1n2onr6',
                'span[data-hover]',
                'a[role="button"] span'
            ]
            
            for selector in reaction_selectors:
                try:
                    spans = element.find_elements(By.CSS_SELECTOR, selector)
                    for span in spans:
                        text = span.text.strip().lower()
                        
                        if not text:
                            continue
                        
                        # Parse counts
                        count = self._parse_count(text)
                        
                        if 'comment' in text:
                            comments = count
                        elif 'share' in text:
                            shares = count
                        elif count > 0 and likes == 0:
                            # Assume first number without label is likes
                            likes = count
                            
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error extracting reactions: {e}")
        
        return likes, comments, shares
    
    def _parse_count(self, text: str) -> int:
        """Parse a count from text like '1.5K' or '2,500'."""
        try:
            text = text.strip().lower()
            
            # Extract number part
            match = re.search(r'([\d.,]+)\s*([kmb])?', text)
            if not match:
                return 0
            
            number_str = match.group(1).replace(',', '')
            multiplier_char = match.group(2)
            
            number = float(number_str)
            
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
            if multiplier_char and multiplier_char in multipliers:
                number *= multipliers[multiplier_char]
            
            return int(number)
            
        except Exception:
            return 0
    
    def _extract_media_urls(self, element) -> List[str]:
        """Extract media (image/video) URLs from post."""
        urls = []
        
        try:
            # Images
            images = element.find_elements(By.CSS_SELECTOR, 'img[src*="fbcdn"]')
            for img in images[:5]:
                src = img.get_attribute('src')
                if src and 'scontent' in src:
                    urls.append(src)
            
            # Videos
            videos = element.find_elements(By.CSS_SELECTOR, 'video source')
            for video in videos[:3]:
                src = video.get_attribute('src')
                if src:
                    urls.append(src)
                    
        except Exception as e:
            logger.debug(f"Error extracting media URLs: {e}")
        
        return urls
    
    # =========================================================================
    # Comment Scraping
    # =========================================================================
    
    def _scrape_post_comments(
        self, 
        element, 
        post_id: str, 
        max_comments: int = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape comments from a post.
        
        Args:
            element: Post WebElement
            post_id: Post ID for logging
            max_comments: Maximum comments to scrape
            
        Returns:
            List of comment dictionaries
        """
        max_comments = max_comments or self.scraping_config.max_comments_per_post
        comments = []
        
        try:
            # Click to expand comments
            if not self._open_comments(element):
                return comments
            
            time.sleep(2)
            
            # Find comment elements
            comment_elements = self._find_comment_elements(element)
            
            for comment_el in comment_elements[:max_comments]:
                try:
                    comment = self._extract_comment(comment_el)
                    if comment:
                        comments.append(comment)
                        self.stats['comments_scraped'] += 1
                except Exception as e:
                    logger.debug(f"Error extracting comment: {e}")
            
            # Close modal if opened
            self._close_modal()
            
            logger.debug(f"Scraped {len(comments)} comments from post {post_id[:10]}")
            
        except Exception as e:
            logger.error(f"Error scraping comments for post {post_id[:10]}: {e}")
        
        return comments
    
    def _open_comments(self, element) -> bool:
        """Click to open/expand comments."""
        driver = self.browser.driver
        
        selectors = [
            'div[role="button"] span:contains("comment")',
            'a[role="button"][href*="comment"]',
            'span[role="button"]',
            'div[aria-label*="comment"]'
        ]
        
        # Try text-based selection
        try:
            buttons = element.find_elements(By.CSS_SELECTOR, 'div[role="button"], a[role="button"]')
            for btn in buttons:
                text = btn.text.lower()
                if 'comment' in text and any(c.isdigit() for c in text):
                    self.browser.click_element(btn)
                    return True
        except Exception:
            pass
        
        return False
    
    def _find_comment_elements(self, parent_element) -> List:
        """Find comment elements within a post or modal."""
        driver = self.browser.driver
        
        selectors = [
            'div[aria-label*="Comment"]',
            'ul[role="list"] li',
            'div[data-testid="UFI2Comment/root_depth_0"]',
            'div.x1n2onr6.x1ja2u2z'
        ]
        
        for selector in selectors:
            try:
                comments = parent_element.find_elements(By.CSS_SELECTOR, selector)
                if len(comments) > 3:
                    return comments
            except Exception:
                continue
        
        return []
    
    def _extract_comment(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single comment element."""
        try:
            # Author
            author = ""
            author_selectors = ['a[role="link"]', 'span[dir="auto"] a']
            for selector in author_selectors:
                try:
                    author_el = element.find_element(By.CSS_SELECTOR, selector)
                    author = author_el.text.strip()
                    if author:
                        break
                except NoSuchElementException:
                    continue
            
            # Content
            content = ""
            content_selectors = ['div[dir="auto"]', 'span[lang]', 'span.xdj266r']
            for selector in content_selectors:
                try:
                    content_el = element.find_element(By.CSS_SELECTOR, selector)
                    content = content_el.text.strip()
                    if content and content != author:
                        break
                except NoSuchElementException:
                    continue
            
            if not content:
                return None
            
            return {
                'author': author or 'Unknown',
                'content': content,
                'timestamp': None,
                'likes': 0,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Error extracting comment: {e}")
            return None
    
    def _close_modal(self):
        """Close any open modal/dialog."""
        driver = self.browser.driver
        
        close_selectors = [
            '[aria-label="Close"]',
            '[data-testid="dialog-close-button"]',
            'div[role="dialog"] button[aria-label*="close"]'
        ]
        
        for selector in close_selectors:
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if close_btn.is_displayed():
                    close_btn.click()
                    time.sleep(0.5)
                    return
            except Exception:
                continue
        
        # Press Escape as fallback
        try:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except Exception:
            pass
    
    # =========================================================================
    # Screenshot Capture
    # =========================================================================
    
    def capture_screenshot(
        self, 
        element=None, 
        filename: str = None
    ) -> Optional[str]:
        """
        Capture a screenshot of an element or the full page.
        
        Args:
            element: WebElement to screenshot (page if None)
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to saved screenshot or None
        """
        try:
            screenshot_dir = Path(self.config.database.data_dir) / 'screenshots'
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"screenshot_{timestamp}.png"
            
            filepath = screenshot_dir / filename
            
            if element:
                element.screenshot(str(filepath))
            else:
                self.browser.driver.save_screenshot(str(filepath))
            
            logger.debug(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset scraping statistics."""
        self.stats = {
            'posts_found': 0,
            'posts_scraped': 0,
            'comments_scraped': 0,
            'errors': 0
        }
