# Facebook Scraper Setup Guide

This guide provides instructions for setting up the Facebook Scraper project with PostgreSQL database integration.

## Features

- **PostgreSQL database integration** for better performance and features
- **Automatic screenshot capture** of posts
- **Local storage** of all post images in the 'images' folder
- **Full comment scraping** (up to 50 per post, robust modal handling)
- **Manual login and cookie support** for reliable access
- **Option to limit posts** scraped per page
- **Debug HTML for failed modal attempts**

## Project Structure

- `db/` - Database models and config
- `scraper/` - Browser and scraping logic
- `content_manager/` - Content saving and export
- `automation/` - Scraper automation
- `setup/` - Initialization scripts
- `tests/` - Test suite

## Setup Steps

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure your `.env` file with database credentials (see `.env` example).
3. Initialize the database:
   ```bash
   python setup/init_database.py
   ```
4. Edit `pages.txt` to specify Facebook pages to scrape.
5. (Optional) Edit `fb_credentials.py` to update your Facebook cookies or credentials.
6. Run the scraper:
   ```bash
   python run_scraper.py
   ```
   - On first run, you may be prompted to log in manually in the browser window. After login, scraping will continue automatically.
   - On subsequent runs, cookies will be loaded if available.

## Notes
- Make sure PostgreSQL is running and accessible.
- For manual login, credentials are in `fb_credentials.py`.
- Logs are saved in the `logs/` directory.
- If posts are not detected, check for Facebook UI changes and update selectors in `post_scraper.py`.
- Debug HTML is saved for failed modal attempts.
