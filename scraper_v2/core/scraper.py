"""
Scraper v2.0
=============
Main scraper orchestrator combining features from:
- beta/automation/auto_scraper.py
- beta/scraper/browser_manager.py

Features:
- Automatic page scraping loop
- Retry logic with exponential backoff
- Session recovery
- Content saving
- Progress tracking
"""

import os
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .browser_manager import BrowserManager
from .post_scraper import PostScraper

logger = logging.getLogger(__name__)


class Scraper:
    """
    Main scraper class that orchestrates the scraping process.
    
    Features:
    - Scrape multiple pages in sequence
    - Automatic retry on failures
    - Session recovery
    - Progress tracking and resumption
    """
    
    def __init__(self, config=None):
        """
        Initialize Scraper.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        if config is None:
            from config import get_config
            config = get_config()
            
        self.config = config
        self.browser: Optional[BrowserManager] = None
        self.post_scraper: Optional[PostScraper] = None
        
        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'posts_scraped': 0,
            'comments_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
        }
        
        # State
        self._is_running = False
        self._current_page = None
        
    def start(self) -> bool:
        """
        Start browser and initialize components.
        
        Returns:
            bool: Whether startup was successful
        """
        try:
            # Create browser manager
            self.browser = BrowserManager(self.config)
            
            if not self.browser.start_browser():
                logger.error("Failed to start browser")
                return False
                
            # Create post scraper
            self.post_scraper = PostScraper(self.browser, self.config)
            
            # Record start time
            self.stats['start_time'] = datetime.now()
            self._is_running = True
            
            logger.info("Scraper started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scraper: {e}")
            return False
            
    def stop(self):
        """Stop scraper and cleanup resources."""
        try:
            self._is_running = False
            self.stats['end_time'] = datetime.now()
            
            if self.browser:
                self.browser.close()
                
            self._print_stats()
            logger.info("Scraper stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scraper: {e}")
            
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
        
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Log into Facebook.
        
        Args:
            email: Facebook email (uses config if None)
            password: Facebook password (uses config if None)
            
        Returns:
            bool: Whether login was successful
        """
        if not self.browser:
            logger.error("Browser not started")
            return False
            
        return self.browser.login(email, password)
        
    def scrape_page(self, page_url: str, max_posts: int = None) -> int:
        """
        Scrape posts from a single Facebook page.
        
        Args:
            page_url: URL of the Facebook page
            max_posts: Maximum posts to scrape (uses config if None)
            
        Returns:
            Number of posts scraped
        """
        if not self._is_running or not self.post_scraper:
            logger.error("Scraper not running")
            return 0
            
        max_posts = max_posts or self.config.scraping.max_posts_per_page
        self._current_page = page_url
        
        try:
            logger.info(f"Starting to scrape: {page_url}")
            
            posts_scraped = self.post_scraper.scrape_posts_on_page(
                page_url, max_posts
            )
            
            self.stats['posts_scraped'] += posts_scraped
            self.stats['pages_scraped'] += 1
            
            # Reset restart counter on success
            self.browser.reset_restart_counter()
            
            return posts_scraped
            
        except Exception as e:
            logger.error(f"Error scraping page {page_url}: {e}")
            self.stats['errors'] += 1
            
            # Try to recover
            if self.browser.ensure_session():
                logger.info("Session recovered, page may need retry")
                
            return 0
            
    def scrape_pages(self, page_urls: List[str], max_posts_per_page: int = None) -> Dict[str, int]:
        """
        Scrape multiple Facebook pages.
        
        Args:
            page_urls: List of page URLs
            max_posts_per_page: Maximum posts per page
            
        Returns:
            Dictionary mapping page URLs to posts scraped
        """
        results = {}
        
        for i, url in enumerate(page_urls):
            if not self._is_running:
                logger.info("Scraper stopped, abandoning remaining pages")
                break
                
            logger.info(f"Processing page {i+1}/{len(page_urls)}: {url}")
            
            # Scrape with retry
            posts = self._scrape_with_retry(url, max_posts_per_page)
            results[url] = posts
            
            # Delay between pages
            if i < len(page_urls) - 1:
                delay = random.uniform(
                    self.config.scraping.page_delay_min,
                    self.config.scraping.page_delay_max
                )
                logger.info(f"Waiting {delay:.1f}s before next page...")
                time.sleep(delay)
                
        return results
        
    def scrape_from_file(self, pages_file: str = None, max_posts_per_page: int = None) -> Dict[str, int]:
        """
        Scrape pages listed in a text file.
        
        Args:
            pages_file: Path to file with page URLs (one per line)
            max_posts_per_page: Maximum posts per page
            
        Returns:
            Dictionary mapping page URLs to posts scraped
        """
        pages_file = pages_file or self.config.pages_file
        
        try:
            urls = self._load_pages_file(pages_file)
            if not urls:
                logger.warning(f"No pages found in {pages_file}")
                return {}
                
            logger.info(f"Loaded {len(urls)} pages from {pages_file}")
            return self.scrape_pages(urls, max_posts_per_page)
            
        except Exception as e:
            logger.error(f"Error loading pages file {pages_file}: {e}")
            return {}
            
    def _scrape_with_retry(self, page_url: str, max_posts: int = None, max_retries: int = None) -> int:
        """
        Scrape a page with retry logic.
        
        Args:
            page_url: Page URL
            max_posts: Maximum posts
            max_retries: Maximum retry attempts
            
        Returns:
            Number of posts scraped
        """
        max_retries = max_retries or self.config.scraping.max_page_retries
        
        for attempt in range(max_retries):
            try:
                posts = self.scrape_page(page_url, max_posts)
                if posts > 0:
                    return posts
                    
                # Zero posts might be OK (empty page)
                if attempt == 0:
                    logger.info(f"No posts found on {page_url}")
                    return 0
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed for {page_url}: {e}")
                
                # Exponential backoff
                delay = self.config.scraping.retry_delay_seconds * (2 ** attempt)
                logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)
                
                # Try to recover session
                if not self.browser.ensure_session():
                    logger.error("Failed to recover session")
                    break
                    
        logger.error(f"Failed to scrape {page_url} after {max_retries} attempts")
        return 0
        
    def _load_pages_file(self, filepath: str) -> List[str]:
        """Load page URLs from file."""
        urls = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Ensure URL is complete
                    if not line.startswith('http'):
                        line = f"https://www.facebook.com/{line}"
                    urls.append(line)
        return urls
        
    def _print_stats(self):
        """Print scraping statistics."""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Pages scraped: {self.stats['pages_scraped']}")
        logger.info(f"Posts scraped: {self.stats['posts_scraped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        if duration:
            logger.info(f"Duration: {duration}")
        logger.info("=" * 60)


class AutoScraper(Scraper):
    """
    Automated scraper that runs continuously.
    
    Features:
    - Continuous scraping loop
    - Configurable intervals
    - Automatic recovery
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self._stop_requested = False
        
    def run_continuous(self, pages_file: str = None, interval_seconds: int = None):
        """
        Run continuous scraping loop.
        
        Args:
            pages_file: Path to pages file
            interval_seconds: Seconds between scraping cycles
        """
        interval = interval_seconds or self.config.scraping.scrape_interval_seconds
        
        try:
            if not self.start():
                logger.error("Failed to start scraper")
                return
                
            if not self.login():
                logger.error("Failed to log in")
                return
                
            cycle = 0
            while not self._stop_requested and self._is_running:
                cycle += 1
                logger.info(f"Starting scraping cycle {cycle}")
                
                try:
                    self.scrape_from_file(pages_file)
                except Exception as e:
                    logger.error(f"Error in scraping cycle {cycle}: {e}")
                    self.stats['errors'] += 1
                    
                if not self._stop_requested:
                    logger.info(f"Cycle {cycle} complete. Waiting {interval}s until next cycle...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()
            
    def request_stop(self):
        """Request graceful stop of continuous scraping."""
        logger.info("Stop requested")
        self._stop_requested = True
