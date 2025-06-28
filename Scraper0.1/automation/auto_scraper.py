"""
Automated Facebook scraper that coordinates browser management,
scraping, and content saving with human-like behavior.
"""
import logging
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from scraper.browser_manager import BrowserManager
from scraper.post_scraper import PostScraper
from content_manager.content_manager import ContentSaver

logger = logging.getLogger(__name__)

class AutoScraper:
    def __init__(self, driver, content_dir):
        self.driver = driver
        self.browser = BrowserManager(driver)
        self.scraper = PostScraper(driver)
        self.saver = ContentSaver(content_dir)
        self.content_dir = content_dir

    def restart_driver(self):
        # Close old driver and start a new one
        try:
            self.driver.quit()
        except Exception:
            pass
        options = Options()
        # Uncomment below to run headless
        # options.headless = True
        self.driver = webdriver.Firefox(options=options)
        self.browser = BrowserManager(self.driver)
        self.scraper = PostScraper(self.driver)
        self.saver = ContentSaver(self.content_dir)
        return self.driver

    def scrape_page(self, page_url):
        try:
            if not self.browser.verify_page_load():
                logger.error(f"Page did not load: {page_url}")
                return False
            posts = self.scraper.scrape_posts(page_url, min_posts=10)
            if posts:
                for post in posts:
                    self.saver.save_post(post, page_url)
                logger.info(f"Saved {len(posts)} posts from {page_url}")
                return True
            return False
        except WebDriverException as e:
            logger.error(f"WebDriverException: {e}. Restarting browser and retrying page: {page_url}")
            self.restart_driver()
            # Try scraping the page again after restart
            try:
                if not self.browser.verify_page_load():
                    logger.error(f"Page did not load after restart: {page_url}")
                    return False
                posts = self.scraper.scrape_posts(page_url, min_posts=10)
                if posts:
                    for post in posts:
                        self.saver.save_post(post, page_url)
                    logger.info(f"Saved {len(posts)} posts from {page_url} after restart")
                    return True
                return False
            except Exception as e2:
                logger.error(f"Failed again after restart: {e2}")
                return False
