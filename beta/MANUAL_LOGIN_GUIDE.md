# Manual Login Guide for Facebook Scraper

This guide provides step-by-step instructions for running the Facebook scraper with manual login.

## Prerequisites

Before starting, ensure you have:

1. Python 3.8 or higher installed
2. Firefox browser installed
3. Stable internet connection

## Setup Steps

### 1. Installation

If you haven't already, set up the project:

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Pages List

Edit the `pages.txt` file to include the Facebook pages you want to scrape, one per line:

```
eaglenewssocial
gogo.mn
zarigmn
```

### 3. Run the Scraper

#### Using the Batch File (Windows)

The easiest way is to use the provided batch file:

```bash
run_scraper.bat
```

This will:
- Set up the virtual environment
- Install dependencies
- Initialize the project directories and database
- Launch the scraper with manual login

#### Using Command Line

Alternatively, you can run directly from the command line:

```bash
# Activate virtual environment
.venv\Scripts\activate  # On Windows

# Run the scraper
python scraper_cli.py --manual
```

## Manual Login Process

1. When you run the scraper, a Firefox browser window will open to Facebook's login page.

2. **Important**: Log in with your Facebook credentials in this browser window.

3. After successful login, you have two options:
   - Return to the terminal window and type `done` and press Enter
   - Wait for automatic login detection (up to 5 minutes)

4. The scraper will then automatically:
   - Visit each page from your pages.txt
   - Scrape posts, images, and comments
   - Save everything to the SQLite database
   - Download images to the images/ directory

5. The terminal will show progress as the scraper runs.

## Checking Results

After scraping completes, you can:

1. Check the database contents:
   ```bash
   python check_db.py
   ```

2. View comments:
   ```bash
   python view_comments.py
   ```

3. Export comments to text:
   ```bash
   python export_comments_to_text.py
   ```

4. Browse the `images` folder to see downloaded images organized by page name.

## Troubleshooting

### Browser Closes Immediately

- The scraper is configured to use a visible browser for manual login
- If the browser closes immediately, check error logs in the `logs/` directory

### Login Problems

- Make sure your Facebook account is active and not locked
- If Facebook shows security challenges or captchas, solve them manually during the login process

### Scraping Issues

- If no data is scraped, check if the page names in `pages.txt` are correct
- Verify the pages are public and accessible
- Check the `debug/` folder for screenshots that might show what went wrong

## Notes

- The manual login process helps avoid Facebook's automated scraping detection
- Browser cookies are not saved between sessions for security reasons
- You will need to log in each time you run the scraper
