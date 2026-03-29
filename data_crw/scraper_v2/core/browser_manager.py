"""
Browser Manager v2.0 - Robust browser session management for Facebook scraping.

Combines the best features from beta and Scraper0.1:
- Session recovery and restart capability (beta)
- Cookie-based and credential-based login (beta)
- Page load verification (Scraper0.1)
- Human-like behavior simulation (beta)
- Anti-detection measures (both)
"""

import logging
import time
import random
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException,
    InvalidSessionIdException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages browser sessions with robust error handling and recovery.
    
    Features:
    - Automatic session recovery on crash
    - Multiple login strategies (cookies, credentials, manual)
    - Human-like behavior simulation
    - Anti-detection measures
    - Page load verification
    """
    
    def __init__(self, config=None):
        """
        Initialize browser manager.
        
        Args:
            config: Optional configuration object. Uses defaults if not provided.
        """
        from config import get_config, BrowserConfig
        
        self.config = config or get_config()
        self.browser_config = self.config.browser if hasattr(self.config, 'browser') else BrowserConfig()
        
        self.driver: Optional[webdriver.Firefox] = None
        self.wait: Optional[WebDriverWait] = None
        self.logged_in: bool = False
        
        # Session state
        self._session_active: bool = False
        self._restart_count: int = 0
        self._last_url: str = ""
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def start(self) -> webdriver.Firefox:
        """
        Initialize and configure the browser with anti-detection measures.
        
        Returns:
            WebDriver instance
            
        Raises:
            RuntimeError: If browser initialization fails
        """
        try:
            logger.info("Starting browser initialization...")
            options = FirefoxOptions()
            
            # Anti-detection preferences
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("privacy.trackingprotection.enabled", False)
            
            # Performance settings
            if self.browser_config.disable_images:
                options.set_preference("permissions.default.image", 2)
            
            options.set_preference("browser.cache.disk.enable", True)
            options.set_preference("browser.cache.memory.enable", True)
            options.set_preference("network.http.pipelining", True)
            options.set_preference("javascript.enabled", True)
            
            # Additional arguments
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            # Headless mode
            if self.browser_config.headless:
                logger.info("Configuring headless mode")
                options.add_argument("--headless")
                options.add_argument(f"--window-size={self.browser_config.window_width},{self.browser_config.window_height}")
            
            # Get Firefox driver
            if WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("Using webdriver-manager for geckodriver")
                service = FirefoxService(GeckoDriverManager().install())
            else:
                logger.info("Using local geckodriver")
                service = FirefoxService("geckodriver")
            
            # Initialize browser
            logger.info("Creating Firefox browser instance...")
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Configure window size
            if not self.browser_config.headless:
                self.driver.set_window_size(
                    self.browser_config.window_width,
                    self.browser_config.window_height
                )
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.browser_config.page_load_timeout)
            self.wait = WebDriverWait(self.driver, self.browser_config.element_wait_timeout)
            
            self._session_active = True
            self._restart_count = 0
            
            logger.info("Browser initialization successful")
            return self.driver
            
        except Exception as e:
            error_msg = f"Browser initialization failed: {e}"
            logger.error(error_msg)
            self._session_active = False
            self.close()
            raise RuntimeError(error_msg)
    
    def is_session_alive(self) -> bool:
        """Check if the browser session is still active."""
        if not self.driver:
            return False
        try:
            _ = self.driver.current_url
            return True
        except (WebDriverException, InvalidSessionIdException):
            self._session_active = False
            return False
    
    def restart_session(self) -> bool:
        """
        Restart the browser session after a crash.
        
        Returns:
            bool: Whether restart was successful
        """
        if self._restart_count >= self.browser_config.max_restart_attempts:
            logger.error(f"Max restart attempts ({self.browser_config.max_restart_attempts}) reached")
            return False
        
        self._restart_count += 1
        logger.info(f"Restarting browser session (attempt {self._restart_count})")
        
        self.close()
        time.sleep(2)
        
        try:
            self.start()
            self._session_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to restart session: {e}")
            return False
    
    def ensure_session(self) -> bool:
        """Ensure the browser session is alive, restart if needed."""
        if self.is_session_alive():
            return True
        return self.restart_session()
    
    def close(self):
        """Close the browser session and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.debug(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
                self._session_active = False
                self.logged_in = False
    
    # =========================================================================
    # Login Methods
    # =========================================================================
    
    def login(self) -> bool:
        """
        Attempt to log in using the best available method.
        
        Tries in order: cookies -> credentials -> manual
        
        Returns:
            bool: Whether login was successful
        """
        if not self.ensure_session():
            logger.error("Cannot establish browser session for login")
            return False
        
        # Step 1: Try cookie-based login (fastest)
        logger.info("Attempting cookie-based login...")
        if self._login_with_cookies():
            return True
        
        # Step 2: Try credential-based login
        logger.info("Attempting credential-based login...")
        if self._login_with_credentials():
            return True
        
        # Step 3: Fall back to manual login
        logger.info("Attempting manual login...")
        return self._manual_login()
    
    def _login_with_cookies(self) -> bool:
        """Attempt login using saved cookies."""
        try:
            cookies = self.config.auth.cookies if hasattr(self.config, 'auth') else {}
            
            if not cookies:
                logger.debug("No cookies available")
                return False
            
            # Navigate to Facebook first
            self.driver.get('https://www.facebook.com')
            time.sleep(2)
            
            # Clear existing cookies
            self.driver.delete_all_cookies()
            
            # Add saved cookies
            for name, value in cookies.items():
                try:
                    self.driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.facebook.com',
                        'path': '/'
                    })
                except Exception as e:
                    logger.debug(f"Failed to add cookie {name}: {e}")
            
            # Refresh to apply cookies
            self.driver.get('https://www.facebook.com')
            time.sleep(3)
            
            # Dismiss any dialogs
            self._dismiss_dialogs()
            
            if self._verify_login():
                logger.info("Cookie-based login successful!")
                self.logged_in = True
                return True
            
            logger.debug("Cookie-based login failed")
            return False
            
        except Exception as e:
            logger.debug(f"Cookie login error: {e}")
            return False
    
    def _login_with_credentials(self) -> bool:
        """Attempt login using email/password."""
        try:
            email = self.config.auth.email if hasattr(self.config, 'auth') else ""
            password = self.config.auth.password if hasattr(self.config, 'auth') else ""
            
            if not email or not password:
                logger.debug("No credentials available")
                return False
            
            self.driver.get('https://www.facebook.com')
            time.sleep(2)
            
            # Dismiss any cookie/consent dialogs
            self._dismiss_dialogs()
            time.sleep(1)
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            self._type_human_like(email_input, email)
            time.sleep(random.uniform(0.5, 1))
            
            # Enter password
            password_input = self.driver.find_element(By.ID, 'pass')
            self._type_human_like(password_input, password)
            time.sleep(random.uniform(0.5, 1))
            
            # Click login
            login_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                '[name="login"], [data-testid="royal_login_button"]'
            )
            login_button.click()
            
            time.sleep(5)
            
            if self._verify_login():
                logger.info("Credential-based login successful!")
                self.logged_in = True
                return True
            
            # Check for 2FA
            if 'checkpoint' in self.driver.current_url.lower():
                logger.warning("2FA or security check detected - manual intervention required")
            
            return False
            
        except Exception as e:
            logger.debug(f"Credential login error: {e}")
            return False
    
    def _manual_login(self) -> bool:
        """Wait for user to manually log in."""
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            
            # Dismiss any cookie/consent dialogs first
            self._dismiss_dialogs()
            
            if self._verify_login():
                logger.info("Already logged in")
                self.logged_in = True
                return True
            
            # Close any login modal that might be blocking
            self._close_login_modal()
            
            print("\n" + "="*60)
            print("MANUAL LOGIN REQUIRED")
            print("="*60)
            print("1. Log in to Facebook in the browser window")
            print("2. Complete any security checks if prompted")
            print("3. The scraper will auto-detect when you're logged in")
            print("="*60 + "\n")
            
            timeout = self.config.auth.login_timeout_seconds if hasattr(self.config, 'auth') else 300
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if not self.is_session_alive():
                    logger.warning("Browser session died during manual login")
                    return False
                
                try:
                    if self._verify_login():
                        print("\nLogin detected!")
                        logger.info("Manual login successful")
                        self.logged_in = True
                        return True
                except Exception:
                    pass
                
                # Progress update every 30 seconds
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 30 == 0:
                    remaining = int((timeout - elapsed) / 60)
                    print(f"Waiting for login... ({remaining} minutes remaining)")
                
                time.sleep(1)
            
            logger.error("Login timeout")
            return False
            
        except Exception as e:
            logger.error(f"Manual login error: {e}")
            return False
    
    def _verify_login(self) -> bool:
        """Check if currently logged in to Facebook."""
        try:
            if not self.is_session_alive():
                return False
            
            current_url = self.driver.current_url.lower()
            
            # If on login page, not logged in
            if "login" in current_url or "welcome" in current_url:
                return False
            
            # Check for logged-in indicators
            selectors = [
                '[aria-label="Home"]',
                '[aria-label="Facebook"]',
                '[role="navigation"]',
                '[role="main"]',
                'div[data-pagelet="Stories"]'
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            # Check if login button is visible (means not logged in)
            try:
                login_btn = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    '[data-testid="royal_login_button"]'
                )
                if login_btn.is_displayed():
                    return False
            except NoSuchElementException:
                # No login button = probably logged in
                if "facebook.com" in current_url:
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Login verification error: {e}")
            return False
    
    def _dismiss_dialogs(self):
        """Dismiss cookie consent and other dialogs."""
        dialog_buttons = [
            # Cookie consent buttons
            '[data-testid="cookie-policy-manage-dialog-accept-button"]',
            'button[title="Allow all cookies"]',
            'button[title="Accept All"]',
            '[aria-label="Allow all cookies"]',
            '[aria-label="Accept all"]',
            'button[data-cookiebanner="accept_button"]',
            # "Only allow essential cookies" alternative
            'button[title="Only allow essential cookies"]',
            # Generic close/accept
            'button[title="Close"]',
            '[aria-label="Close"]',
            # Decline optional cookies (GDPR)
            '[data-testid="cookie-policy-manage-dialog-decline-button"]',
        ]
        
        for selector in dialog_buttons:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        logger.debug(f"Dismissed dialog with: {selector}")
                        time.sleep(1)
                        return
            except Exception:
                continue
    
    def _close_login_modal(self):
        """Close the Facebook login modal/popup if present."""
        modal_close_selectors = [
            # Modal close buttons
            '[aria-label="Close"]',
            'div[role="dialog"] [aria-label="Close"]',
            'div[role="dialog"] button[type="button"]',
            # Specific login modal close
            'img[src*="close"]',
            'i[data-visualcompletion="css-img"]',
            # X button variations
            'div[aria-label="Close"] > div',
            'div[role="button"][aria-label="Close"]',
        ]
        
        for selector in modal_close_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    try:
                        if el.is_displayed():
                            # Check if it's inside a dialog
                            parent = el.find_element(By.XPATH, './ancestor::div[@role="dialog"]')
                            if parent:
                                el.click()
                                logger.debug(f"Closed login modal with: {selector}")
                                time.sleep(1)
                                return True
                    except Exception:
                        continue
            except Exception:
                continue
        
        # Try pressing Escape key as fallback
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except Exception:
            pass
        
        return False
    
    def _handle_login_page(self):
        """Handle the login page - dismiss modals and prepare for login."""
        # First dismiss any cookie dialogs
        self._dismiss_dialogs()
        time.sleep(1)
        
        # Check if there's a blocking modal
        try:
            modal = self.driver.find_element(By.CSS_SELECTOR, 'div[role="dialog"]')
            if modal.is_displayed():
                logger.debug("Login modal detected, attempting to close...")
                self._close_login_modal()
        except NoSuchElementException:
            pass
    
    # =========================================================================
    # Navigation
    # =========================================================================
    
    def navigate_to(self, url: str, verify: bool = True) -> bool:
        """
        Navigate to a URL with retry logic.
        
        Args:
            url: The URL to navigate to
            verify: Whether to verify page load
            
        Returns:
            bool: Whether navigation was successful
        """
        max_retries = self.config.scraping.max_page_retries if hasattr(self.config, 'scraping') else 3
        
        for attempt in range(max_retries):
            if not self.ensure_session():
                logger.error("Browser session not available")
                continue
            
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Clear storage on retry
                if attempt > 0:
                    try:
                        self.driver.delete_all_cookies()
                        self.driver.execute_script("window.localStorage.clear();")
                        self.driver.execute_script("window.sessionStorage.clear();")
                    except Exception:
                        pass
                
                self.driver.get(url)
                self._last_url = url
                
                # Dismiss any dialogs/modals that might appear
                time.sleep(2)
                self._dismiss_dialogs()
                self._close_login_modal()
                
                if verify and not self._verify_page_load():
                    logger.warning("Page load verification failed")
                    time.sleep(5)
                    continue
                
                # Check for error pages
                if self._is_error_page():
                    logger.warning("Detected error page")
                    time.sleep(5)
                    continue
                
                logger.info("Page loaded successfully")
                return True
                
            except TimeoutException:
                logger.warning(f"Page load timeout for {url}")
            except Exception as e:
                logger.error(f"Navigation error: {e}")
            
            time.sleep(5)
        
        logger.error(f"Failed to navigate to {url} after {max_retries} attempts")
        return False
    
    def _verify_page_load(self) -> bool:
        """Verify that page has fully loaded."""
        try:
            self.wait.until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            start_url = self.driver.current_url
            time.sleep(2)
            
            # Check for redirect
            if self.driver.current_url != start_url:
                logger.debug(f"Redirect detected: {start_url} -> {self.driver.current_url}")
                self.wait.until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            
            # Check for login page
            if self._is_login_page():
                logger.warning("Redirected to login page")
                return False
            
            # Check for main content
            return self._find_main_content() is not None
            
        except Exception as e:
            logger.debug(f"Page load verification error: {e}")
            return False
    
    def _is_login_page(self) -> bool:
        """Check if current page is login/checkpoint page."""
        try:
            url = self.driver.current_url.lower()
            if 'login' in url or 'checkpoint' in url:
                return True
            
            # Check for login form
            email_fields = self.driver.find_elements(By.NAME, 'email')
            pass_fields = self.driver.find_elements(By.NAME, 'pass')
            return bool(email_fields and pass_fields)
            
        except Exception:
            return False
    
    def _is_error_page(self) -> bool:
        """Check if current page is an error page."""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            error_indicators = [
                "Sorry, something went wrong",
                "Page Not Found",
                "Content Not Found",
                "This content isn't available"
            ]
            return any(error in body_text for error in error_indicators)
        except Exception:
            return False
    
    def _find_main_content(self):
        """Find the main content area of the page."""
        selectors = [
            '[role="main"]',
            'div[role="main"]',
            'div[data-pagelet="MainFeed"]',
            '[role="feed"]',
            'main'
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    # =========================================================================
    # Human-like Behavior
    # =========================================================================
    
    def _type_human_like(self, element, text: str):
        """Type text with human-like delays."""
        min_delay = self.browser_config.min_typing_delay
        max_delay = self.browser_config.max_typing_delay
        
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
            
            # Occasional longer pause
            if random.random() < 0.05:
                time.sleep(random.uniform(0.3, 0.6))
    
    def scroll(self, steps: int = 5, pixels_per_step: int = 400) -> int:
        """
        Scroll the page with human-like behavior.
        
        Args:
            steps: Number of scroll steps
            pixels_per_step: Pixels to scroll per step
            
        Returns:
            Number of successful scroll steps
        """
        if not self.is_session_alive():
            return 0
        
        scroll_count = 0
        prev_height = 0
        no_change_count = 0
        
        for _ in range(steps):
            try:
                # Get current height
                current_height = self.driver.execute_script(
                    "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
                )
                
                if current_height == prev_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        break
                else:
                    no_change_count = 0
                
                prev_height = current_height
                
                # Scroll with variation
                actual_pixels = pixels_per_step + random.randint(-50, 50)
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: window.pageYOffset + {actual_pixels},
                        behavior: 'smooth'
                    }});
                """)
                
                scroll_count += 1
                
                # Wait for content to load
                pause = random.uniform(0.5, 1.5)
                time.sleep(pause)
                
                # Check for loading indicators
                self._wait_for_loading()
                
            except Exception as e:
                logger.debug(f"Scroll error: {e}")
                break
        
        logger.debug(f"Completed {scroll_count} scroll steps")
        return scroll_count
    
    def _wait_for_loading(self, timeout: float = 2.0):
        """Wait for any loading indicators to disappear."""
        try:
            loading_selectors = [
                '[role="progressbar"]',
                '[aria-busy="true"]',
                '.loading',
                '.spinner'
            ]
            
            for selector in loading_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if any(elem.is_displayed() for elem in elements):
                    time.sleep(timeout)
                    return
                    
        except Exception:
            pass
    
    def click_element(self, element, use_js: bool = False):
        """
        Click an element with human-like behavior.
        
        Args:
            element: WebElement to click
            use_js: Use JavaScript click instead of Selenium click
        """
        try:
            # Scroll element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(random.uniform(0.1, 0.3))
            
            min_delay = self.browser_config.min_click_delay
            max_delay = self.browser_config.max_click_delay
            
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                # Move to element with slight offset
                actions = ActionChains(self.driver)
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-3, 3)
                actions.move_to_element_with_offset(element, offset_x, offset_y)
                actions.pause(random.uniform(min_delay, max_delay))
                actions.click()
                actions.perform()
            
            time.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            logger.debug(f"Click error: {e}")
            raise
