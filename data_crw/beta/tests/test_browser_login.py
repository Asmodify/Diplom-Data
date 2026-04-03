#!/usr/bin/env python
"""
Test browser login and cookie saving functionality
"""
import logging
import json
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.browser_manager import BrowserManager
from fb_credentials import FB_EMAIL, FB_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_browser_login_and_cookie_save():
    """Test login with password and save cookies for future use"""
    browser = None
    try:
        # Initialize browser
        browser = BrowserManager(headless=False)
        browser.start()
        
        # Try to login with email/password
        logger.info("Attempting login with email/password...")
        success = browser.login(FB_EMAIL, FB_PASSWORD, use_cookies=False)
        
        if not success:
            logger.error("Failed to login with email/password")
            return False
            
        logger.info("Successfully logged in!")
        
        # Get cookies after successful login
        cookies = browser.driver.get_cookies()
        
        # Convert cookies to the format we want to save
        cookie_dict = {}
        for cookie in cookies:
            if cookie['domain'] == '.facebook.com':
                cookie_dict[cookie['name']] = cookie['value']
                
        # Save cookies to a file
        cookie_path = Path(__file__).parent.parent / 'fb_credentials.py'
        
        # Read existing content
        with open(cookie_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find where to insert cookies
        cookie_str = "cookies = " + json.dumps(cookie_dict, indent=4)
        
        # If cookies section exists, replace it
        if "cookies = {" in content:
            lines = content.split('\n')
            start_idx = next(i for i, line in enumerate(lines) if line.strip().startswith('cookies = {'))
            end_idx = next(i for i in range(start_idx, len(lines)) if lines[i].strip() == '}')
            lines[start_idx:end_idx+1] = cookie_str.split('\n')
            new_content = '\n'.join(lines)
        else:
            # Otherwise append it
            new_content = content + "\n\n# Cookie-based authentication\n" + cookie_str
            
        # Save updated content
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logger.info(f"Saved {len(cookie_dict)} cookies to {cookie_path}")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False
        
    finally:
        if browser:
            browser.close()

if __name__ == "__main__":
    test_browser_login_and_cookie_save()
