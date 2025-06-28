#!/usr/bin/env python
"""
Comment Extraction Test Script
For verifying if a post contains comments and scraping them using improved methods
"""

import sys
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    print("Error: Missing required packages. Run: pip install selenium webdriver-manager")
    sys.exit(1)

def setup_firefox():
    """Set up Firefox browser for testing"""
    try:
        options = FirefoxOptions()
        
        # Set preferences for better performance
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("media.volume_scale", "0.0")  # Mute audio
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_window_size(1366, 768)
        
        return driver
    except Exception as e:
        logger.error(f"Error setting up Firefox: {e}")
        return None

def manual_login(driver):
    """Perform manual login to Facebook"""
    try:
        driver.get("https://www.facebook.com/")
        
        print("\n" + "="*80)
        print("MANUAL LOGIN REQUIRED")
        print("="*80)
        print("1. Log in to Facebook with your credentials in the browser window")
        print("2. Complete any security checks if prompted")
        print("3. Return to this terminal when logged in")
        print("4. Type 'done' and press Enter to continue")
        print("="*80)
        
        user_input = input("After logging in, type 'done' here: ")
        
        if user_input.strip().lower() == 'done':
            time.sleep(3)  # Wait for page to load after login
            
            # Check if successfully logged in
            search_box = driver.find_elements(By.XPATH, "//input[@aria-label='Search Facebook' or @placeholder='Search Facebook']")
            
            if search_box:
                print("✅ Successfully logged in to Facebook!")
                return True
        
        print("❌ Failed to log in or verify login")
        return False
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return False

def test_post_comments(driver, post_url):
    """Test extracting comments from a post using different methods"""
    try:
        print(f"\nNavigating to post: {post_url}")
        driver.get(post_url)
        time.sleep(5)
        
        # Create debug directory if it doesn't exist
        debug_dir = os.path.join(ROOT_DIR, "debug")
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
            
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(debug_dir, f"test_post_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Check if post has comments indicator
        comment_indicators = driver.find_elements(By.XPATH, 
            "//span[contains(text(), 'comment') or contains(text(), 'Comment')]")
        
        comment_count = 0
        for indicator in comment_indicators:
            match = re.search(r'(\d+)\s*comment', indicator.text.lower())
            if match:
                comment_count = int(match.group(1))
                print(f"Found comment indicator: {indicator.text} (count: {comment_count})")
                break
        
        # Try to click on comments section
        comment_selectors = [
            "//span[contains(text(), 'comment')]/ancestor::div[@role='button']",
            "//a[contains(text(), 'comment')]",
            "//span[contains(text(), 'Comment')]/ancestor::div[@role='button']"
        ]
        
        clicked = False
        for selector in comment_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        print(f"Clicking comments section: {element.text}")
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                        clicked = True
                        break
                except Exception as e:
                    print(f"Failed to click element: {e}")
            
            if clicked:
                break
                
        # Take another screenshot after clicking comments
        if clicked:
            screenshot_path = os.path.join(debug_dir, f"test_post_comments_expanded_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot after expanding comments: {screenshot_path}")
            
            # Expand more comments if available
            for i in range(5):  # Try up to 5 times
                view_more_buttons = driver.find_elements(By.XPATH, 
                    "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']")
                
                if not view_more_buttons:
                    view_more_buttons = driver.find_elements(By.XPATH, 
                        "//div[@role='button' and contains(., 'View more comments')]")
                        
                if not view_more_buttons:
                    break
                    
                for button in view_more_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Clicking 'View more comments' button ({i+1})")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            break
                    except Exception as e:
                        print(f"Failed to click view more: {e}")
                        
            # Now look for actual comments
            comment_elements = []
            
            # Try multiple comment selector patterns
            comment_selectors = [
                "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
                "//div[contains(@class, 'comments-comment-item')]",
                "//div[contains(@data-testid, 'UFI2Comment')]",
                "//div[@data-testid='comment']",
                "//div[@role='article' and contains(@class, 'comment')]"
            ]
            
            for selector in comment_selectors:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    comment_elements = elements
                    print(f"Found {len(elements)} comments using selector: {selector}")
                    break
            
            # Extract sample comment details
            for i, comment in enumerate(comment_elements[:5], 1):  # Show first 5 comments
                try:
                    # Try to get author and text
                    author_element = comment.find_element(By.XPATH, ".//a[contains(@class, 'actor') or @role='link']")
                    author = author_element.text if author_element else "Unknown"
                    
                    text_element = comment.find_element(By.XPATH, ".//span[@dir='auto'] | .//div[contains(@class, 'comment-content')]")
                    text = text_element.text if text_element else "No text"
                    
                    print(f"Comment {i}: Author='{author}', Text='{text[:50]}...'")
                except Exception as e:
                    print(f"Error extracting comment {i}: {e}")
            
            # Final screenshot
            screenshot_path = os.path.join(debug_dir, f"test_post_comments_final_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            
            found_comments = len(comment_elements)
            print(f"\nSummary: Found {found_comments} comments")
            
            if comment_count > 0:
                if found_comments >= comment_count:
                    print(f"✅ Successfully found all expected comments ({found_comments} ≥ {comment_count})")
                else:
                    print(f"⚠️ Found fewer comments than expected ({found_comments} < {comment_count})")
            else:
                if found_comments > 0:
                    print(f"✅ Found {found_comments} comments despite no count indicator")
                else:
                    print("⚠️ No comments found and no count indicator")
        else:
            print("❌ Couldn't expand comments section")
                
    except Exception as e:
        print(f"❌ Error testing post: {e}")

def main():
    """Main function"""
    print("\n" + "="*80)
    print("FACEBOOK COMMENT EXTRACTION TESTER")
    print("="*80)
    
    # Set up driver
    driver = setup_firefox()
    if not driver:
        print("Failed to set up Firefox browser")
        return 1
        
    try:
        # Login
        if not manual_login(driver):
            return 1
            
        # Get post URL from user
        print("\nEnter a Facebook post URL to test comment extraction:")
        post_url = input("Post URL: ").strip()
        
        if not post_url:
            print("No URL provided")
            return 1
            
        # Test comment extraction
        test_post_comments(driver, post_url)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 130
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed")
            except:
                pass

if __name__ == "__main__":
    sys.exit(main())
