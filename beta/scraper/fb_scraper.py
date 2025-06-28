from pathlib import Path
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class FacebookScraper:
    def __init__(self, headless=False, max_comments=100):
        self.headless = headless
        self.max_comments = max_comments
        self.driver = None
        
    def start(self):
        """Initialize the browser"""
        options = Options()
        if self.headless:
            options.add_argument("-headless")
            
        # Set preferences
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("media.volume_scale", "0.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_window_size(1366, 768)
        
    def login(self):
        """Manual login process"""
        if not self.driver:
            self.start()
            
        self.driver.get("https://www.facebook.com")
        print("Please log in to Facebook manually...")
        print("Type 'done' and press Enter when finished...")
        
        while input().lower() != 'done':
            print("Please type 'done' when you've logged in...")
            
        return self._check_login()
        
    def _check_login(self):
        """Verify login status"""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='navigation']"))
            )
            return True
        except:
            return False
            
    def scrape_page(self, page_name, max_posts=10):
        """Scrape posts from a Facebook page"""
        try:
            if not self.driver:
                self.start()
                
            url = f"https://www.facebook.com/{page_name}"
            self.driver.get(url)
            time.sleep(3)
            
            posts = []
            post_elements = self._get_posts(max_posts)
            
            for post in post_elements:
                post_data = self._extract_post(post, page_name)
                if post_data:
                    # Get comments if available
                    has_comments = self._check_comments(post)
                    if has_comments:
                        comments = self._extract_comments(post_data['post_url'])
                        post_data['comments'] = comments
                    
                    posts.append(post_data)
                    
            return posts
            
        except Exception as e:
            print(f"Error scraping page {page_name}: {e}")
            return []
            
    def _get_posts(self, max_posts):
        """Get post elements from page"""
        posts = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while len(posts) < max_posts:
            # Scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get posts
            elements = self.driver.find_elements(By.XPATH, "//div[@role='article']")
            posts = elements[:max_posts]
            
            # Check if we reached bottom
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        return posts
        
    def _extract_post(self, post_element, page_name):
        """Extract data from a post"""
        try:
            # Take screenshot
            screenshot = self._take_screenshot(post_element)
            
            # Get post URL
            url_elem = post_element.find_element(By.XPATH, ".//a[contains(@href, '/posts/')]")
            post_url = url_elem.get_attribute('href')
            
            # Get post text
            text_elem = post_element.find_element(By.XPATH, ".//div[@data-ad-preview='message']")
            text = text_elem.text
            
            return {
                'post_id': str(int(time.time())) + "_" + page_name,
                'page_name': page_name,
                'post_url': post_url,
                'post_text': text,
                'screenshot': screenshot,
                'extracted_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error extracting post: {e}")
            return None
            
    def _check_comments(self, post_element):
        """Check if post has comments"""
        try:
            comment_elements = post_element.find_elements(By.XPATH, 
                ".//span[contains(text(), 'comment') or contains(text(), 'Comment')]")
            return len(comment_elements) > 0
        except:
            return False
            
    def _extract_comments(self, post_url, max_depth=3):
        """Extract comments from a post URL"""
        try:
            self.driver.get(post_url)
            time.sleep(2)
            
            # Expand comments
            self._expand_comments()
            
            # Get comment elements
            comments = []
            elements = self.driver.find_elements(By.XPATH, "//div[@role='article' and contains(@aria-label, 'Comment')]")
            
            for element in elements[:self.max_comments]:
                try:
                    comment = {
                        'text': element.find_element(By.XPATH, ".//div[@dir='auto']").text,
                        'author': element.find_element(By.XPATH, ".//a[@role='link']").text,
                        'timestamp': element.find_element(By.XPATH, ".//a[contains(@href, 'comment_id')]").text
                    }
                    
                    # Get replies
                    if max_depth > 0:
                        replies = self._get_replies(element, max_depth - 1)
                        if replies:
                            comment['replies'] = replies
                            
                    comments.append(comment)
                except:
                    continue
                    
            return comments
            
        except Exception as e:
            print(f"Error extracting comments: {e}")
            return []
            
    def _expand_comments(self):
        """Expand all comments"""
        for _ in range(10):  # Try up to 10 times
            try:
                buttons = self.driver.find_elements(By.XPATH,
                    "//span[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]")
                if not buttons:
                    break
                    
                for button in buttons:
                    try:
                        button.click()
                        time.sleep(1)
                    except:
                        continue
            except:
                break
                
    def _get_replies(self, comment_element, depth):
        """Get replies to a comment"""
        try:
            # Click view replies if present
            try:
                reply_button = comment_element.find_element(By.XPATH, 
                    ".//span[contains(text(), 'View') and contains(text(), 'repl')]")
                reply_button.click()
                time.sleep(1)
            except:
                return []
                
            # Get reply elements
            replies = []
            elements = comment_element.find_elements(By.XPATH, ".//div[@role='article' and contains(@aria-label, 'Comment reply')]")
            
            for element in elements:
                try:
                    reply = {
                        'text': element.find_element(By.XPATH, ".//div[@dir='auto']").text,
                        'author': element.find_element(By.XPATH, ".//a[@role='link']").text,
                        'timestamp': element.find_element(By.XPATH, ".//a[contains(@href, 'comment_id')]").text
                    }
                    
                    if depth > 0:  # Get nested replies if any
                        nested = self._get_replies(element, depth - 1)
                        if nested:
                            reply['replies'] = nested
                            
                    replies.append(reply)
                except:
                    continue
                    
            return replies
            
        except Exception as e:
            print(f"Error getting replies: {e}")
            return []
            
    def _take_screenshot(self, element):
        """Take screenshot of an element"""
        try:
            return element.screenshot_as_png
        except:
            return None
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
