import unittest
from selenium import webdriver
from scraper.browser_manager import BrowserManager

class TestBrowserManager(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.manager = BrowserManager(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_page_load(self):
        self.driver.get('https://facebook.com')
        result = self.manager.verify_page_load()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
