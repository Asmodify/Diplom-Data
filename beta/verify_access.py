#!/usr/bin/env python
"""
Verify Facebook access by checking login status using Firefox
"""

import sys
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
try:
    from webdriver_manager.firefox import GeckoDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.config import LOGS_DIR, DEBUG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'verify_access.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Initialize Firefox driver with optimized settings"""
    logger.info("Setting up Firefox driver...")
    try:
        # Configure Firefox options
        options = FirefoxOptions()
        options.set_preference("dom.webnotifications.enabled", False)  # Disable notifications
        options.headless = True  # Run in headless mode
        
        # Try with WebDriver Manager if available
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                logger.info("Using WebDriver Manager for Firefox setup")
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            except Exception as e:
                logger.warning(f"WebDriver Manager approach failed: {e}")
                # Fall back to direct Firefox setup
                logger.info("Falling back to direct Firefox setup")
                driver = webdriver.Firefox(options=options)
        else:
            # Direct Firefox setup
            logger.info("WebDriver Manager not available, using direct Firefox setup")
            driver = webdriver.Firefox(options=options)
        
        logger.info("Firefox browser set up successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Error setting up Firefox browser: {e}")
        # Save detailed error information
        error_log_path = DEBUG_DIR / f"browser_error_{int(time.time())}.txt"
        with open(error_log_path, "w") as f:
            f.write(f"Error: {e}\n")
            
        raise RuntimeError(f"Could not initialize Firefox browser: {e}")

def verify_facebook_access(mock=False):
    """Verify Facebook access using cookies"""
    # Mock mode is no longer supported
    if mock:
        logger.warning("Mock mode is no longer supported - always using real browser verification")
    
    # Ensure directories exist
    LOGS_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    
    # Try to import cookies
    try:
        sys.path.append(str(ROOT_DIR))
        from fb_credentials import cookies
        logger.info("Found cookies in fb_credentials.py")
    except ImportError:
        logger.error("Could not import cookies from fb_credentials.py")
        return False
    
    driver = None
    try:
        # Setup driver
        try:
            driver = setup_driver()
        except Exception as e:
            logger.error(f"Error verifying Facebook access: {e}")
            # Don't override the error status - if driver setup fails, verification fails
            return False
        
        # Visit Facebook and add cookies
        logger.info("Navigating to Facebook...")
        driver.get("https://www.facebook.com")
        time.sleep(2)
        
        # Add cookies
        logger.info("Adding cookies...")
        for name, value in cookies.items():
            driver.add_cookie({"name": name, "value": value})
        
        # Refresh page
        driver.refresh()
        time.sleep(2)
        
        # Check if logged in
        logger.info("Checking login status...")
        
        try:
            # Try multiple selectors that might indicate login success
            login_success = False
            
            # Save current page source and screenshot for analysis
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            html_path = DEBUG_DIR / f"page_source_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            # Try multiple selectors that might indicate successful login
            selectors = [
                "div[role='navigation']", 
                "div[aria-label*='profile']", 
                "div[aria-label*='menu']",
                "a[aria-label*='profile']",
                "div[data-pagelet='Stories']",
                "div[role='main']"
            ]
            
            for selector in selectors:
                try:
                    # Short timeout per selector attempt
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Login verified! Found element with selector: {selector}")
                    login_success = True
                    break
                except Exception:
                    continue
            
            if login_success:
                # Save screenshot for verification
                screenshot_path = DEBUG_DIR / f"access_verified_{timestamp}.png"
                driver.save_screenshot(str(screenshot_path))
                return True
            else:
                # Check for login form - if not present, we might be logged in
                if len(driver.find_elements(By.CSS_SELECTOR, "form#login_form")) == 0:
                    # No login form, we might be logged in but without typical navigation
                    logger.info("No login form found, may have partial access")
                    screenshot_path = DEBUG_DIR / f"access_verified_{timestamp}.png"
                    driver.save_screenshot(str(screenshot_path))
                    return True
                    
                logger.error("Could not verify login - no known elements found")
                screenshot_path = DEBUG_DIR / f"access_failed_{timestamp}.png"
                driver.save_screenshot(str(screenshot_path))
                return False
                
        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            
            # Save error screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = DEBUG_DIR / f"access_failed_{timestamp}.png"
            driver.save_screenshot(str(screenshot_path))
            return False
            
    except Exception as e:
        logger.error(f"Error verifying Facebook access: {e}")
        return False
    finally:
        # Close browser
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Facebook access')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (deprecated)')
    args = parser.parse_args()
    
    if args.mock:
        logger.warning("Mock mode is deprecated - running with real verification")
    
    if verify_facebook_access(mock=False):
        logger.info("✅ Facebook access verified")
        print("Facebook access verified!")
        return 0
    else:
        logger.error("❌ Facebook access verification failed")
        print("Facebook access verification failed!")
        return 1
        
if __name__ == "__main__":
    sys.exit(main())
