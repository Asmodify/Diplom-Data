import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from automation.auto_scraper import AutoScraper
from fb_credentials import cookies
import time
from selenium.common.exceptions import WebDriverException

logging.basicConfig(level=logging.INFO)

def get_facebook_urls(pages_file="pages.txt"):
    base_url = "https://facebook.com/"
    with open(pages_file, "r", encoding="utf-8") as f:
        return [base_url + line.strip() for line in f if line.strip()]

def load_cookies(driver, cookies):
    driver.get("https://facebook.com/")
    for name, value in cookies.items():
        driver.add_cookie({"name": name, "value": value})
    driver.refresh()
    logging.info("Cookies loaded and browser refreshed.")

def manual_login_pause(driver, wait_time=60):
    print(f"\nPlease log in to Facebook in the opened browser window. Waiting {wait_time} seconds...")
    driver.get("https://facebook.com/")
    time.sleep(wait_time)
    print("Continuing with scraping...")

def main():
    options = Options()
    # Uncomment below to run headless
    # options.headless = True
    driver = webdriver.Firefox(options=options)
    # Try loading cookies, fallback to manual login
    try:
        load_cookies(driver, cookies)
        driver.get("https://facebook.com/")
        time.sleep(1)
        if "login" in driver.current_url:
            manual_login_pause(driver)
    except Exception as e:
        logging.warning(f"Cookie load failed: {e}. Falling back to manual login.")
        manual_login_pause(driver)
    scraper = AutoScraper(driver, content_dir="data")
    page_urls = get_facebook_urls()
    for page_url in page_urls:
        try:
            scraper.scrape_page(page_url)
        except WebDriverException as e:
            logging.error(f"WebDriverException in main loop: {e}. Restarting browser and continuing.")
            # Restart driver and scraper
            driver.quit()
            driver = webdriver.Firefox(options=options)
            scraper = AutoScraper(driver, content_dir="data")
            try:
                load_cookies(driver, cookies)
                driver.get("https://facebook.com/")
                time.sleep(1)
                if "login" in driver.current_url:
                    manual_login_pause(driver)
            except Exception as e2:
                logging.warning(f"Cookie load failed after restart: {e2}. Falling back to manual login.")
                manual_login_pause(driver)
            scraper.scrape_page(page_url)
    driver.quit()

if __name__ == "__main__":
    main()
