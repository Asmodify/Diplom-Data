"""
Auto Scraper v2.0 - Main orchestration for automated Facebook scraping.

Coordinates browser, scraping, and database operations with:
- Robust session management
- Automatic recovery from errors
- Page rotation and scheduling
- Statistics tracking
"""

import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoScraper:
    """
    Main orchestrator for automated Facebook page scraping.
    
    Features:
    - Multi-page scraping with rotation
    - Automatic session recovery
    - Configurable intervals
    - Statistics and logging
    """
    
    def __init__(self, config=None):
        """
        Initialize the auto scraper.
        
        Args:
            config: Optional configuration object
        """
        from config import get_config
        
        self.config = config or get_config()
        
        # Components (lazy initialization)
        self._browser = None
        self._post_scraper = None
        self._db = None
        
        # State
        self.running = False
        self.pages: List[str] = []
        self.stats = {
            'total_posts': 0,
            'total_comments': 0,
            'pages_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    # =========================================================================
    # Component Initialization
    # =========================================================================
    
    @property
    def browser(self):
        """Lazy initialization of browser manager."""
        if self._browser is None:
            from core.browser_manager import BrowserManager
            self._browser = BrowserManager(self.config)
        return self._browser
    
    @property
    def post_scraper(self):
        """Lazy initialization of post scraper."""
        if self._post_scraper is None:
            from core.post_scraper import PostScraper
            self._post_scraper = PostScraper(self.browser, self.config)
        return self._post_scraper
    
    @property
    def db(self):
        """Lazy initialization of database manager."""
        if self._db is None:
            try:
                from db.database import DatabaseManager
                self._db = DatabaseManager(self.config)
                self._db.initialize()
            except ImportError:
                logger.warning("Database module not available, using in-memory storage")
                self._db = InMemoryStorage()
        return self._db
    
    def _initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Start browser
            logger.info("Starting browser...")
            self.browser.start()
            
            # Login
            logger.info("Logging in to Facebook...")
            if not self.browser.login():
                logger.error("Failed to log in to Facebook")
                return False
            
            logger.info("Initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    # =========================================================================
    # Page Management
    # =========================================================================
    
    def load_pages(self, pages: List[str] = None, file_path: str = None) -> int:
        """
        Load pages to scrape.
        
        Args:
            pages: List of page URLs/names
            file_path: Path to file containing page list
            
        Returns:
            Number of pages loaded
        """
        if pages:
            self.pages = self._normalize_pages(pages)
        elif file_path:
            self.pages = self._load_pages_from_file(file_path)
        else:
            # Default pages file
            default_path = Path(__file__).parent.parent / 'pages.txt'
            if default_path.exists():
                self.pages = self._load_pages_from_file(str(default_path))
        
        logger.info(f"Loaded {len(self.pages)} pages to scrape")
        return len(self.pages)
    
    def _normalize_pages(self, pages: List[str]) -> List[str]:
        """Normalize page identifiers to full URLs."""
        normalized = []
        for page in pages:
            page = page.strip()
            if not page or page.startswith('#'):
                continue
            if not page.startswith('http'):
                page = f"https://www.facebook.com/{page}"
            normalized.append(page)
        return normalized
    
    def _load_pages_from_file(self, file_path: str) -> List[str]:
        """Load page list from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return self._normalize_pages(f.readlines())
        except Exception as e:
            logger.error(f"Error loading pages from {file_path}: {e}")
            return []
    
    # =========================================================================
    # Main Scraping Logic
    # =========================================================================
    
    def run(
        self, 
        pages: List[str] = None,
        max_posts_per_page: int = None,
        continuous: bool = False
    ):
        """
        Run the scraper.
        
        Args:
            pages: List of pages to scrape (or use loaded pages)
            max_posts_per_page: Maximum posts per page
            continuous: Run continuously in loop
        """
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        if pages:
            self.load_pages(pages)
        
        if not self.pages:
            logger.error("No pages to scrape!")
            return
        
        # Initialize
        if not self._initialize():
            logger.error("Failed to initialize scraper")
            return
        
        try:
            if continuous:
                self._run_continuous(max_posts_per_page)
            else:
                self._run_single_pass(max_posts_per_page)
                
        except KeyboardInterrupt:
            logger.info("Scraper interrupted by user")
        except Exception as e:
            logger.error(f"Scraper error: {e}")
            self.stats['errors'] += 1
        finally:
            self._cleanup()
    
    def _run_single_pass(self, max_posts: int = None):
        """Run a single pass through all pages."""
        max_posts = max_posts or self.config.scraping.min_posts_per_page
        
        for i, page_url in enumerate(self.pages):
            if not self.running:
                break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping page {i+1}/{len(self.pages)}: {page_url}")
            logger.info(f"{'='*60}")
            
            try:
                posts = self._scrape_page_with_retry(page_url, max_posts)
                
                if posts:
                    # Save to database
                    saved = self._save_posts(posts)
                    self.stats['total_posts'] += saved
                    
                    # Update comment stats
                    for post in posts:
                        self.stats['total_comments'] += len(post.comment_list)
                    
                    self.stats['pages_scraped'] += 1
                    logger.info(f"Saved {saved} posts from {page_url}")
                else:
                    logger.warning(f"No posts scraped from {page_url}")
                
                # Delay between pages
                if i < len(self.pages) - 1:
                    delay = random.uniform(
                        self.config.scraping.page_delay_min,
                        self.config.scraping.page_delay_max
                    )
                    logger.info(f"Waiting {delay:.1f}s before next page...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error scraping {page_url}: {e}")
                self.stats['errors'] += 1
        
        self._print_summary()
    
    def _run_continuous(self, max_posts: int = None):
        """Run continuously, cycling through pages."""
        cycle = 0
        
        while self.running:
            cycle += 1
            logger.info(f"\n{'#'*60}")
            logger.info(f"Starting cycle {cycle}")
            logger.info(f"{'#'*60}")
            
            self._run_single_pass(max_posts)
            
            if self.running:
                interval = self.config.scraping.scrape_interval_seconds
                logger.info(f"Cycle complete. Waiting {interval}s before next cycle...")
                time.sleep(interval)
    
    def _scrape_page_with_retry(
        self, 
        page_url: str, 
        max_posts: int,
        max_retries: int = 3
    ) -> List:
        """Scrape a page with retry logic."""
        for attempt in range(max_retries):
            try:
                # Ensure browser session is alive
                if not self.browser.ensure_session():
                    logger.warning("Failed to ensure browser session")
                    continue
                
                # Check login status
                if not self.browser.logged_in:
                    logger.info("Re-logging in...")
                    if not self.browser.login():
                        continue
                
                # Scrape
                posts = self.post_scraper.scrape_page_posts(
                    page_url, 
                    max_posts=max_posts,
                    scrape_comments=True
                )
                
                if posts:
                    return posts
                    
            except Exception as e:
                logger.error(f"Scrape attempt {attempt+1} failed: {e}")
                
                # Try to recover session
                if attempt < max_retries - 1:
                    logger.info("Attempting to restart session...")
                    if self.browser.restart_session():
                        self.browser.login()
                    time.sleep(5)
        
        return []
    
    def _save_posts(self, posts: List) -> int:
        """Save posts to database."""
        saved = 0
        for post in posts:
            try:
                if self.db.save_post(post):
                    saved += 1
            except Exception as e:
                logger.error(f"Error saving post: {e}")
        return saved
    
    # =========================================================================
    # Control Methods
    # =========================================================================
    
    def stop(self):
        """Stop the scraper gracefully."""
        logger.info("Stopping scraper...")
        self.running = False
    
    def _cleanup(self):
        """Clean up resources."""
        self.stats['end_time'] = datetime.now()
        
        if self._browser:
            self._browser.close()
        
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
        
        logger.info("Cleanup complete")
    
    def _print_summary(self):
        """Print scraping summary."""
        duration = None
        if self.stats['start_time']:
            end = self.stats['end_time'] or datetime.now()
            duration = end - self.stats['start_time']
        
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Pages scraped:    {self.stats['pages_scraped']}/{len(self.pages)}")
        print(f"Posts collected:  {self.stats['total_posts']}")
        print(f"Comments:         {self.stats['total_comments']}")
        print(f"Errors:           {self.stats['errors']}")
        if duration:
            print(f"Duration:         {duration}")
        print("="*60 + "\n")
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            **self.stats,
            'scraper_stats': self.post_scraper.get_stats() if self._post_scraper else {}
        }


class InMemoryStorage:
    """Simple in-memory storage fallback when database is not available."""
    
    def __init__(self):
        self.posts = []
        self.post_ids = set()
    
    def initialize(self):
        pass
    
    def save_post(self, post) -> bool:
        if post.post_id in self.post_ids:
            return False
        self.posts.append(post.to_dict())
        self.post_ids.add(post.post_id)
        return True
    
    def get_posts(self, limit: int = 100) -> List[Dict]:
        return self.posts[:limit]
    
    def close(self):
        pass


# =========================================================================
# Module-level convenience function
# =========================================================================

def run_scraper(
    pages: List[str] = None,
    max_posts: int = 10,
    continuous: bool = False,
    config_path: str = None
):
    """
    Convenience function to run the scraper.
    
    Args:
        pages: List of pages to scrape
        max_posts: Maximum posts per page
        continuous: Run continuously
        config_path: Path to config file
    """
    scraper = AutoScraper()
    scraper.run(
        pages=pages,
        max_posts_per_page=max_posts,
        continuous=continuous
    )
    return scraper.get_stats()
