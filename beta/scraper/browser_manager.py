#!/usr/bin/env python
"""
Browser manager for Facebook scraping.
Handles Firefox browser setup, configuration, and login.
"""

import logging
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.webdriver.remote.webelement import WebElement

try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("Warning: Webdriver-manager not available. Will use local Firefox driver.")

# Configure logging
logger = logging.getLogger(__name__)

class FacebookEventListener(AbstractEventListener):
    """Event listener for Selenium actions to help with debugging"""
    
    def before_navigate_to(self, url, driver):
        logger.debug(f"Navigating to: {url}")
        
    def after_navigate_to(self, url, driver):
        logger.debug(f"Navigated to: {url}")
        
    def before_click(self, element, driver):
        logger.debug(f"Clicking element: {element.get_attribute('outerHTML')[:100]}...")
        
    def after_click(self, element, driver):
        logger.debug("Clicked element")
        
    def on_exception(self, exception, driver):
        # Avoid log spam for expected probing misses during selector checks.
        if isinstance(exception, NoSuchElementException):
            logger.debug(f"Element not found during probe: {exception}")
            return
        logger.warning(f"Exception occurred: {exception}")

class BrowserManager:
    """Manages browser sessions for Facebook scraping"""
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.logged_in = False
        self.wait = None  # Will be set after driver initialization
        self._session_active = False
        self._max_restart_attempts = 3
        self._restart_count = 0
    
    def is_session_alive(self) -> bool:
        """Check if the browser session is still active"""
        if not self.driver:
            return False
        try:
            # Try a simple operation to test if session is alive
            _ = self.driver.current_url
            return True
        except Exception:
            self._session_active = False
            return False
    
    def restart_session(self) -> bool:
        """
        Restart the browser session after a crash
        
        Returns:
            bool: Whether restart was successful
        """
        if self._restart_count >= self._max_restart_attempts:
            logger.error(f"Max restart attempts ({self._max_restart_attempts}) reached")
            return False
            
        self._restart_count += 1
        logger.info(f"Restarting browser session (attempt {self._restart_count}/{self._max_restart_attempts})")
        
        # Close existing driver if any
        self.close()
        time.sleep(2)  # Wait before restart
        
        # Start fresh
        try:
            self.start()
            self._session_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to restart session: {e}")
            return False
    
    def ensure_session(self) -> bool:
        """Ensure the browser session is alive, restart if needed"""
        if self.is_session_alive():
            return True
        return self.restart_session()
        
    def start(self):
        """Initialize and configure the browser with anti-detection measures"""
        try:
            logger.info("Starting browser initialization...")
            options = FirefoxOptions()
            
            # Enhanced Firefox configuration
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("privacy.trackingprotection.enabled", False)
            
            # Improved browser settings for better compatibility
            options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
            options.set_preference("permissions.default.image", 2)  # Disable images for faster loading
            options.set_preference("browser.cache.disk.enable", True)
            options.set_preference("browser.cache.memory.enable", True)
            options.set_preference("browser.cache.offline.enable", True)
            options.set_preference("network.http.pipelining", True)
            options.set_preference("network.http.proxy.pipelining", True)
            options.set_preference("network.http.pipelining.maxrequests", 8)
            options.set_preference("javascript.enabled", True)  # Ensure JavaScript is enabled
            
            # Add necessary arguments
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            if self.headless:
                logger.info("Configuring headless mode")
                options.add_argument("--headless")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-gpu")
                options.add_argument("--enable-javascript")
                options.add_argument("--start-maximized")
            
            # Get Firefox driver
            if WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("Using webdriver-manager to get geckodriver")
                service = FirefoxService(GeckoDriverManager().install())
            else:
                logger.info("Using local geckodriver")
                service = FirefoxService("geckodriver")
            
            # Initialize the browser
            logger.info("Creating Firefox browser instance...")
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Configure window size if not headless
            if not self.headless:
                viewports = [(1920, 1080), (1366, 768), (1440, 900)]
                width, height = random.choice(viewports)
                self.driver.set_window_size(width, height)
            
            # Add event listener for debugging
            self.driver = EventFiringWebDriver(self.driver, FacebookEventListener())
            self.wait = WebDriverWait(self.driver, 20)

            # Inject CSS/JS to hide Mongolian paywall message
            hide_script = """
            var nodes = document.querySelectorAll('body *');
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].innerText && nodes[i].innerText.includes('Та эрхээ сунгаж үзвэрээ үзнэ үү!')) {
                    nodes[i].style.display = 'none';
                }
            }
            var style = document.createElement('style');
            style.innerHTML = "*:contains('Та эрхээ сунгаж үзвэрээ үзнэ үү!'){display:none !important;}";
            document.head.appendChild(style);
            """
            try:
                self.driver.execute_script(hide_script)
            except Exception as e:
                logger.warning(f"Could not inject paywall hide script: {e}")

            logger.info("Browser initialization successful")
            self._session_active = True
            self._restart_count = 0  # Reset restart count on successful start
            return self.driver

        except Exception as e:
            error_msg = f"Browser initialization failed: {str(e)}"
            logger.error(error_msg)
            self._session_active = False
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            raise RuntimeError(error_msg)

    def verify_login(self):
        """Verify if user is logged in to Facebook"""
        # First check if session is alive
        if not self.is_session_alive():
            logger.warning("Browser session is not alive during verify_login")
            return False
            
        try:
            # Default wait of 15 seconds for the Facebook UI to load
            wait = WebDriverWait(self.driver, 15)
            
            # Try different elements that indicate successful login
            selectors = [
                '[aria-label="Home"]',       # New FB interface home button
                '[aria-label="Facebook"]',    # New FB interface logo/button
                '[role="main"]',             # Main content area
                '[role="feed"]',             # News feed
                'div[role="navigation"]',     # Navigation menu
                'div[aria-label="Facebook"]', # FB logo (alternate)
                'div[aria-label="Menu"]',     # Menu button
                'div[data-pagelet="Stories"]' # Stories section
            ]
            
            # First check URL - if we're on login page, return False
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "welcome" in current_url:
                logger.debug("On login page, not logged in")
                return False
                
            # Try each selector
            for selector in selectors:
                try:
                    logger.debug(f"Checking for selector: {selector}")
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if element.is_displayed():
                        logger.info(f"Found login indicator: {selector}")
                        self.logged_in = True
                        return True
                except Exception as e:
                    logger.debug(f"Selector {selector} not found: {e}")
                    continue
                    
            # Final check - if we're logged in, we shouldn't see login button
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="royal_login_button"]')
                if login_button.is_displayed():
                    logger.debug("Login button visible, not logged in")
                    return False
            except NoSuchElementException:
                # If login button isn't found and we're on Facebook, we're probably logged in
                if "facebook.com" in current_url:
                    logger.info("No login button found and on Facebook - assuming logged in")
                    self.logged_in = True
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error verifying login: {e}")
            return False
            
    def login_with_cookies(self) -> bool:
        """
        Attempt to log in using saved cookies from fb_credentials.py
        
        Returns:
            bool: Whether cookie-based login was successful
        """
        try:
            from fb_credentials import cookies
            logger.info("Attempting cookie-based login...")
            
            # First navigate to Facebook to set domain
            self.driver.get('https://www.facebook.com')
            time.sleep(2)
            
            # Clear existing cookies first
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
                    logger.debug(f"Added cookie: {name}")
                except Exception as e:
                    logger.warning(f"Failed to add cookie {name}: {e}")
            
            # Refresh to apply cookies
            self.driver.get('https://www.facebook.com')
            time.sleep(3)
            
            # Verify login
            if self.verify_login():
                logger.info("Cookie-based login successful!")
                self.logged_in = True
                return True
            else:
                logger.warning("Cookie-based login failed - cookies may have expired")
                return False
                
        except ImportError:
            logger.warning("No cookies found in fb_credentials.py")
            return False
        except Exception as e:
            logger.error(f"Cookie login error: {e}")
            return False
    
    def login_with_credentials(self) -> bool:
        """
        Attempt to log in using email/password from fb_credentials.py
        
        Returns:
            bool: Whether credential-based login was successful
        """
        try:
            from fb_credentials import FB_EMAIL, FB_PASSWORD
            
            if not FB_EMAIL or not FB_PASSWORD:
                logger.warning("No credentials found in fb_credentials.py")
                return False
            
            logger.info("Attempting credential-based login...")
            self.driver.get('https://www.facebook.com')
            time.sleep(2)
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            self.simulate_human_typing(email_input, FB_EMAIL)
            time.sleep(random.uniform(0.5, 1))
            
            # Enter password
            password_input = self.driver.find_element(By.ID, 'pass')
            self.simulate_human_typing(password_input, FB_PASSWORD)
            time.sleep(random.uniform(0.5, 1))
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, '[name="login"], [data-testid="royal_login_button"]')
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            if self.verify_login():
                logger.info("Credential-based login successful!")
                self.logged_in = True
                return True
            else:
                # Check for 2FA or security checks
                if 'checkpoint' in self.driver.current_url.lower():
                    logger.warning("Facebook security check detected - manual intervention required")
                return False
                
        except Exception as e:
            logger.error(f"Credential login error: {e}")
            return False

    def manual_login(self) -> bool:
        """
        Handle login process - tries cookies first, then credentials, then manual
        
        Returns:
            bool: Whether login was successful
        """
        if not self.driver:
            if not self.start():
                logger.error("Failed to start browser for login")
                return False
        
        # Ensure session is alive
        if not self.ensure_session():
            logger.error("Cannot establish browser session for login")
            return False
            
        try:
            # Step 1: Try cookie-based login first (fastest)
            logger.info("Step 1: Trying cookie-based login...")
            if self.login_with_cookies():
                return True
            
            # Step 2: Try credential-based login
            logger.info("Step 2: Trying credential-based login...")
            if self.login_with_credentials():
                return True
            
            # Step 3: Fall back to manual login
            logger.info("Step 3: Automatic login failed, requesting manual login...")
            
            # Navigate to Facebook
            self.driver.get("https://www.facebook.com")
            time.sleep(2)  # Wait for initial page load
            
            # Check if already logged in
            if self.verify_login():
                logger.info("Already logged in")
                return True
            
            # Print login instructions
            print("\n" + "="*80)
            print(" "*30 + "MANUAL LOGIN REQUIRED")
            print("="*80)
            print("1. Log in to Facebook with your credentials in the browser window")
            print("2. Complete any security checks if prompted")
            print("3. The scraper will auto-detect when you're logged in")
            print("\nNote: You have 5 minutes to complete the login process.")
            print("="*80 + "\n")
            
            # Wait for login with timeout (5 minutes)
            max_attempts = 300  # 5 minutes (1 check per second)
            attempt = 0
            
            # Cross-platform keyboard input handling
            try:
                import msvcrt  # Windows-specific
                HAS_MSVCRT = True
            except ImportError:
                HAS_MSVCRT = False
            
            while attempt < max_attempts:
                # Check if session is still alive
                if not self.is_session_alive():
                    logger.warning("Browser session died during manual login wait")
                    print("\nBrowser session was closed. Please restart the scraper.")
                    return False
                
                # First check if already logged in
                try:
                    if self.verify_login():
                        print("\nLogin detected automatically!")
                        logger.info("Login successful - auto-detected")
                        return True
                except Exception as e:
                    logger.debug(f"Login verification error: {e}")
                
                # Check for keyboard input (Windows only)
                if HAS_MSVCRT and msvcrt.kbhit():
                    # Read the input buffer until we get a complete line
                    input_buffer = []
                    while msvcrt.kbhit():
                        char = msvcrt.getwch()
                        if char == '\r':  # Enter key
                            user_input = ''.join(input_buffer).strip().lower()
                            if user_input == "done":
                                print("\nVerifying login...")
                                # Give Facebook a moment to update the UI
                                time.sleep(3)  # Increased wait time for UI update
                                
                                # Multiple verification attempts
                                for i in range(3):
                                    if self.verify_login():
                                        print("Login successful!")
                                        logger.info("Login successful - user confirmed")
                                        return True
                                    if i < 2:  # Don't sleep after last attempt
                                        time.sleep(1)
                                        print("Retrying verification...")
                                
                                print("\nLogin verification failed. Please check if you're properly logged in.")
                                print("The scraper will keep checking automatically.")
                            break
                        else:
                            input_buffer.append(char)
                            print(char, end='', flush=True)  # Echo the character
                
                # Show progress every 30 seconds
                if attempt % 30 == 0 and attempt > 0:
                    remaining = int((max_attempts - attempt) / 60)  # Convert to minutes
                    print(f"Waiting for login... ({remaining} minutes remaining)")
                
                time.sleep(1)  # Consistent 1-second sleep between checks
                attempt += 1
            
            logger.error("Login timeout - no successful login detected")
            return False
            
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            return False
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
                self._session_active = False
                self.logged_in = False
                
    def simulate_human_typing(self, element, text):
        """Simulate human-like typing patterns with random delays"""
        try:
            for char in text:
                element.send_keys(char)
                # Random delay between keystrokes
                time.sleep(random.uniform(0.1, 0.3))
                # 10% chance of a longer pause
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.error(f"Error during typing simulation: {e}")
            raise

    def simulate_human_scroll(self, step=None, max_scrolls=5, patience=3):
        """
        Simulate human-like scrolling with smart content loading detection
        
        Args:
            step: Base scroll step in pixels
            max_scrolls: Maximum number of scroll attempts
            patience: Number of attempts to wait for content to load
        """
        try:
            logger.info("Starting simulated scroll")
            if step is None:
                step = random.randint(400, 800)
            
            prev_height = 0
            no_change_count = 0
            scroll_count = 0
            
            while scroll_count < max_scrolls and no_change_count < patience:
                # Log progress
                logger.debug(f"Scroll iteration {scroll_count + 1}/{max_scrolls}")
                
                # Get current document height
                current_height = self.driver.execute_script(
                    "return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);"
                )
                
                if current_height == prev_height:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    
                prev_height = current_height
                
                # Scroll with human-like variation
                actual_step = step + random.randint(-50, 50)
                
                # Smooth scroll animation
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: window.pageYOffset + {actual_step},
                        behavior: 'smooth'
                    }});
                """)
                
                # Wait for potential dynamic content
                load_wait = random.uniform(1.5, 3.0)
                time.sleep(load_wait)
                
                # Try to detect if new content is still loading
                try:
                    loading_indicators = [
                        '[role="progressbar"]',
                        '[aria-busy="true"]',
                        '.spinner',
                        '.loading'
                    ]
                    for indicator in loading_indicators:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                        if elements and any(elem.is_displayed() for elem in elements):
                            logger.debug("Detected loading indicator, waiting...")
                            time.sleep(2)
                            break
                except Exception as e:
                    logger.debug(f"Error checking loading indicators: {e}")
                
                scroll_count += 1
                
                # Random longer pause (20% chance)
                if random.random() < 0.2:
                    time.sleep(random.uniform(1.0, 2.0))
                    
            logger.info(f"Completed scrolling after {scroll_count} iterations")
            return scroll_count > 0
            
            
        except Exception as e:
            logger.error(f"Error during scroll simulation: {e}")
            raise

    def simulate_human_click(self, element):
        """Simulate human-like clicking behavior"""
        try:
            # Create action chain
            actions = webdriver.ActionChains(self.driver)

            # Move to element with random offset
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            actions.move_to_element_with_offset(element, offset_x, offset_y)

            # Random pause before clicking
            actions.pause(random.uniform(0.1, 0.3))

            # Click
            actions.click()

            # Perform the actions
            actions.perform()

            # Random pause after clicking
            time.sleep(random.uniform(0.2, 0.5))

        except Exception as e:
            logger.error(f"Error during click simulation: {e}")
            raise
    
    def login(self, email: str, password: str, use_cookies: bool = True) -> bool:
        """
        Log into Facebook using either cookies or email/password
        
        Args:
            email: Facebook email
            password: Facebook password
            use_cookies: Whether to try cookie-based login first
            
        Returns:
            bool: Whether login was successful
        """
        try:
            # First try cookie-based login if enabled
            if use_cookies:
                try:
                    from fb_credentials import cookies
                    self.driver.get('https://www.facebook.com')
                    
                    # Add cookies
                    for name, value in cookies.items():
                        self.driver.add_cookie({
                            'name': name,
                            'value': value,
                            'domain': '.facebook.com'
                        })
                        
                    # Refresh to apply cookies
                    self.driver.get('https://www.facebook.com')
                    time.sleep(random.uniform(3, 5))
                    
                    # Check if logged in
                    if self._is_logged_in():
                        logger.info("Successfully logged in using cookies")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Cookie login failed: {str(e)}")
            
            # Fall back to email/password login
            self.driver.get('https://www.facebook.com')
            time.sleep(random.uniform(2, 4))
            
            # Enter email
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            self._type_like_human(email_input, email)
            time.sleep(random.uniform(0.5, 1))
            
            # Enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.ID, 'pass'))
            )
            self._type_like_human(password_input, password)
            time.sleep(random.uniform(0.5, 1))
            
            # Click login
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="login"]'))
            )
            login_button.click()
            
            # Wait and check login status
            time.sleep(random.uniform(3, 5))
            return self._is_logged_in()
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
            
    def _is_logged_in(self) -> bool:
        """Check if we're logged into Facebook"""
        try:
            # Wait for either the feed or the login form
            time.sleep(random.uniform(2, 4))
            
            try:
                # Check for elements that only appear when logged in
                self.wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    '[role="navigation"]'
                )))
                return True
            except TimeoutException:
                return False
                
        except Exception:
            return False
            
    def _type_like_human(self, element: WebElement, text: str):
        """Type text with random delays between characters"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
    
    def find_main_content(self, max_retries=3, wait_time=2):
        """
        Try multiple selectors to find the main Facebook content area.
        Returns the element if found, else None.
        """
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
        """
        Detect if the current page is a Facebook login or checkpoint page.
        Returns True if login is required.
        """
        try:
            # Check for login form
            if self.driver.find_elements(By.NAME, 'email') and self.driver.find_elements(By.NAME, 'pass'):
                logger.info("Detected Facebook login page.")
                return True
            # Check for checkpoint/interstitial
            if 'checkpoint' in self.driver.current_url or 'login' in self.driver.current_url:
                logger.info(f"Detected checkpoint or login in URL: {self.driver.current_url}")
                return True
        except Exception as e:
            logger.warning(f"Error checking login page: {e}")
        return False

    def verify_page_load(self, timeout=30) -> bool:
        """
        Verify that a page has fully loaded and handle any redirects
        
        Args:
            timeout: Maximum time to wait for page load in seconds
            
        Returns:
            bool: Whether the page loaded successfully
        """
        try:
            # Wait for the initial page load
            self.wait.until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            start_url = self.driver.current_url
            time.sleep(2)  # Short wait for any immediate redirects
            
            # Check if we were redirected
            if self.driver.current_url != start_url:
                logger.info(f"Detected redirect: {start_url} -> {self.driver.current_url}")
                self.wait.until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
            
            # Check for login/interstitial
            if self.is_login_page():
                logger.warning(f"Login or checkpoint page detected at {self.driver.current_url}")
                return False
            # Try to find main content
            main_content = self.find_main_content()
            if main_content is not None:
                logger.info("Main content found. Page loaded successfully.")
                return True
            else:
                logger.error(f"Main content not found after page load. URL: {self.driver.current_url}, Title: {self.driver.title}")
                return False
        except Exception as e:
            logger.warning(f"Exception during page load verification: {e}")
            logger.debug(f"Current URL: {self.driver.current_url}, Title: {self.driver.title}")
            return False
        
    def navigate_to(self, url: str, max_retries: int = 3) -> bool:
        """
        Navigate to a URL with retry logic and verification
        
        Args:
            url: The URL to navigate to
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: Whether navigation was successful
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Navigating to {url} (attempt {retry_count + 1}/{max_retries})")
                
                # Clear browser data if this is a retry
                if retry_count > 0:
                    self.driver.delete_all_cookies()
                    self.driver.execute_script("window.localStorage.clear();")
                    self.driver.execute_script("window.sessionStorage.clear();")
                
                # Navigate to the URL
                self.driver.get(url)
                
                # Verify page load
                if self.verify_page_load():
                    # Additional check for Facebook-specific error pages
                    error_texts = [
                        "Sorry, something went wrong",
                        "Page Not Found",
                        "Content Not Found",
                        "This content isn't available right now"
                    ]
                    
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if any(error in page_text for error in error_texts):
                        logger.warning("Detected Facebook error page")
                        retry_count += 1
                        time.sleep(5)  # Wait before retry
                        continue
                    
                    logger.info("Page loaded successfully")
                    return True
                    
                retry_count += 1
                time.sleep(5)  # Wait before retry
                
            except Exception as e:
                logger.error(f"Navigation error: {e}")
                retry_count += 1
                time.sleep(5)  # Wait before retry
                
        logger.error(f"Failed to navigate to {url} after {max_retries} attempts")
        return False
