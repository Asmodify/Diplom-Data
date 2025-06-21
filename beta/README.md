# Facebook Scraper (Production)

A powerful tool for scraping real posts, images, comments, and engagement metrics from Facebook pages.

## Features

✅ Scrapes real posts from Facebook pages  
✅ Downloads post images automatically  
✅ Captures post comments with author and likes  
✅ Records engagement metrics (likes, shares)  
✅ Stores data in a SQLite database  
✅ Clean command-line interface  
✅ Manual login support for reliable access  

## Directory Structure

```
facebook-scraper/
├── db/                      # Database package
│   ├── __init__.py
│   ├── config.py            # Database configuration
│   ├── database.py          # Database manager
│   └── models.py            # SQLAlchemy models
├── images/                  # Downloaded images
│   └── [page_name]/         # Organized by page
├── logs/                    # Log files
├── debug/                   # Debug screenshots and HTML
├── check_db.py              # Database inspection tool
├── export_comments_to_text.py # Export comments utility
├── export_comments_to_text.bat # Batch file for export
├── facebook_scraper.py      # Main scraper with manual login
├── facebook_scraper.db      # SQLite database
├── fb_credentials.py        # Facebook authentication cookies
├── init_project.py          # Project initialization
├── pages.txt                # List of pages to scrape
├── requirements.txt         # Python dependencies
├── run_scraper.bat          # Windows batch file for manual login
├── scraper_cli.py           # Command-line interface
├── verify_access.py         # Facebook access validation
├── view_comments.bat        # Batch file for viewing comments
└── view_comments.py         # View scraped comments
```

## Setup

### Prerequisites

- Python 3.8 or higher
- Firefox browser
- Selenium WebDriver for Firefox (geckodriver)

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/facebook-scraper.git
cd facebook-scraper
```

2. **Create a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Initialize the project:**

```bash
python init_project.py
```

## Running the Scraper

The project now uses manual login mode for increased reliability:

1. **Edit page list:**

Add Facebook page usernames to `pages.txt`, one per line.

2. **Run the scraper:**

```bash
python scraper_cli.py --manual
```

Or use the batch file:

```bash
run_scraper.bat
```

3. **Login manually:**

When prompted, log into Facebook in the browser window that opens.
Type 'done' in the terminal when you've successfully logged in.
The scraper will then automatically collect posts, images, and comments.

## Exporting Data

You can check the database contents:

```bash
python check_db.py
```

Export comments to a text file:

```bash
python export_comments_to_text.py
```

Or use the batch file:

```bash
export_comments_to_text.bat
```

## Usage

### Quick Start (Windows)

Run the batch file:

```bash
run_scraper.bat
```

### Using the Command Line

Run the scraper with manual login:

```bash
python scraper_cli.py --manual
```

Specify pages to scrape:

```bash
python scraper_cli.py --manual --pages eaglenewssocial gogo.mn
```

Customize scraping parameters:

```bash
python scraper_cli.py --manual --max-posts 10
```

Verify Facebook access without scraping:

```bash
python verify_access.py
```

### Pages to Scrape

Add Facebook page names to `pages.txt`, one per line:

```
eaglenewssocial
zarigmn
gogo.mn
```

## Database Schema

The scraper stores data in three tables in SQLite:

### facebook_posts

- `id`: Primary key
- `page_name`: Name of the Facebook page
- `post_id`: Unique ID of the post
- `post_url`: URL to the post
- `post_text`: Text content of the post
- `post_time`: When the post was published
- `author`: Author of the post
- `likes`: Number of likes
- `shares`: Number of shares
- `extracted_at`: When the post was scraped

### post_images

- `id`: Primary key
- `post_id`: Foreign key to facebook_posts
- `original_url`: Original image URL
- `local_path`: Local file path
- `filename`: Image filename
- `downloaded_at`: When the image was downloaded

### post_comments

- `id`: Primary key
- `post_id`: Foreign key to facebook_posts
- `author`: Comment author
- `text`: Comment text
- `comment_time`: When the comment was posted
- `likes`: Number of likes on the comment
- `extracted_at`: When the comment was scraped

## Cleaning the Project

To remove any test files and mock data, run:

```bash
python clean_project.py
```

This utility:
- Removes test files from the workspace
- Deletes mock data from the database
- Cleans up mock images
- Ensures only real scraped data remains

## Troubleshooting

### Facebook Login Issues
- The scraper uses manual login - follow the prompts in the terminal
- Make sure you can log in to Facebook in Firefox
- If login fails, check that Facebook isn't showing captchas or security challenges

### Scraper Issues
- Look at log files in `logs/` directory
- Verify HTML structure in `debug/` if elements are not found
- Check for changes in Facebook's page structure

## Disclaimer

This tool is for educational purposes only. Scraping Facebook may violate their Terms of Service. Use responsibly and at your own risk.


## Manual Login Instructions

# Facebook Scraper with Manual Login

This project is a Facebook scraper that collects real posts, images, and comments from Facebook pages. It uses manual login to avoid authentication issues.

## Features

- **Real Facebook Data**: Scrapes actual Facebook posts, images, and comments (no mock data)
- **Manual Login**: Opens a browser window for you to manually log in to Facebook
- **Database Storage**: Saves all scraped data to an SQLite database
- **Image Downloads**: Automatically downloads and saves post images
- **Selective Scraping**: Scrape specific pages with customizable post limits

## Setup

1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Ensure you have Firefox installed (the scraper uses Firefox with Selenium)

## Usage

### Easy Method (Batch File)

Simply run the batch file:
```
run_manual_scraper.bat
```

This will:
1. Create/activate a virtual environment
2. Install dependencies
3. Initialize the database
4. Open Firefox for you to log in manually
5. Scrape the pages listed in `test_pages.txt`
6. Show the scraped data summary

### Python Command

Run the scraper directly:
```
python facebook_scraper_manual.py --pages-file pages.txt --max-posts 5
```

### Command Line Arguments

- `--pages [page1 page2 ...]`: List of Facebook page names to scrape
- `--pages-file FILENAME`: Path to file containing page names (one per line)
- `--max-posts N`: Maximum number of posts to scrape per page (default: 5)
- `--headless`: Run in headless mode (NOT recommended for manual login)

## Login Process

When you run the scraper:
1. A Firefox browser window will open to Facebook's login page
2. You have 120 seconds to manually log in with your credentials
3. After successful login, the scraper will automatically continue
4. The browser will navigate to each page and collect data

## Data Storage

- **Database**: All data is stored in an SQLite database (`facebook_data.db`)
- **Images**: Downloaded to `images/<page_name>/` directories
- **Debug Info**: Screenshots and HTML saved to `debug/` directory

## Checking Results

Run the database check script to see what was scraped:
```
python check_db.py
```

This will show:
- Recent posts with text, URLs, and engagement metrics
- Downloaded images with file locations
- Comments with author and text information
- Overall database statistics

## Troubleshooting

- **Browser Issues**: If Firefox doesn't work, ensure it's updated to the latest version
- **Login Problems**: The manual login gives you direct control - make sure to complete it within the time limit
- **Missing Data**: Some Facebook pages have different layouts; the scraper attempts to handle various formats

## Notes

- Be respectful of Facebook's terms of service
- Avoid excessive scraping that might trigger rate limits
- The scraper includes appropriate delays between actions to avoid detection
