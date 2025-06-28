# Smart Facebook Scraper

This implementation upgrades the Facebook scraper with intelligent comment handling capabilities.

## Smart Scraper Features

- **Automatic Post Detection**: Identifies posts on Facebook pages
- **Screenshot Capture**: Takes screenshots of posts showing content, author, likes, and timestamp
- **Smart Comment Detection**: Detects if a post has comments before attempting extraction
- **Intelligent Comment Handling**:
  - For posts without comments: Takes a screenshot and saves metadata only
  - For posts with comments: Navigates to the post page and extracts all comments
  - Includes automatic pagination to get all comments and replies
  - Limits to 50 comments if a post has more than 100 comments
- **Image Extraction**: Downloads all post images
- **Database Storage**: Saves all data in PostgreSQL database
- **Manual Login**: Supports manual login for improved reliability

## How It Works

1. The main file `facebook_scraper_all.py` is a thin wrapper that imports the `SmartFacebookScraper` class from `facebook_scraper_smart.py`
2. When `facebook_scraper_all.py` is executed, it creates a `SmartFacebookScraper` instance and delegates all scraping operations to it
3. This approach ensures minimal code duplication while providing the enhanced smart features

## Usage

```bash
# Basic usage
python facebook_scraper_all.py --pages-file pages.txt

# With custom options
python facebook_scraper_all.py --pages-file pages.txt --max-posts 20 --max-comments 100
```

Or use the included batch file:

```bash
run_smart_scraper.bat
```

## Command Line Options

- `--pages`: List of Facebook page names to scrape
- `--pages-file`: File containing list of Facebook page names (default: pages.txt)
- `--max-posts`: Maximum number of posts to scrape per page (0 = all)
- `--headless`: Run browser in headless mode (no UI)
- `--no-images`: Do not download images
- `--no-comments`: Do not extract comments
- `--no-screenshots`: Do not take screenshots of posts
- `--wait-time`: Maximum time to wait for manual login in seconds (default: 300)
- `--max-comments`: Maximum number of comments to extract per post (0 = all, default: 50)
