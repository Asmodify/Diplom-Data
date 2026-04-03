"""
Facebook scraper module
"""
from .browser_manager import BrowserManager
from .post_scraper import PostScraper, CommentScraper

__all__ = ['BrowserManager', 'PostScraper', 'CommentScraper']
