# Facebook Scraper Usage Guide

This comprehensive guide explains how to run the Facebook Scraper with all available options and features.

## Features

- **Post scraping** with page name, text, time, and engagement metrics
- **PostgreSQL database** storage for reliable data management
- **Automatic image download** from posts
- **Screenshot capture** of each post
- **Complete comment scraping** (up to 50 per post, robust modal handling)
- **Manual login and cookie support** for reliable access
- **Post limit options** to control scraping depth
- **Robust error handling and deduplication**
- **Supports video, photo, and text posts**

## Getting Started

See the README for installation and setup instructions.

## Running the Scraper

Run the main script:

```bash
python run_scraper.py
```

- On first run, you may be prompted to log in manually in the browser window. After login, scraping will continue automatically.
- On subsequent runs, cookies will be loaded if available.

## Options
- Edit `pages.txt` to specify which Facebook pages to scrape.
- Configure database and credentials in `.env` or `db/config.py`.
- Edit `fb_credentials.py` to update your Facebook cookies or credentials.
- Adjust post/comment limits in the code if needed.

## Output
- Posts, images, and comments are saved in the `data/` directory and the database.
- Each post includes metadata, up to 50 comments, and modal open status.
- Debug HTML is saved for failed modal attempts.

## Troubleshooting
- Ensure you are logged in to Facebook (manual login may be required on first run).
- Check logs in the `logs/` directory for errors.
- If posts are not detected, check for Facebook UI changes and update selectors in `post_scraper.py`.
- For video posts, the scraper tries multiple strategies to open the comment modal.

## Advanced
- The scraper now only counts posts where a modal was opened or comments were found.
- Robust fallback strategies are implemented for modal opening and comment extraction.
- For further customization, see `scraper/post_scraper.py` and `content_manager/`.
