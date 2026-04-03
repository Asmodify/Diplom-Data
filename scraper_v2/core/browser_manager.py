"""
Browser Manager v2.0
=====================
Comprehensive browser session management combining ALL features from:
- beta/scraper/browser_manager.py (EventFiringWebDriver, session recovery, 3-tier login)
- Scraper0.1/scraper/post_scraper.py (robust modal handling, multiple click strategies)

Features:
- EventFiringWebDriver with custom listener for debugging
- Session recovery: is_session_alive(), restart_session(), ensure_session()
- 3-tier login: cookies -> credentials -> manual input
- Human simulation: typing, scrolling, clicking with random delays
- Random viewport sizes for anti-detection
- Paywall hiding script
- Login modal dismissal
- Dialog close functionality
- Windows keyboard handling with msvcrt
"""

import os
import sys
import time
import random
import logging
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSessionIdException,
    SessionNotCreatedException
)
from selenium.webdriver.remote.webelement import WebElement

# EventFiringWebDriver for debugging
try:
    from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
    HAS_EVENT_LISTENER = True
except ImportError:
    HAS_EVENT_LISTENER = False
    EventFiringWebDriver = None
    AbstractEventListener = object

# WebDriver Manager for automatic driver installation
try:
    from webdriver_manager.firefox import GeckoDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

logger = logging.getLogger(__name__)


class ScraperEventListener(AbstractEventListener):
    """
    Event listener for debugging WebDriver actions.
    Logs all navigation, element interactions, and JavaScript executions.
    """
    
    def __init__(self):
        self.last_action_time = time.time()
        self.action_count = 0
        
    def before_navigate_to(self, url: str, driver) -> None:
        logger.debug(f"→ Navigating to: {url}")
        
    def after_navigate_to(self, url: str, driver) -> None:
        logger.debug(f"✓ Navigated to: {driver.current_url}")
        self.last_action_time = time.time()
        
    def before_find(self, by: str, value: str, driver) -> None:
        logger.debug(f"→ Finding element: {by}='{value}'")
        
    def after_find(self, by: str, value: str, driver) -> None:
        self.action_count += 1
        
    def before_click(self, element: WebElement, driver) -> None:
        try:
            logger.debug(f"→ Clicking element: tag={element.tag_name}, text='{element.text[:30]}...'")
        except Exception:
            logger.debug("→ Clicking element")
            
    def after_click(self, element: WebElement, driver) -> None:
        logger.debug("✓ Click completed")
        self.last_action_time = time.time()
        
    def before_execute_script(self, script: str, driver) -> None:
        if len(script) > 100:
            logger.debug(f"→ Executing script: {script[:100]}...")
        else:
            logger.debug(f"→ Executing script: {script}")
            
    def after_execute_script(self, script: str, driver) -> None:
        self.last_action_time = time.time()
        
    def on_exception(self, exception, driver) -> None:
        logger.error(f"✗ WebDriver exception: {type(exception).__name__}: {exception}")


