# Modular Facebook Scraper - Scraper0.1

A modular Facebook scraper with automated scheduling, content management, and smart scraping features.

## Features

- **Smart Scraping**
  - Automatic post detection and scraping (robust modal handling, up to 10 posts per page)
  - Reply and comment extraction (up to 50 comments per post, with deduplication)
  - Handles video, photo, and text posts
- **Content Management**
  - Organized storage of posts, comments, and images
  - PostgreSQL database integration
  - Debug HTML for failed modal attempts
- **Automation**
  - Scheduled scraping
  - Headless mode support
  - Manual login and cookie support

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure PostgreSQL database:

```bash
python setup/init_database.py
```

3. Set up your `.env` file (see `.env` example).

4. Run the scraper:

```bash
python run_scraper.py
```

See `USAGE_GUIDE.md` and `SETUP_GUIDE.md` for more details.
