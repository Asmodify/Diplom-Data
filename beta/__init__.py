"""
Root package initialization

Note: Scraper and automation modules are only imported when needed.
This avoids import errors when Selenium is not available (e.g., in cloud deployments).
"""
# from .scraper import BrowserManager, PostScraper
# from .automation import AutoScraper
# from .content_manager import ContentSaver

# These can be imported explicitly when needed:
# from beta.scraper import BrowserManager, PostScraper
# from beta.automation import AutoScraper
# from beta.content_manager import ContentSaver