class BrowserManager:
    """
    Advanced browser session management with:
    - Session recovery and automatic restart
    - Human-like behavior simulation
    - Multi-strategy login (cookies, credentials, manual)
    - Dialog/modal dismissal
    - Anti-detection features
    """
    
    def __init__(self, config=None):
        """
        Initialize BrowserManager.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        if config is None:
            from config import get_config
            config = get_config()
            
        self.config = config
        self.driver: Optional[webdriver.Firefox] = None
        self.wait: Optional[WebDriverWait] = None
        self.event_listener: Optional[ScraperEventListener] = None
        
        # Session state
        self._is_logged_in = False
        self._session_start_time: Optional[datetime] = None
        self._restart_count = 0
        self._last_activity_time = time.time()
        
        # Directories
        self.data_dir = Path(config.database.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_firefox_options(self) -> FirefoxOptions:
        """Configure Firefox with anti-detection and performance options."""
        options = FirefoxOptions()
        
        browser_config = self.config.browser
        
        # Headless mode
        if browser_config.headless:
            options.add_argument('--headless')
            
        # Window size (use random if enabled)
        if browser_config.random_viewport:
            width, height = random.choice(browser_config.viewports)
        else:
            width, height = browser_config.window_width, browser_config.window_height
        options.add_argument(f'--width={width}')
        options.add_argument(f'--height={height}')
        
        # Performance options
        if browser_config.disable_images:
            options.set_preference('permissions.default.image', 2)
            
        # Anti-detection preferences
        options.set_preference('dom.webdriver.enabled', False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference('privacy.trackingprotection.enabled', True)
        options.set_preference('network.http.sendRefererHeader', 2)
        options.set_preference('general.useragent.override', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0')
        
        # Disable notifications
        options.set_preference('dom.push.enabled', False)
        options.set_preference('dom.webnotifications.enabled', False)
        
        # Page load strategy
        options.page_load_strategy = 'normal'
        
        return options
        
    def start_browser(self) -> bool:
        """
        Initialize the browser with all configured options.
        
        Returns:
            bool: Whether browser started successfully
        """
        try:
            logger.info("Starting Firefox browser...")
            
            options = self._get_firefox_options()
            
            # Get service (with webdriver_manager if available)
            if HAS_WEBDRIVER_MANAGER:
                service = FirefoxService(GeckoDriverManager().install())
            else:
                service = FirefoxService()
                
            # Create base driver
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Wrap with EventFiringWebDriver if available and enabled
            if HAS_EVENT_LISTENER and self.config.browser.enable_event_listener:
                self.event_listener = ScraperEventListener()
                self.driver = EventFiringWebDriver(self.driver, self.event_listener)
                logger.debug("EventFiringWebDriver enabled for debugging")
                
            # Configure timeouts
            self.driver.set_page_load_timeout(self.config.browser.page_load_timeout)
            self.driver.implicitly_wait(5)
            
            # Create wait object
            self.wait = WebDriverWait(self.driver, self.config.browser.element_wait_timeout)
            
            # Session tracking
            self._session_start_time = datetime.now()
            self._last_activity_time = time.time()
            
            logger.info("Browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
            
    def close(self):
        """Close browser and cleanup resources."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        finally:
            self.driver = None
            self.wait = None
            self._is_logged_in = False
            
    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
        
    # =========================================================================
    # SESSION MANAGEMENT (from beta/browser_manager.py)
    # =========================================================================
    
    def is_session_alive(self) -> bool:
        """
        Check if the WebDriver session is still active.
        
        Returns:
            bool: True if session is alive, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            # Try to get current URL - this will fail if session is dead
            _ = self.driver.current_url
            _ = self.driver.title
            return True
        except (InvalidSessionIdException, WebDriverException, SessionNotCreatedException):
            return False
        except Exception as e:
            logger.warning(f"Session check error: {e}")
            return False
            
    def restart_session(self) -> bool:
        """
        Restart the browser session.
        
        Returns:
            bool: Whether restart was successful
        """
        self._restart_count += 1
        
        if self._restart_count > self.config.browser.max_restart_attempts:
            logger.error(f"Max restart attempts ({self.config.browser.max_restart_attempts}) exceeded")
            return False
            
        logger.info(f"Restarting browser session (attempt {self._restart_count})")
        
        # Close existing
        self.close()
        
        # Wait before restart
        time.sleep(random.uniform(2, 5))
        
        # Start new browser
        return self.start_browser()
        
    def ensure_session(self) -> bool:
        """
        Ensure browser session is alive, restarting if necessary.
        
        Returns:
            bool: Whether session is now active
        """
        if self.is_session_alive():
            return True
            
        logger.warning("Session not alive, attempting restart...")
        return self.restart_session()
        
    def reset_restart_counter(self):
        """Reset the restart counter (call after successful operations)."""
        self._restart_count = 0
        
    # =========================================================================
    # HUMAN SIMULATION (from beta/browser_manager.py)
    # =========================================================================
    
    def simulate_human_typing(self, element: WebElement, text: str, clear_first: bool = True):
        """
        Type text into an element with human-like random delays.
        
        Args:
            element: The input element to type into
            text: Text to type
            clear_first: Whether to clear the field first
        """
        try:
            if clear_first:
                element.clear()
                time.sleep(random.uniform(0.1, 0.3))
                
            for char in text:
                element.send_keys(char)
                # Variable delay - longer for some characters
                if char in ' \n':
                    time.sleep(random.uniform(0.1, 0.25))
                else:
                    time.sleep(random.uniform(
                        self.config.browser.min_typing_delay,
                        self.config.browser.max_typing_delay
                    ))
                    
        except Exception as e:
            logger.error(f"Error during human typing simulation: {e}")
            raise
            
    def simulate_human_scroll(self, scroll_amount: int = None, container: WebElement = None):
        """
        Perform human-like scrolling with variable speed.
        
        Args:
            scroll_amount: Pixels to scroll (random if None)
            container: Container element to scroll (page if None)
        """
        try:
            if scroll_amount is None:
                scroll_amount = random.randint(200, 600)
                
            # Smooth scrolling in steps
            steps = random.randint(3, 7)
            step_amount = scroll_amount // steps
            
            for _ in range(steps):
                if container:
                    self.driver.execute_script(
                        "arguments[0].scrollBy(0, arguments[1]);",
                        container, step_amount
                    )
                else:
                    self.driver.execute_script(
                        f"window.scrollBy(0, {step_amount});"
                    )
                time.sleep(random.uniform(0.05, 0.15))
                
            # Brief pause after scrolling
            time.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            logger.error(f"Error during scroll simulation: {e}")
            raise
            
    def simulate_human_click(self, element: WebElement, use_actions: bool = True):
        """
        Click an element with human-like behavior (move to element first).
        
        Args:
            element: Element to click
            use_actions: Whether to use ActionChains for realistic movement
        """
        try:
            # Scroll element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(random.uniform(0.2, 0.4))
            
            if use_actions:
                actions = ActionChains(self.driver)
                # Move to element with offset for realism
                actions.move_to_element(element)
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)
                actions.move_by_offset(offset_x, offset_y)
                actions.pause(random.uniform(0.1, 0.2))
                actions.click()
                actions.perform()
            else:
                element.click()
                
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            logger.error(f"Error during click simulation: {e}")
            raise
            
    # =========================================================================
    # LOGIN MANAGEMENT (3-tier from beta + dialog handling from Scraper0.1)
    # =========================================================================
    
    def login(self, email: str = None, password: str = None, use_cookies: bool = True) -> bool:
        """
        Log into Facebook using 3-tier approach:
        1. Try cookies first
        2. Fall back to email/password
        3. Wait for manual login if needed
        
        Args:
            email: Facebook email (uses config if None)
            password: Facebook password (uses config if None)
            use_cookies: Whether to try cookie-based login first
            
        Returns:
            bool: Whether login was successful
        """
        email = email or self.config.auth.email
        password = password or self.config.auth.password
        
        # Tier 1: Cookie-based login
        if use_cookies and self._try_cookie_login():
            self._is_logged_in = True
            return True
            
        # Tier 2: Credentials login
        if email and password and self._try_credentials_login(email, password):
            self._is_logged_in = True
            return True
            
        # Tier 3: Manual login
        if self._wait_for_manual_login():
            self._is_logged_in = True
            return True
            
        return False
        
    def _try_cookie_login(self) -> bool:
        """
        Attempt login using saved cookies.
        
        Returns:
            bool: Whether cookie login succeeded
        """
        try:
            cookies = self.config.auth.cookies
            if not cookies:
                logger.debug("No cookies configured, skipping cookie login")
                return False
                
            logger.info("Attempting cookie-based login...")
            
            # Navigate to Facebook first (required for cookies)
            self.driver.get('https://www.facebook.com')
            time.sleep(random.uniform(2, 4))
            
            # Dismiss any login modals
            self._dismiss_dialogs()
            
            # Add cookies
            for name, value in cookies.items():
                try:
                    self.driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.facebook.com',
                        'path': '/'
                    })
                except Exception as e:
                    logger.warning(f"Failed to add cookie {name}: {e}")
                    
            # Refresh to apply cookies
            self.driver.get('https://www.facebook.com')
            time.sleep(random.uniform(3, 5))
            
            # Dismiss any dialogs again
            self._dismiss_dialogs()
            
            if self._is_logged_in_check():
                logger.info("Cookie login successful")
                return True
                
        except Exception as e:
            logger.warning(f"Cookie login failed: {e}")
            
        return False
        
    def _try_credentials_login(self, email: str, password: str) -> bool:
        """
        Attempt login using email/password.
        
        Returns:
            bool: Whether credentials login succeeded
        """
        try:
            logger.info("Attempting credentials login...")
            
            self.driver.get('https://www.facebook.com')
            time.sleep(random.uniform(2, 4))
            
            # Dismiss any dialogs
            self._dismiss_dialogs()
            
            # Find and fill email
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'email'))
                )
            except TimeoutException:
                # Try alternative selector
                email_input = self.driver.find_element(By.NAME, 'email')
                
            self.simulate_human_typing(email_input, email)
            time.sleep(random.uniform(0.5, 1))
            
            # Find and fill password
            try:
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'pass'))
                )
            except TimeoutException:
                password_input = self.driver.find_element(By.NAME, 'pass')
                
            self.simulate_human_typing(password_input, password)
            time.sleep(random.uniform(0.5, 1))
            
            # Click login button
            login_selectors = [
                (By.CSS_SELECTOR, '[name="login"]'),
                (By.CSS_SELECTOR, '[data-testid="royal_login_button"]'),
                (By.XPATH, "//button[contains(text(), 'Log In') or contains(text(), 'Log in')]"),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
            ]
            
            for by, selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(by, selector)
                    login_btn.click()
                    break
                except NoSuchElementException:
                    continue
                    
            # Wait for login to complete
            time.sleep(random.uniform(3, 6))
            
            # Dismiss any post-login dialogs
            self._dismiss_dialogs()
            
            if self._is_logged_in_check():
                logger.info("Credentials login successful")
                return True
                
        except Exception as e:
            logger.warning(f"Credentials login failed: {e}")
            
        return False
        
    def _wait_for_manual_login(self) -> bool:
        """
        Wait for user to manually log in.
        Uses msvcrt for Windows keyboard input.
        
        Returns:
            bool: Whether manual login succeeded
        """
        try:
            logger.info("=" * 60)
            logger.info("MANUAL LOGIN REQUIRED")
            logger.info("Please log into Facebook manually in the browser window.")
            logger.info("Press ENTER when done, or wait 5 minutes for timeout...")
            logger.info("=" * 60)
            
            print("\n" + "=" * 60)
            print("MANUAL LOGIN REQUIRED")
            print("Please log into Facebook manually in the browser window.")
            print("Press ENTER when done, or 'q' to quit...")
            print("=" * 60 + "\n")
            
            timeout = self.config.auth.login_timeout_seconds
            start_time = time.time()
            
            # Windows keyboard handling
            if sys.platform == 'win32':
                try:
                    import msvcrt
                    while time.time() - start_time < timeout:
                        if msvcrt.kbhit():
                            key = msvcrt.getch()
                            if key in (b'\r', b'\n'):  # Enter
                                break
                            if key.lower() == b'q':
                                return False
                                
                        # Check if already logged in
                        if self._is_logged_in_check():
                            logger.info("Detected successful login")
                            return True
                            
                        time.sleep(1)
                except ImportError:
                    # Fallback: simple wait with input
                    time.sleep(timeout)
            else:
                # Non-Windows: simple wait with periodic check
                while time.time() - start_time < timeout:
                    if self._is_logged_in_check():
                        logger.info("Detected successful login")
                        return True
                    time.sleep(2)
                    
            # Final check
            return self._is_logged_in_check()
            
        except Exception as e:
            logger.error(f"Manual login wait failed: {e}")
            return False
            
    def _is_logged_in_check(self) -> bool:
        """
        Check if currently logged into Facebook.
        
        Returns:
            bool: True if logged in
        """
        try:
            time.sleep(random.uniform(1, 2))
            
            # Check for logged-in indicators
            logged_in_selectors = [
                '[role="navigation"]',
                '[aria-label="Account"]',
                '[aria-label="Your profile"]',
                '[data-pagelet="Stories"]',
                'div[data-pagelet="ProfileTilesFeed"]',
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
                    
            # Check for login form (indicates NOT logged in)
            try:
                self.driver.find_element(By.ID, 'email')
                self.driver.find_element(By.ID, 'pass')
                return False  # Login form present = not logged in
            except NoSuchElementException:
                pass
                
            # Check URL
            current_url = self.driver.current_url
            if 'login' in current_url or 'checkpoint' in current_url:
                return False
                
            return True  # Default to assuming logged in if no contra-indicators
            
        except Exception as e:
            logger.warning(f"Login check error: {e}")
            return False
            
    # =========================================================================
    # DIALOG/MODAL HANDLING (from both projects)
    # =========================================================================
    
    def _dismiss_dialogs(self):
        """Dismiss any Facebook dialogs/modals that appear."""
        self._close_login_modal()
        self._handle_cookie_consent()
        self._hide_paywall()
        
    def _close_login_modal(self):
        """
        Close Facebook login modal/overlay if present.
        Uses multiple strategies from both projects.
        """
        close_selectors = [
            # Close buttons
            (By.CSS_SELECTOR, '[aria-label="Close"]'),
            (By.CSS_SELECTOR, 'div[aria-label="Close"]'),
            (By.XPATH, "//div[@aria-label='Close']"),
            (By.XPATH, "//button[@aria-label='Close']"),
            
            # Not now buttons
            (By.XPATH, "//span[text()='Not Now']/ancestor::div[@role='button']"),
            (By.XPATH, "//*[text()='Not now' or text()='Not Now']"),
            (By.CSS_SELECTOR, '[data-testid="cookie-policy-manage-dialog-decline-button"]'),
            
            # Cancel/dismiss
            (By.XPATH, "//span[text()='Cancel']/ancestor::div[@role='button']"),
            (By.XPATH, "//div[@role='button' and contains(., 'Continue as Guest')]"),
            (By.XPATH, "//a[contains(@href, 'close_dialog')]"),
        ]
        
        for by, selector in close_selectors:
            try:
                elements = self.driver.find_elements(by, selector)
                for element in elements[:3]:  # Try first 3 matches
                    if element.is_displayed():
                        try:
                            element.click()
                            time.sleep(0.3)
                            logger.debug(f"Closed dialog using: {selector}")
                        except (ElementClickInterceptedException, ElementNotInteractableException):
                            # Try JavaScript click
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(0.3)
                            logger.debug(f"Closed dialog with JS click: {selector}")
            except Exception:
                continue
                
        # Also try pressing Escape
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.2)
        except Exception:
            pass
            
    def _handle_cookie_consent(self):
        """Handle cookie consent dialogs."""
        cookie_selectors = [
            (By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"),
            (By.XPATH, "//span[contains(text(), 'Accept') or contains(text(), 'Allow')]/ancestor::button"),
            (By.CSS_SELECTOR, '[data-testid="cookie-policy-manage-dialog-accept-button"]'),
            (By.XPATH, "//button[contains(text(), 'Only allow essential cookies')]"),
        ]
        
        for by, selector in cookie_selectors:
            try:
                elements = self.driver.find_elements(by, selector)
                for element in elements[:2]:
                    if element.is_displayed():
                        element.click()
                        time.sleep(0.3)
                        logger.debug("Handled cookie consent")
                        return
            except Exception:
                continue
                
    def _hide_paywall(self):
        """Inject CSS to hide paywall and login prompts (from beta)."""
        try:
            hide_script = """
                (function() {
                    var style = document.createElement('style');
                    style.textContent = `
                        [data-testid="login_popup_cta_form"],
                        [data-testid="cookie-policy-banner"],
                        div[role="dialog"][aria-modal="true"],
                        div[class*="uiLayer"]:has([data-testid="login"]),
                        div[class*="LoginOverlay"],
                        div[class*="paywall"] {
                            display: none !important;
                            visibility: hidden !important;
                            opacity: 0 !important;
                        }
                        body {
                            overflow: auto !important;
                        }
                    `;
                    document.head.appendChild(style);
                })();
            """
            self.driver.execute_script(hide_script)
            logger.debug("Injected paywall hiding CSS")
        except Exception as e:
            logger.debug(f"Failed to inject paywall CSS: {e}")
            
    # =========================================================================
    # NAVIGATION (from beta)
    # =========================================================================
    
    def navigate_to(self, url: str, max_retries: int = 3) -> bool:
        """
        Navigate to a URL with retry logic and verification.
        
        Args:
            url: The URL to navigate to
            max_retries: Maximum retry attempts
            
        Returns:
            bool: Whether navigation was successful
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Ensure session is alive
                if not self.ensure_session():
                    continue
                    
                # Clear browser data on retry
                if attempt > 0:
                    try:
                        self.driver.delete_all_cookies()
                        self.driver.execute_script("window.localStorage.clear();")
                        self.driver.execute_script("window.sessionStorage.clear();")
                    except Exception:
                        pass
                        
                # Navigate
                self.driver.get(url)
                
                # Verify page load
                if self._verify_page_load():
                    # Dismiss any dialogs
                    self._dismiss_dialogs()
                    
                    # Check for error pages
                    if not self._check_for_errors():
                        logger.info("Navigation successful")
                        self._last_activity_time = time.time()
                        return True
                        
                logger.warning(f"Navigation verification failed, retrying...")
                time.sleep(random.uniform(3, 6))
                
            except TimeoutException:
                logger.warning(f"Navigation timeout on attempt {attempt + 1}")
            except WebDriverException as e:
                logger.error(f"Navigation error: {e}")
                self.restart_session()
                
        logger.error(f"Failed to navigate to {url} after {max_retries} attempts")
        return False
        
    def _verify_page_load(self, timeout: int = 30) -> bool:
        """
        Verify page has fully loaded.
        
        Returns:
            bool: Whether page loaded successfully
        """
        try:
            # Wait for document ready
            self.wait.until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Brief wait for any scripts
            time.sleep(random.uniform(1, 2))
            
            # Check for login page
            if self._is_login_page():
                logger.warning("Redirected to login page")
                return False
                
            # Try to find main content
            main_selectors = [
                '[role="main"]',
                'div[role="main"]',
                '#contentArea',
                'div[data-pagelet="MainFeed"]',
                'main',
            ]
            
            for selector in main_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
                    
            # If no main content found but also no login page, might be OK
            return True
            
        except Exception as e:
            logger.warning(f"Page load verification error: {e}")
            return False
            
    def _is_login_page(self) -> bool:
        """Check if current page is a login/checkpoint page."""
        try:
            # Check URL
            current_url = self.driver.current_url.lower()
            if any(x in current_url for x in ['login', 'checkpoint', 'recover']):
                return True
                
            # Check for login form
            if (self.driver.find_elements(By.NAME, 'email') and 
                self.driver.find_elements(By.NAME, 'pass')):
                return True
                
        except Exception as e:
            logger.warning(f"Error checking login page: {e}")
            
        return False
        
    def _check_for_errors(self) -> bool:
        """
        Check for Facebook error pages.
        
        Returns:
            bool: True if error page detected
        """
        try:
            error_texts = [
                "Sorry, something went wrong",
                "Page Not Found",
                "Content Not Found",
                "This content isn't available right now",
                "This page isn't available",
                "The link you followed may be broken",
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            for error_text in error_texts:
                if error_text in page_text:
                    logger.warning(f"Detected error page: {error_text}")
                    return True
                    
        except Exception:
            pass
            
        return False
        
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def take_screenshot(self, filename: str = None) -> Optional[str]:
        """
        Take a screenshot and save it.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to saved screenshot or None
        """
        try:
            screenshots_dir = self.data_dir / 'screenshots'
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            if filename is None:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
            filepath = screenshots_dir / filename
            self.driver.save_screenshot(str(filepath))
            logger.debug(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
            
    def save_page_source(self, filename: str = None) -> Optional[str]:
        """
        Save current page HTML for debugging.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to saved file or None
        """
        try:
            debug_dir = self.data_dir / 'debug'
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            if filename is None:
                filename = f"page_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                
            filepath = debug_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
                
            logger.debug(f"Page source saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save page source: {e}")
            return None
            
    def wait_for_element(self, by: By, selector: str, timeout: int = None) -> Optional[WebElement]:
        """
        Wait for an element to be present.
        
        Args:
            by: Locator type
            selector: Element selector
            timeout: Wait timeout (uses config if None)
            
        Returns:
            WebElement or None
        """
        try:
            timeout = timeout or self.config.browser.element_wait_timeout
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            return None
            
    def click_element_safe(self, element: WebElement, use_js: bool = False) -> bool:
        """
        Safely click an element with multiple strategies (from Scraper0.1).
        
        Strategies:
        1. Direct element.click()
        2. JavaScript click
        3. ActionChains click
        
        Args:
            element: Element to click
            use_js: Force JavaScript click
            
        Returns:
            bool: Whether click succeeded
        """
        try:
            # Scroll into view first
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(0.2)
            
            # Strategy 1: Direct click
            if not use_js:
                try:
                    element.click()
                    return True
                except ElementClickInterceptedException:
                    pass
                except ElementNotInteractableException:
                    pass
                    
            # Strategy 2: JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                pass
                
            # Strategy 3: ActionChains
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
                return True
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"All click strategies failed: {e}")
            
        return False
        
    def find_elements_safe(self, by: By, selector: str, timeout: int = 5) -> List[WebElement]:
        """
        Find elements with implicit wait and error handling.
        
        Args:
            by: Locator type
            selector: Element selector
            timeout: Wait timeout
            
        Returns:
            List of found elements (empty if none)
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            pass
            
        try:
            return self.driver.find_elements(by, selector)
        except Exception:
            return []
