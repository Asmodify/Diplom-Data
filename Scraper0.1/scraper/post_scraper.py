from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import re
import time
from bs4 import BeautifulSoup
from db.database import DatabaseManager
from db.models import PostComment

def clean_text(text: str) -> str:
    # Remove Mongolian paywall message and extra whitespace
    paywall_msg = "Та эрхээ сунгаж үзвэрээ үзнэ үү!"
    return text.replace(paywall_msg, "").strip()

def sanitize_filename(name: str) -> str:
    # Remove or replace invalid filename characters for Windows and query params
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.replace('=', '_').replace('?', '_').replace('&', '_')
    return name

logger = logging.getLogger(__name__)

class PostScraper:
    def __init__(self, driver, wait_time=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_time)
        self.db = DatabaseManager()

    def extract_post_date(self, elem) -> Optional[datetime]:
        # Try to extract post date from element (may need adjustment for Facebook's structure)
        try:
            # Look for a <abbr> or <span> with a timestamp or aria-label
            time_elem = elem.find_element(By.TAG_NAME, 'abbr')
            date_str = time_elem.get_attribute('aria-label') or time_elem.text
            # Try to parse date string
            from dateparser import parse
            post_date = parse(date_str, languages=['en'])
            return post_date
        except Exception:
            return None

    def scroll_page(self, scrolls=20, pause=2, min_new_posts=2):
        # Scroll until no new posts are loaded or max scrolls reached
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(scrolls):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                return
            last_height = new_height

    def take_screenshot(self, elem, full_path):
        self.driver.execute_script("arguments[0].scrollIntoView();", elem)
        time.sleep(0.2)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        elem.screenshot(full_path)
        return full_path

    def extract_post_meta(self, elem):
        # Try to extract author, date, likes, shares, comments count
        meta = {}
        try:
            # Author
            author_elem = elem.find_element(By.CSS_SELECTOR, 'h2 span a, strong a')
            meta['author'] = author_elem.text
        except Exception:
            meta['author'] = None
        try:
            # Date
            meta['date'] = self.extract_post_date(elem)
        except Exception:
            meta['date'] = None
        try:
            # Likes, comments, shares (may need adjustment)
            footer = elem.find_element(By.XPATH, ".//*[contains(text(),'Like') or contains(text(),'Share') or contains(text(),'Comment')]/ancestor::div[1]")
            meta['likes'] = self._extract_number_from_text(footer.text, 'Like')
            meta['comments'] = self._extract_number_from_text(footer.text, 'Comment')
            meta['shares'] = self._extract_number_from_text(footer.text, 'Share')
        except Exception:
            meta['likes'] = meta['comments'] = meta['shares'] = None
        return meta

    def _extract_number_from_text(self, text, keyword):
        match = re.search(rf"(\d+) {keyword}", text)
        return int(match.group(1)) if match else None

    def scrape_post(self, post_url: str) -> Optional[Dict[str, Any]]:
        try:
            self.driver.get(post_url)
            self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            # Example: find post content
            content_elem = self.driver.find_element(By.CSS_SELECTOR, 'div[data-ad-preview="message"]')
            content = clean_text(content_elem.text)
            return {'url': post_url, 'content': content}
        except Exception as e:
            logger.warning(f"Failed to scrape post {post_url}: {e}")
            return None

    def scroll_until_posts(self, selectors, max_scrolls=30, pause=2):
        # Scroll until at least one post is found or max_scrolls reached
        for i in range(max_scrolls):
            found = False
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    found = True
                    break
            if found:
                return True
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(pause)
        return False

    def slow_scroll(self, step=500, pause=2):
        """Scroll the page slowly by a given pixel step."""
        self.driver.execute_script(f"window.scrollBy(0, {step});")
        time.sleep(pause)

    def click_comment_button(self):
        """
        Robustly click the comment button for all post types, always inside the post modal/footer.
        Tries by label ("Comment", "Сэтгэгдэл"), icon, and position (middle button), with debug logging and HTML saving.
        If no such button exists, return False (no comments for this post).
        """
        try:
            # Wait for modal to appear (should contain role="dialog" or aria-modal)
            modal = None
            for sel in [
                'div[role="dialog"]',
                'div[aria-modal="true"]',
                'div[aria-label*="Post"]',
            ]:
                try:
                    modal = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if modal:
                        break
                except Exception:
                    continue
            if not modal:
                logger.warning("No post modal found for comment button click.")
                return False

            # Try to find the modal footer (where Like/Comment/Share are)
            footer = None
            for sel in [
                'footer',
                'div[role="toolbar"]',
                'div[aria-label*="actions"]',
                'div[aria-label*="Footer"]',
                'div[role="group"]',
            ]:
                try:
                    footers = modal.find_elements(By.CSS_SELECTOR, sel)
                    # Pick the one with 3-5 buttons
                    for f in footers:
                        btns = f.find_elements(By.XPATH, ".//div[@role='button']")
                        if 2 < len(btns) < 6:
                            footer = f
                            break
                    if footer:
                        break
                except Exception:
                    continue
            if not footer:
                logger.info("No modal footer found for comment button click. This post likely has no comments. Saving modal HTML for debug.")
                with open("modal_debug.html", "w", encoding="utf-8") as f:
                    f.write(modal.get_attribute("outerHTML"))
                return False

            # Find all buttons in the footer
            buttons = footer.find_elements(By.XPATH, ".//div[@role='button']")
            comment_btn = None
            # 1. Try by label/text
            for btn in buttons:
                txt = btn.text.strip().lower()
                aria = btn.get_attribute("aria-label") or ""
                if any(x in txt for x in ["comment", "сэтгэгдэл"]) or any(x in aria.lower() for x in ["comment", "сэтгэгдэл"]):
                    comment_btn = btn
                    break
            # 2. Try by SVG icon (aria-label or data-testid)
            if not comment_btn:
                for btn in buttons:
                    try:
                        svg = btn.find_element(By.XPATH, ".//svg")
                        aria = svg.get_attribute("aria-label") or ""
                        datatest = svg.get_attribute("data-testid") or ""
                        if "comment" in aria.lower() or "comment" in datatest.lower():
                            comment_btn = btn
                            break
                    except Exception:
                        continue
            # 3. Fallback: pick the middle button if 3 or 4 buttons
            if not comment_btn and 2 < len(buttons) < 6:
                comment_btn = buttons[len(buttons)//2]
            if comment_btn:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comment_btn)
                    time.sleep(0.1)
                    comment_btn.click()
                    time.sleep(0.5)
                    return True
                except Exception as e:
                    logger.error(f"Failed to click comment button: {e}")
                    return False
            else:
                logger.info("No comment button found in modal footer. This post likely has no comments. Saving modal HTML for debug.")
                with open("modal_debug.html", "w", encoding="utf-8") as f:
                    f.write(modal.get_attribute("outerHTML"))
                return False
        except Exception as e:
            logger.error(f"Error in click_comment_button: {e}")
            return False

    def scrape_posts(self, page_url: str, min_posts: int = 10):
        self.driver.get(page_url)
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        selectors = [
            'div[role="article"]',
            'div[data-ad-preview="message"]',
            'div[aria-label="Reel"]',
            'div[aria-label="Video post"]',
        ]
        page_name = page_url.rstrip('/').split('/')[-1] or sanitize_filename(page_url.split('/')[-1])
        if 'profile.php' in page_url:
            page_name = 'profile_' + re.sub(r'\W+', '_', page_url.split('id=')[-1])
        base_dir = os.path.join('data', page_name)
        posts_dir = os.path.join(base_dir, 'posts')
        screenshots_dir = os.path.join(base_dir, 'screenshots')
        images_dir = os.path.join(base_dir, 'images')
        os.makedirs(posts_dir, exist_ok=True)
        os.makedirs(screenshots_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        five_days_ago = datetime.now() - timedelta(days=5)
        seen_posts = set()
        all_posts = []
        # --- REWRITE: Robust Selenium-only scrolling and post detection ---
        seen_post_elems = set()
        all_posts = []
        max_scrolls = 60
        scroll_step = 300  # pixels per scroll
        scroll_pause = 0.08  # fast but not too fast
        posts_found = set()
        for scroll_num in range(max_scrolls):
            # Scroll bit by bit, stop as soon as a new post is detected
            self.driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            time.sleep(scroll_pause)
            # Use Selenium to find post elements directly
            post_elems = []
            for selector in selectors:
                post_elems.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
            new_post_detected = False
            for idx, elem in enumerate(post_elems):
                # Use id, data-ft, or fallback to hash of text for uniqueness
                post_key = elem.get_attribute('data-ft') or elem.get_attribute('id') or (elem.text[:40] if elem.text else str(idx))
                if post_key in posts_found:
                    continue
                posts_found.add(post_key)
                new_post_detected = True
                if len(all_posts) >= 10:
                    break  # Only break the inner loop if post limit reached
                post_id = f"post_{idx}_{int(time.time())}"
                modal_opened = False
                comments = []
                post_meta = self.extract_post_meta(elem)
                post_url = None
                # Try to get a post URL (timestamp link or fallback)
                try:
                    timestamp_link = elem.find_element(By.XPATH, ".//a[contains(@href, 'posts/') or contains(@href, '/posts/') or contains(@href, 'photo.php') or contains(@href, 'video.php')]")
                    post_url = timestamp_link.get_attribute('href')
                except Exception:
                    post_url = None
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                    time.sleep(0.2)
                    # Try to find the timestamp link
                    timestamp_link = None
                    try:
                        timestamp_link = elem.find_element(By.XPATH, ".//a[contains(@href, 'posts/') or contains(@href, '/posts/') or contains(@href, 'photo.php') or contains(@href, 'video.php')]")
                    except Exception as e:
                        logger.debug(f"No timestamp/main link: {e}")
                    # Try to open modal: timestamp, then comment button, then fallback
                    if timestamp_link:
                        try:
                            self.wait.until(EC.element_to_be_clickable(timestamp_link))
                            timestamp_link.click()
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                            )
                            modal_opened = True
                            logger.info(f"Opened modal via timestamp for post_id={post_id}")
                        except Exception as e:
                            logger.debug(f"Timestamp click failed: {e}")
                            try:
                                self.driver.execute_script("arguments[0].click();", timestamp_link)
                                WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                                )
                                modal_opened = True
                                logger.info(f"Opened modal via timestamp (JS click) for post_id={post_id}")
                            except Exception as e2:
                                logger.debug(f"Timestamp JS click failed: {e2}")
                                try:
                                    ActionChains(self.driver).move_to_element(timestamp_link).click().perform()
                                    WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                                    )
                                    modal_opened = True
                                    logger.info(f"Opened modal via timestamp (ActionChains) for post_id={post_id}")
                                except Exception as e3:
                                    logger.debug(f"Timestamp ActionChains click failed: {e3}")
                    if not modal_opened:
                        # Try comment button(s) for video posts
                        comment_btn = None
                        comment_btn_selectors = [
                            ".//div[@aria-label='Comment']",
                            ".//span[contains(text(),'Comment') or contains(text(),'сэтгэгдэл')]/ancestor::div[@role='button']",
                            ".//div[@aria-label='Write a comment']",
                            ".//div[@aria-label='Write a comment…']",
                            ".//div[@aria-label='Write a comment...']",
                            ".//div[@aria-label='Leave a comment']",
                            ".//div[@role='button' and descendant::svg[@aria-label='Comment']]",
                            ".//span[contains(text(),'See comments') or contains(text(),'View comments')]/ancestor::div[@role='button']",
                            ".//span[contains(text(),'See comments') or contains(text(),'View comments')]/ancestor::button",
                        ]
                        for sel in comment_btn_selectors:
                            try:
                                btns = elem.find_elements(By.XPATH, sel)
                                if btns:
                                    comment_btn = btns[0]
                                    break
                            except Exception:
                                continue
                        if comment_btn:
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comment_btn)
                                time.sleep(0.1)
                                self.wait.until(EC.element_to_be_clickable(comment_btn))
                                comment_btn.click()
                                WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                                )
                                modal_opened = True
                                logger.info(f"Opened modal via comment button for post_id={post_id}")
                            except Exception as e:
                                logger.debug(f"Comment button click failed: {e}")
                                try:
                                    self.driver.execute_script("arguments[0].click();", comment_btn)
                                    WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                                    )
                                    modal_opened = True
                                    logger.info(f"Opened modal via comment button (JS click) for post_id={post_id}")
                                except Exception as e2:
                                    logger.debug(f"Comment button JS click failed: {e2}")
                                    try:
                                        ActionChains(self.driver).move_to_element(comment_btn).click().perform()
                                        WebDriverWait(self.driver, 10).until(
                                            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                                        )
                                        modal_opened = True
                                        logger.info(f"Opened modal via comment button (ActionChains) for post_id={post_id}")
                                    except Exception as e3:
                                        logger.debug(f"Comment button ActionChains click failed: {e3}")
                        else:
                            logger.debug("No comment button found for modal open.")
                    if not modal_opened:
                        # Fallback: try clicking the post container itself with JS
                        try:
                            self.driver.execute_script("arguments[0].click();", elem)
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                            )
                            modal_opened = True
                            logger.info(f"Opened modal via post container for post_id={post_id}")
                        except Exception as e2:
                            logger.error(f"Fallback JS click on post container also failed: {e2}")
                            # Save HTML for debug
                            debug_dir = os.path.join(base_dir, 'debug')
                            os.makedirs(debug_dir, exist_ok=True)
                            fname = f"failed_post_{post_id}.html"
                            with open(os.path.join(debug_dir, fname), 'w', encoding='utf-8') as f:
                                f.write(elem.get_attribute("outerHTML"))
                    if modal_opened:
                        try:
                            modal = self.driver.find_element(By.XPATH, "//div[@aria-label='Comments' or @role='dialog']")
                            comments = []
                            seen_comment_ids = set()
                            last_count = 0
                            scroll_attempts = 0
                            max_scrolls_modal = 40
                            for _ in range(max_scrolls_modal):
                                new_comments = self.extract_modal_comments(modal, post_id, base_dir)
                                for c in new_comments:
                                    c_id = c.get('id') or c.get('text')
                                    if c_id and c_id not in seen_comment_ids:
                                        comments.append(c)
                                        seen_comment_ids.add(c_id)
                                if len(comments) >= 50:
                                    comments = comments[:50]
                                    break
                                more_btns = modal.find_elements(By.XPATH, ".//span[contains(text(),'View more comments') or contains(text(),'See more comments') or contains(text(),'More Comments')]/ancestor::div[@role='button']")
                                for btn in more_btns:
                                    try:
                                        self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                                        btn.click()
                                        time.sleep(0.15)
                                    except Exception:
                                        continue
                                time.sleep(0.25)
                                # Find the scrollable container inside the modal
                                scrollable = None
                                try:
                                    # Try common selectors for Facebook's scrollable comment area
                                    for sel in [
                                        'div[aria-label="Comments"]',
                                        'div[aria-label="comments"]',
                                        'div[role="dialog"] div[role="main"]',
                                        'div[role="dialog"] div[tabindex="0"]',
                                        'div[role="dialog"] div[style*="overflow-y: auto"]',
                                    ]:
                                        found = modal.find_elements(By.CSS_SELECTOR, sel)
                                        if found:
                                            scrollable = found[0]
                                            break
                                except Exception:
                                    scrollable = None
                                if not scrollable:
                                    scrollable = modal  # fallback
                                # Incremental scroll inside the scrollable container
                                for scroll_y in range(0, 2000, 200):
                                    self.driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable, scroll_y)
                                    time.sleep(0.08)
                        except Exception as e:
                            logger.error(f"Error extracting or scrolling modal comments: {e}")
                except Exception as e:
                    logger.error(f"Modal extraction failed: {e}")
                finally:
                    if modal_opened:
                        try:
                            close_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Close' or @aria-label='Close dialog']")
                            close_btn.click()
                            WebDriverWait(self.driver, 5).until_not(
                                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                            )
                        except Exception as e:
                            logger.warning(f"Failed to close modal for post_id={post_id}: {e}")
                    if comments:
                        if len(comments) > 50:
                            comments = comments[:50]
                        self.save_comments_to_db(comments, post_id)
                # --- Always append post info to all_posts ONLY if modal was opened or comments were found ---
                if modal_opened or comments:
                    all_posts.append({
                        'post_id': post_id,
                        'meta': post_meta,
                        'url': post_url,
                        'comments_count': len(comments),
                        'modal_opened': modal_opened,
                        'comments': comments
                    })
            if len(all_posts) >= 10:
                break  # Stop scrolling if post limit reached
            if not new_post_detected:
                break  # If no new posts were detected in this scroll, stop scrolling
        # --- End of scroll loop ---
        if len(all_posts) < min_posts:
            logging.warning(f"Only {len(all_posts)} posts found on {page_url} after scrolling.")
        if not all_posts:
            logging.warning(f"No posts found on {page_url} within the last 5 days.")
        return all_posts

    def scrape_comments_mobile(self, post_url: str, max_comments=50):
        """
        Fallback: Scrape comments from m.facebook.com for a given post URL. Always save HTML/text if nothing is found.
        """
        import re
        from bs4 import BeautifulSoup
        import os, time, json
        # Convert to mobile URL
        mobile_url = post_url.replace('www.facebook.com', 'm.facebook.com').replace('facebook.com', 'm.facebook.com')
        self.driver.get(mobile_url)
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(2)
        comments = []
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Facebook mobile comments are in divs with id^="ufi_" or class="_2b06" or similar
            comment_blocks = soup.find_all('div', id=re.compile(r'^ufi_'))
            if not comment_blocks:
                comment_blocks = soup.find_all('div', class_='_2b06')
            for block in comment_blocks:
                author = block.find('h3')
                text = block.find('div', {'data-sigil': 'comment-body'})
                if not text:
                    text = block.find('span')
                comment = {
                    'author': author.text.strip() if author else None,
                    'text': text.text.strip() if text else block.text.strip(),
                }
                comments.append(comment)
                if len(comments) >= max_comments:
                    break
            if not comments:
                # Save mobile HTML and text for offline analysis
                debug_dir = os.path.join('data', 'mobile_debug')
                os.makedirs(debug_dir, exist_ok=True)
                fname = f"mobile_fallback_{int(time.time())}.html"
                with open(os.path.join(debug_dir, fname), 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                fname_txt = f"mobile_fallback_{int(time.time())}.txt"
                with open(os.path.join(debug_dir, fname_txt), 'w', encoding='utf-8') as f:
                    f.write(soup.get_text())
                # Return a fallback comment
                comments = [{
                    'author': None,
                    'text': 'NO_COMMENTS_FOUND_MOBILE',
                    'fallback_html_file': fname,
                    'fallback_text_file': fname_txt
                }]
        except Exception as e:
            logger.error(f"Mobile comment scrape failed: {e}")
            # Save mobile HTML and text for offline analysis
            debug_dir = os.path.join('data', 'mobile_debug')
            os.makedirs(debug_dir, exist_ok=True)
            fname = f"mobile_fallback_{int(time.time())}.html"
            with open(os.path.join(debug_dir, fname), 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            fname_txt = f"mobile_fallback_{int(time.time())}.txt"
            with open(os.path.join(debug_dir, fname_txt), 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            comments = [{
                'author': None,
                'text': f'ERROR_MOBILE_SCRAPE: {e}',
                'fallback_html_file': fname,
                'fallback_text_file': fname_txt
            }]
        return comments, None

    def scrape_comments_with_video_sidebar(self, post_url: str, max_comments=50):
        """
        Scrape up to 50 comments from a post, clicking the comments icon/button under the post (not the video), then slowly scrolling only the comments container/sidebar. Take a screenshot from inside the comment section/modal.
        """
        self.driver.get(post_url)
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        comments = []
        screenshot_path_from_comment = None
        try:
            # Explicitly find and click the comments icon/button under the post (not the video)
            post_container = None
            for sel in ['div[role="article"]', 'div[aria-label="Reel"]', 'div[aria-label="Video post"]']:
                try:
                    post_container = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if post_container:
                        break
                except Exception:
                    continue
            if post_container:
                comment_btn = None
                btn_selectors = [
                    ".//div[@aria-label='Comment']",
                    ".//span[contains(text(),'Comment') or contains(text(),'сэтгэгдэл')]/ancestor::div[@role='button']",
                    ".//div[@aria-label='Write a comment']",
                    ".//div[@aria-label='Write a comment…']",
                    ".//div[@aria-label='Write a comment...']",
                    ".//div[@aria-label='Leave a comment']",
                    ".//div[@role='button' and descendant::svg[@aria-label='Comment']]",
                    ".//span[contains(text(),'сэтгэгдэл')]/ancestor::div[@role='button']",
                ]
                for sel in btn_selectors:
                    btns = post_container.find_elements(By.XPATH, sel)
                    if btns:
                        comment_btn = btns[0]
                        break
                if comment_btn:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView();", comment_btn)
                        comment_btn.click()
                        time.sleep(0.5)
                    except Exception:
                        pass
            # Wait for comment section/modal to appear (try more selectors and longer)
            comments_container = None
            possible_selectors = [
                'div[aria-label="Comments"]',
                'div[aria-label="comments"]',
                'div[role="complementary"]',
                'div[role="region"]',
                'ul[role="list"]',
                'div[aria-label*="comment"]',
            ]
            for _ in range(10):
                for sel in possible_selectors:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for e in elems:
                        # Heuristic: must contain at least one comment-like div
                        if len(e.find_elements(By.XPATH, ".//div[@aria-label='Comment'] | .//div[@role='article']")) > 0:
                            comments_container = e
                            break
                    if comments_container:
                        break
                if comments_container:
                    break
                time.sleep(0.1)
            # Take screenshot from inside the comment section/modal
            try:
                if post_container:
                    screenshot_path_from_comment = f"screenshot_commentview_{int(time.time())}.png"
                    self.take_screenshot(post_container, screenshot_path_from_comment)
            except Exception:
                pass
            # Scroll and load more comments
            if comments_container:
                for _ in range(20):
                    self.driver.execute_script("arguments[0].scrollBy(0, 150);", comments_container)
                    time.sleep(0.1)
                    # Click 'View more comments' if present
                    try:
                        more_btns = self.driver.find_elements(By.XPATH, "//span[contains(text(),'View more comments') or contains(text(),'See more comments') or contains(text(),'More Comments')]")
                        for more_btn in more_btns:
                            self.driver.execute_script("arguments[0].scrollIntoView();", more_btn)
                            more_btn.click()
                            time.sleep(0.5)
                    except Exception:
                        pass
            # Find all comment elements (try multiple selectors)
            comment_elems = []
            comment_selectors = [
                "//div[@aria-label='Comment']",
                "//ul[@role='list']//div[@dir='auto']",
                "//div[contains(@aria-label, 'comment')]//div[@dir='auto']",
            ]
            for sel in comment_selectors:
                found = self.driver.find_elements(By.XPATH, sel)
                if found:
                    comment_elems.extend(found)
            if not comment_elems:
                logger.warning(f"No comments found for post: {post_url}")
            for elem in comment_elems:
                if len(comments) >= max_comments:
                    break
                try:
                    # Try to get author
                    try:
                        author = elem.find_element(By.XPATH, "./ancestor::div[@aria-label='Comment']//a[role='link']").text
                    except Exception:
                        author = None
                    # Try to get text
                    try:
                        text = elem.text
                    except Exception:
                        text = None
                    # Try to get date
                    try:
                        date_elem = elem.find_element(By.TAG_NAME, 'abbr')
                        date_str = date_elem.get_attribute('aria-label') or date_elem.text
                        from dateparser import parse
                        comment_date = parse(date_str, languages=['en'])
                    except Exception:
                        comment_date = None
                    comments.append({
                        'author': author,
                        'text': text,
                        'date': comment_date.isoformat() if comment_date else None
                    })
                except Exception:
                    continue
        except Exception as e:
            logging.warning(f"Failed to scrape comments from {post_url}: {e}")
        return comments, screenshot_path_from_comment

    def expand_and_extract_comments(self, post_url, post_id, base_dir, max_comments=50):
        """
        Robustly expand and extract comments from a Facebook post. Always save results or fallback HTML/text.
        """
        import re, time, os, json
        from datetime import datetime
        self.driver.get(post_url)
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(0.5)
        debug_dir = os.path.join(base_dir, 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        # Expand all comments and replies
        total_clicks = 0
        for attempt in range(10):
            if total_clicks > 200:
                break
            current_clicks = 0
            view_more_selectors = [
                "//span[contains(text(), 'View more comments')]/ancestor::div[@role='button']",
                "//span[contains(text(), 'View previous comments')]/ancestor::div[@role='button']",
                "//div[@role='button' and contains(., 'View more comments')]",
                "//div[@role='button' and contains(., 'View previous comments')]",
                "//div[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]",
                "//span[contains(text(), 'View') and contains(text(), 'comment')]/ancestor::*[1]",
                "//div[contains(@class, 'UFIPagerLink')]",
                "//a[contains(@class, 'UFIPagerLink')]",
                "//a[contains(text(), 'View more comments') or contains(text(), 'View previous comments')]"
            ]
            for selector in view_more_selectors:
                more_buttons = self.driver.find_elements(By.XPATH, selector)
                for button in more_buttons[:5]:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].click();", button)
                        current_clicks += 1
                        total_clicks += 1
                        time.sleep(0.2)
                        if total_clicks > 200:
                            break
                    except:
                        pass
                if total_clicks > 200:
                    break
            reply_selectors = [
                "//span[contains(text(), 'View') and contains(text(), 'repl')]/ancestor::div[@role='button']",
                "//div[@role='button' and contains(., 'View') and contains(., 'repl')]",
                "//a[contains(text(), 'View') and contains(text(), 'repl')]",
                "//span[contains(text(), 'Reply') or contains(text(), 'Replies')]/ancestor::div[@role='button']",
                "//div[contains(@class, 'UFIReplyList')]//a[contains(text(), 'View')]"
            ]
            for selector in reply_selectors:
                reply_buttons = self.driver.find_elements(By.XPATH, selector)
                for button in reply_buttons[:5]:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].click();", button)
                        current_clicks += 1
                        total_clicks += 1
                        time.sleep(0.2)
                        if total_clicks > 200:
                            break
                    except:
                        pass
                if total_clicks > 200:
                    break
            if current_clicks == 0 and attempt >= 2:
                break
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.1)
        # Extract comments
        comment_selectors = [
            "//div[@aria-label='Comment' or contains(@class, 'UFIComment')]",
            "//div[contains(@class, 'comments-comment-item')]",
            "//div[contains(@data-testid, 'UFI2Comment')]",
            "//div[@data-testid='comment']",
            "//div[@role='article' and contains(@class, 'comment')]",
            "//div[contains(@class, 'commentable_item')]"
        ]
        comment_elements = []
        for selector in comment_selectors:
            elements = self.driver.find_elements(By.XPATH, selector)
            if elements:
                comment_elements = elements
                break
        comments = []
        for comment in comment_elements:
            try:
                author = "Unknown"
                author_selectors = [
                    ".//a[contains(@class, 'UFIComment') or @role='link' or contains(@href, 'facebook.com')]",
                    ".//span[contains(@class, 'author') or contains(@class, 'user')]",
                    ".//h3[contains(@class, 'actor')]",
                    ".//a[contains(@class, 'actor')]",
                    ".//a[@data-hovercard]",
                    ".//strong"
                ]
                for selector in author_selectors:
                    author_elements = comment.find_elements(By.XPATH, selector)
                    if author_elements and author_elements[0].text:
                        author = author_elements[0].text
                        break
                text = ""
                text_selectors = [
                    ".//div[contains(@class, 'UFICommentBody') or @data-ad-comet-preview='message']",
                    ".//div[@data-testid='comment-content']",
                    ".//div[contains(@class, 'comment-content')]",
                    ".//div[contains(@class, 'commentText')]",
                    ".//span[@dir='auto']"
                ]
                for selector in text_selectors:
                    text_elements = comment.find_elements(By.XPATH, selector)
                    if text_elements and text_elements[0].text:
                        text = text_elements[0].text
                        break
                if not text:
                    continue
                likes = 0
                likes_elements = comment.find_elements(By.XPATH, ".//span[contains(@class, 'UFICommentLikeButton') or contains(text(), 'Like')]")
                for likes_element in likes_elements:
                    likes_text = likes_element.get_attribute('aria-label') or likes_element.text
                    if likes_text and 'like' in likes_text.lower():
                        likes_match = re.search(r'(\d+)', likes_text)
                        if likes_match:
                            likes = int(likes_match.group(1))
                comments.append({
                    'post_id': post_id,
                    'author': author,
                    'text': text,
                    'likes': likes,
                    'comment_time': datetime.now().isoformat(),
                    'extracted_at': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Error extracting a comment: {e}")
        # Save comments or fallback (now inside the loop, so elem is always in scope)
        comments_dir = os.path.join(base_dir, 'comments')
        os.makedirs(comments_dir, exist_ok=True)
        if comments:
            comments_file = os.path.join(comments_dir, f"{post_id}_comments.json")
            with open(comments_file, 'w', encoding='utf-8') as cf:
                json.dump(comments, cf, ensure_ascii=False, indent=2)
        else:
            # Save fallback HTML and text
            html_file = os.path.join(debug_dir, f"{post_id}_comments_fallback.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            txt_file = os.path.join(debug_dir, f"{post_id}_comments_fallback.txt")
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.find_element(By.TAG_NAME, 'body').text)
        return comments

    def save_comments_to_db(self, comments: list, post_id: str) -> None:
        """
        Save a list of comment dicts to the database for a given post_id.
        Skips empty comments and avoids duplicates. Logs all actions.
        """
        if not comments:
            logger.info(f"No comments to save for post_id={post_id}")
            return
        session = self.db.Session()
        saved, skipped_empty, skipped_dup, failed = 0, 0, 0, 0
        try:
            for comment in comments:
                text = comment.get('text', '').strip()
                if not text:
                    logger.warning(f"Skipping empty comment for post_id={post_id}")
                    skipped_empty += 1
                    continue
                # Check for duplicate (same post_id and comment_text)
                exists = session.query(PostComment).filter_by(post_id=post_id, comment_text=text).first()
                if exists:
                    logger.info(f"Duplicate comment skipped for post_id={post_id}")
                    skipped_dup += 1
                    continue
                try:
                    db_comment = PostComment(
                        post_id=post_id,
                        comment_text=text,
                        timestamp=datetime.now()
                    )
                    session.add(db_comment)
                    saved += 1
                except Exception as e:
                    logger.error(f"Failed to add comment to session for post_id={post_id}: {e}")
                    failed += 1
            session.commit()
            logger.info(f"Comments saved for post_id={post_id}: {saved} saved, {skipped_empty} empty, {skipped_dup} duplicates, {failed} failed.")
        except Exception as e:
            logger.error(f"Failed to commit comments to DB for post_id={post_id}: {e}")
            session.rollback()
        finally:
            session.close()

    def extract_in_feed_comments(self, elem, post_id, base_dir):
        """
        Extract comments directly visible in the post feed (not in modal).
        This is a stub implementation. Replace with actual extraction logic as needed.
        """
        comments = []  # Replace with real extraction logic
        # ...real extraction logic should limit to 50 comments...
        if len(comments) > 50:
            comments = comments[:50]
        self.save_comments_to_db(comments, post_id)
        return comments

    def extract_modal_comments(self, elem, post_id, base_dir):
        """
        Extract comments from the modal dialog after clicking the post.
        Uses robust selectors and BeautifulSoup to extract all visible comment texts.
        Logs every comment found. Only saves non-empty, deduplicated comments.
        """
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup
        comments = []
        seen_comments = set()
        max_comments = 50
        modal_closed = False
        try:
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' or @aria-modal='true']"))
            )
            scrollable = None
            for candidate in modal.find_elements(By.XPATH, ".//*"):
                try:
                    if candidate.value_of_css_property("overflow-y") in ("auto", "scroll") and candidate.size["height"] > 200:
                        scrollable = candidate
                        break
                except Exception:
                    continue
            if not scrollable:
                scrollable = modal
            last_height = 0
            scroll_attempts = 0
            last_comment_count = 0
            while len(comments) < max_comments and scroll_attempts < 30:
                self.driver.execute_script("arguments[0].scrollBy(0, 200);", scrollable)
                time.sleep(0.5)
                if "Сэтгэгдэл хараахан алга" in modal.text:
                    logger.info(f"No comments message detected in modal for post_id={post_id}, stopping.")
                    break
                # Use BeautifulSoup to extract all visible comment texts from modal HTML
                soup = BeautifulSoup(modal.get_attribute('innerHTML'), 'html.parser')
                # Facebook comments are often in <div> or <span> with role="article" or aria-label="Comment"
                for cdiv in soup.find_all(['div', 'article'], attrs={'aria-label': 'Comment'}):
                    text = cdiv.get_text(separator=' ', strip=True)
                    if text and text not in seen_comments:
                        logger.info(f"[Comment] {text}")
                        comments.append(text)
                        seen_comments.add(text)
                        if len(comments) >= max_comments:
                            break
                # Fallback: try role="article" without aria-label
                for cdiv in soup.find_all(['div', 'article'], attrs={'role': 'article'}):
                    text = cdiv.get_text(separator=' ', strip=True)
                    if text and text not in seen_comments:
                        logger.info(f"[Comment] {text}")
                        comments.append(text)
                        seen_comments.add(text)
                        if len(comments) >= max_comments:
                            break
                # If no new comments were found after scroll, break
                if len(comments) == last_comment_count:
                    logger.info(f"No new comments found after scroll for post_id={post_id}, stopping.")
                    break
                last_comment_count = len(comments)
                # Try clicking "View more comments" if present
                more_btns = scrollable.find_elements(By.XPATH, ".//div[@role='button' and (contains(text(),'View more comments') or contains(text(),'See more comments'))]")
                if not more_btns:
                    logger.info(f"No more 'View more comments' buttons for post_id={post_id}, stopping.")
                    break
                for btn in more_btns:
                    try:
                        btn.click()
                        time.sleep(0.5)
                    except Exception:
                        continue
                new_height = self.driver.execute_script("return arguments[0].scrollTop;", scrollable)
                if new_height == last_height:
                    logger.info(f"Scroll position did not change for post_id={post_id}, assuming bottom reached.")
                    break
                last_height = new_height
            if len(comments) > max_comments:
                comments = comments[:max_comments]
            logger.info(f"Extracted {len(comments)} comments from modal for post_id={post_id}")
        except Exception as e:
            logger.error(f"Error extracting comments from modal for post_id={post_id}: {e}")
            if base_dir:
                try:
                    with open(os.path.join(base_dir, f"modal_debug_{post_id}.html"), "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                except Exception:
                    pass
        finally:
            try:
                self.close_modal()
                modal_closed = True
            except Exception as e:
                logger.warning(f"Failed to close modal for post_id={post_id} in extract_modal_comments: {e}")
        self.save_comments_to_db(comments, post_id)
        return comments

    def close_modal(self):
        """
        Attempt to close the Facebook post modal by sending ESC or clicking the close button.
        """
        try:
            # Try ESC key
            from selenium.webdriver.common.keys import Keys
            body = self.driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            # Check if modal is closed
            modals = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"], div[aria-modal="true"]')
            if not modals:
                return True
            # Try clicking close button
            for sel in [
                'div[aria-label="Close"]',
                'div[aria-label="close"]',
                'div[role="button"][tabindex="0"]',
                'svg[aria-label="Close"]',
            ]:
                try:
                    close_btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for btn in close_btns:
                        btn.click()
                        time.sleep(0.5)
                        modals = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"], div[aria-modal="true"]')
                        if not modals:
                            return True
                except Exception:
                    continue
            logger.warning("Modal may not have closed properly.")
        except Exception as e:
            logger.error(f"Error closing modal: {e}")
        return False

    def extract_comments_modal_first(self, post_elem, post_id, base_dir):
        """
        Always attempt to open the comment modal for a post, extract up to 50 comments if present, then close modal.
        Tries multiple strategies for all post types (text, photo, video):
        - Timestamp link
        - Comment button
        - Post container
        - Video overlay/play button (for video posts)
        """
        comments = []
        modal_opened = False
        try:
            # Try to open modal by clicking timestamp link
            try:
                timestamp = post_elem.find_element(By.XPATH, ".//a[contains(@href, '/posts/') or contains(@href, '/videos/')]")
                timestamp.click()
                modal_opened = True
                logger.info(f"Opened modal via timestamp for post_id={post_id}")
            except Exception:
                # Try to open modal by clicking comment button
                try:
                    comment_btn = post_elem.find_element(By.XPATH, ".//div[@aria-label='Leave a comment' or @aria-label='Comment']")
                    comment_btn.click()
                    modal_opened = True
                    logger.info(f"Opened modal via comment button for post_id={post_id}")
                except Exception:
                    # Try to open modal by clicking post container
                    try:
                        post_elem.click()
                        modal_opened = True
                        logger.info(f"Opened modal via post container for post_id={post_id}")
                    except Exception:
                        # Try to open modal by clicking video overlay/play button
                        try:
                            video_btn = post_elem.find_element(By.XPATH, ".//div[contains(@aria-label, 'Play video') or contains(@aria-label, 'Watch') or contains(@role, 'button')]")
                            video_btn.click()
                            modal_opened = True
                            logger.info(f"Opened modal via video overlay for post_id={post_id}")
                        except Exception:
                            logger.warning(f"Could not open modal for post_id={post_id} (all strategies failed)")
            if modal_opened:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                )
                # Extract comments from modal
                comments = self.extract_modal_comments(post_elem, post_id, base_dir)
                if not comments:
                    logger.info(f"No comments found in modal for post_id={post_id}")
        except Exception as e:
            logger.warning(f"Modal could not be opened or no comments for post_id={post_id}: {e}")
        finally:
            if modal_opened:
                closed = False
                # Try to close the modal robustly
                try:
                    close_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Close' or @aria-label='Close dialog']")
                    close_btn.click()
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Comments' or @role='dialog']"))
                    )
                    closed = True
                except Exception:
                    pass
                if not closed:
                    try:
                        self.close_modal()
                    except Exception as e:
                        logger.warning(f"Failed to close modal for post_id={post_id} (fallback): {e}")
            # Save comments if any
            if comments:
                if len(comments) > 50:
                    comments = comments[:50]
                self.save_comments_to_db(comments, post_id)
        return comments

    def scrape_posts_on_page(self, page_url, max_posts=10, base_dir=None):
        """
        Scrape up to max_posts from a single Facebook page, always attempting modal extraction for each post.
        Refetches post elements by index after each modal close to avoid stale element issues.
        """
        self.driver.get(page_url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]'))
        )
        scraped = 0
        post_idx = 0
        while scraped < max_posts:
            try:
                posts = self.driver.find_elements(By.XPATH, "//div[@role='article']")
                if post_idx >= len(posts):
                    break
                post_elem = posts[post_idx]
                post_id = self.extract_post_id(post_elem)
                if not post_id:
                    post_idx += 1
                    continue
                self.extract_comments_modal_first(post_elem, post_id, base_dir)
                scraped += 1
                post_idx += 1
            except Exception as e:
                logger.error(f"Error scraping post: {e}")
                try:
                    self.close_modal()
                except Exception:
                    pass
                post_idx += 1
                continue
        logger.info(f"Scraped {scraped} posts from {page_url}")
        return scraped

    def extract_post_id(self, post_elem):
        """Extract a unique post ID from the post element (stub, replace with real logic)."""
        try:
            # Try to extract post ID from data-ft or other attribute
            return post_elem.get_attribute('data-ft') or post_elem.get_attribute('id')
        except Exception:
            return None
