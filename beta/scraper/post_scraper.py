from pathlib import Path
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException
)

# Configure logging
logger = logging.getLogger(__name__)

def clean_text(text):
    if not text:
        return text
    return text.replace("Та эрхээ сунгаж үзвэрээ үзнэ үү!", "").strip()

class PostScraper:
    """Component responsible for scraping posts from Facebook pages"""
    def __init__(self, driver: webdriver.Firefox, max_comments: int = 100,
                 take_screenshots: bool = True, download_images: bool = True):
        """
        Initialize the post scraper
        
        Args:
            driver: Selenium WebDriver instance
            max_comments: Maximum number of comments to scrape per post
            take_screenshots: Whether to capture screenshots of posts
            download_images: Whether to download post images
        """
        self.driver = driver
        self.max_comments = max_comments
        self.take_screenshots = take_screenshots
        self.download_images = download_images
        self.wait = WebDriverWait(driver, 20)  # Increased wait time
        
    def get_posts(self, page_name: str) -> List[Dict[str, Any]]:
        """
        Get posts from a Facebook page
        
        Args:
            page_name: Name of the Facebook page to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        posts = []
        try:
            # Facebook page variants may not expose role="feed". Try several containers.
            feed_selectors = [
                '[role="feed"]',
                'div[data-pagelet="MainFeed"]',
                'div[aria-label="Timeline: Timeline"]',
                '[role="main"]',
                'main'
            ]
            post_selectors = [
                'div[role="article"][aria-posinset]',
                'div[role="article"]',
                '[data-ad-preview="message"]',
                '[data-ad-comet-preview="message"]'
            ]

            feed = None
            for selector in feed_selectors:
                try:
                    feed = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if feed is None:
                logger.warning(f"No feed container found for {page_name}; falling back to document-wide search")

            # Find posts inside feed when possible, then fall back to document-wide search.
            post_elements = []
            for selector in post_selectors:
                elements = []
                if feed is not None:
                    elements = feed.find_elements(By.CSS_SELECTOR, selector)
                if not elements:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    post_elements = elements
                    break
            
            for post in post_elements:
                try:
                    post_data = self._extract_post_data(post)
                    if post_data and (post_data.get('content') or post_data.get('comment_count', 0) > 0):
                        posts.append(post_data)
                except Exception as e:
                    logger.error(f"Error extracting post data: {str(e)}")
                    continue
                    
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts from {page_name}: {str(e)}")
            return []
            
    def extract_posts_with_bs(self, page_name: str) -> List[Dict[str, Any]]:
        """
        Extract posts using BeautifulSoup for better parsing
        
        Args:
            page_name: Name of the Facebook page to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        try:
            # Navigate to the page
            url = f"https://www.facebook.com/{page_name}"
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for content to load
            time.sleep(random.uniform(3, 5))
            
            # Initial scroll to load some content
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            
            posts = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll and collect posts
            scroll_attempts = 0
            max_attempts = 5
            
            while scroll_attempts < max_attempts:
                # Find all post elements
                post_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    '[role="article"]'
                )
                
                for post in post_elements:
                    try:
                        post_data = self._extract_post_data(post)
                        if post_data and post_data not in posts:
                            posts.append(post_data)
                    except Exception as e:
                        logger.warning(f"Error extracting post data: {e}")
                        continue
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height
                
            return posts
            
        except Exception as e:
            logger.error(f"Error extracting posts from {page_name}: {e}")
            return []
            
    def _extract_post_data(self, post_element: WebElement) -> Optional[Dict[str, Any]]:
        """Extract data from a single post element"""
        try:
            # Get post text
            try:
                text_element = post_element.find_element(By.CSS_SELECTOR, '[data-ad-comet-preview="message"]')
                post_text = text_element.text
            except NoSuchElementException:
                post_text = ""
            
            # Get post date
            try:
                date_element = post_element.find_element(By.CSS_SELECTOR, 'a[role="link"] span')
                post_date = date_element.text
            except NoSuchElementException:
                post_date = ""
            
            # Get engagement metrics
            try:
                metrics = post_element.find_elements(By.CSS_SELECTOR, '[role="button"]')
                likes = comments = shares = "0"
                for metric in metrics:
                    text = metric.text.lower()
                    if "like" in text:
                        likes = text.split()[0]
                    elif "comment" in text:
                        comments = text.split()[0]
                    elif "share" in text:
                        shares = text.split()[0]
            except Exception:
                likes = comments = shares = "0"
            
            return {
                "text": post_text,
                "date": post_date,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error parsing post element: {e}")
            return None
            
    def _extract_post_data(self, post_element: WebElement) -> Optional[Dict[str, Any]]:
        """Extract data from a post element"""
        try:
            # Basic post data
            post_data = {
                'timestamp': None,
                'content': '',
                'likes': 0,
                'comment_count': 0,
                'shares': 0,
                'images': [],
                'comments': []
            }
            
            # Get post content with selector fallbacks across FB variants.
            content_selectors = [
                'div[data-ad-comet-preview="message"]',
                'div[data-ad-preview="message"]',
                'div[dir="auto"] span[dir="auto"]',
                'div[dir="auto"]'
            ]
            for selector in content_selectors:
                content_elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                for el in content_elements:
                    text = clean_text((el.text or '').strip())
                    if text:
                        post_data['content'] = text
                        break
                if post_data['content']:
                    break

            # Last-resort fallback to element text if targeted selectors fail.
            if not post_data['content']:
                fallback_text = clean_text((post_element.text or '').strip())
                if fallback_text:
                    post_data['content'] = fallback_text[:2000]
                
            # Get interaction counts
            interaction_bar = post_element.find_elements(
                By.CSS_SELECTOR,
                'div[role="button"] span'
            )
            
            for element in interaction_bar:
                text = element.text.lower()
                if 'comment' in text:
                    try:
                        post_data['comment_count'] = int(''.join(filter(str.isdigit, text)))
                    except ValueError:
                        pass
                elif 'like' in text or 'reaction' in text:
                    try:
                        post_data['likes'] = int(''.join(filter(str.isdigit, text)))
                    except ValueError:
                        pass
                elif 'share' in text:
                    try:
                        post_data['shares'] = int(''.join(filter(str.isdigit, text)))
                    except ValueError:
                        pass
                        
            # Only process posts with comments if they have comments
            if post_data['comment_count'] > 0:
                comments = self._get_comments(post_element)
                post_data['comments'] = comments
                
            return post_data
            
        except Exception as e:
            logger.error(f"Error extracting post data: {str(e)}")
            return None
            
    def _get_comments(self, post_element: WebElement) -> List[Dict[str, Any]]:
        """Get comments from a post"""
        comments = []
        try:
            # Click "View more comments" if present
            try:
                view_more = post_element.find_element(
                    By.CSS_SELECTOR,
                    'div[role="button"]'
                )
                if "View" in view_more.text and "comment" in view_more.text.lower():
                    view_more.click()
                    time.sleep(random.uniform(1, 2))
            except NoSuchElementException:
                pass
                
            # Find comment elements
            comment_elements = post_element.find_elements(
                By.CSS_SELECTOR,
                'div[aria-label^="Comment"]'
            )
            
            for comment in comment_elements[:self.max_comments]:
                try:
                    comment_data = {
                        'author': '',
                        'content': '',
                        'timestamp': None
                    }
                    
                    # Get comment author
                    author_element = comment.find_element(
                        By.CSS_SELECTOR,
                        'a[role="link"]'
                    )
                    comment_data['author'] = author_element.text.strip()
                    
                    # Get comment content
                    content_element = comment.find_element(
                        By.CSS_SELECTOR,
                        'div[dir="auto"]'
                    )
                    comment_data['content'] = clean_text(content_element.text.strip())
                    
                    comments.append(comment_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting comment data: {str(e)}")
                    continue
                    
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return []

    def navigate_to_profile(self, page_name: str) -> bool:
        """
        Navigate to a Facebook profile/page
        
        Args:
            page_name: Name or URL of the Facebook page
            
        Returns:
            bool: Whether navigation was successful
        """
        try:
            if not page_name.startswith('http'):
                page_url = f'https://www.facebook.com/{page_name}'
            else:
                page_url = page_name
                
            self.driver.get(page_url)
            time.sleep(random.uniform(3, 5))  # Random delay for human-like behavior
            
            # Wait for the main content to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
            except TimeoutException:
                logger.warning(f"Timeout waiting for main content on {page_name}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to {page_name}: {str(e)}")
            return False
            
    def close(self):
        """Close the scraper and clean up resources"""
        pass  # The driver is managed by BrowserManager

class CommentScraper:
    """Component responsible for scraping comments from posts"""
    def __init__(self, max_comments=100):
        self.max_comments = max_comments
        
    def get_comments_from_post(self, driver, post_url):
        """Extract comments from a post URL"""
        try:
            driver.get(post_url)
            time.sleep(2)
            
            # Expand comments
            self._expand_all_comments(driver)
            
            # Get comments sections
            comments = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Comment"]')
            return self._process_comments(comments)
            
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []