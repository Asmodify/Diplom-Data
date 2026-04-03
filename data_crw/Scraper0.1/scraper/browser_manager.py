#!/usr/bin/env python
"""
Browser manager for Facebook scraping.
Handles Firefox browser setup, configuration, and login.
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, driver=None, wait_time=15):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, wait_time) if driver else None

    def find_main_content(self, max_retries=3, wait_time=2):
        selectors = [
            '[role="main"]',
            'div[role="main"]',
            '#contentArea',
            'div[data-pagelet="MainFeed"]',
            'div[aria-label="Timeline: Timeline"]',
            'div[aria-label="News Feed"]',
            'main',
        ]
        for attempt in range(max_retries):
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found main content with selector: {selector}")
                    return element
                except NoSuchElementException:
                    logger.debug(f"Selector not found: {selector}")
            logger.warning(f"Main content not found on attempt {attempt+1}. Retrying after {wait_time}s...")
            time.sleep(wait_time)
        logger.error(f"Main content not found after {max_retries} attempts. URL: {self.driver.current_url}, Title: {self.driver.title}")
        return None

    def is_login_page(self):
        try:
            if self.driver.find_elements(By.NAME, 'email') and self.driver.find_elements(By.NAME, 'pass'):
                logger.info("Detected Facebook login page.")
                return True
            if 'checkpoint' in self.driver.current_url or 'login' in self.driver.current_url:
                logger.info(f"Detected checkpoint or login in URL: {self.driver.current_url}")
                return True
        except Exception as e:
            logger.warning(f"Error checking login page: {e}")
        return False

    def restart_browser(self, driver_factory, max_retries=2):
        """
        Restart the browser session if it crashes or loses connection.
        driver_factory: a callable that returns a new webdriver instance.
        """
        for attempt in range(max_retries):
            try:
                if self.driver:
                    self.driver.quit()
                self.driver = driver_factory()
                self.wait = WebDriverWait(self.driver, 15)
                logger.info(f"Browser restarted (attempt {attempt+1})")
                return True
            except Exception as e:
                logger.error(f"Failed to restart browser (attempt {attempt+1}): {e}")
                time.sleep(2)
        logger.critical("Could not restart browser after multiple attempts.")
        return False

    def verify_page_load(self, timeout=30, auto_restart=False, driver_factory=None) -> bool:
        try:
            self.wait.until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            start_url = self.driver.current_url
            time.sleep(2)
            if self.driver.current_url != start_url:
                logger.info(f"Detected redirect: {start_url} -> {self.driver.current_url}")
                self.wait.until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
            if self.is_login_page():
                logger.warning(f"Login or checkpoint page detected at {self.driver.current_url}")
                return False
            main_content = self.find_main_content()
            if main_content is not None:
                logger.info("Main content found. Page loaded successfully.")
                return True
            else:
                logger.error(f"Main content not found after page load. URL: {self.driver.current_url}, Title: {self.driver.title}")
                return False
        except WebDriverException as e:
            logger.error(f"WebDriverException during page load: {e}")
            if auto_restart and driver_factory:
                logger.info("Attempting to auto-restart browser...")
                return self.restart_browser(driver_factory)
            return False
        except Exception as e:
            logger.warning(f"Exception during page load verification: {e}")
            logger.debug(f"Current URL: {getattr(self.driver, 'current_url', 'N/A')}, Title: {getattr(self.driver, 'title', 'N/A')}")
            return False
