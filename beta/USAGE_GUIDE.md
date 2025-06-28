# Facebook Scraper Usage Guide

This comprehensive guide explains how to run the Facebook Scraper with all available options and features.

## Features

- **Post scraping** with page name, text, time, and engagement metrics
- **PostgreSQL database** storage for reliable data management
- **Automatic image download** from posts
- **Screenshot capture** of each post
- **Complete comment scraping** with no limit
- **Manual login support** for reliable access
- **Post limit options** to control scraping depth

## Getting Started

Before running the scraper, make sure you've completed the setup as described in the [Setup Guide](SETUP_GUIDE.md).

## List of Facebook Pages

Create or edit `pages.txt` with the Facebook pages you want to scrape, one per line:

```
Nike
Apple
Microsoft
```

You can also add comments to this file using `#`:

```
# Tech companies
Apple
Microsoft
# Sports brands
Nike
Adidas
```

## Running the Scraper

### Standard Scraping

### Basic Usage

To run the scraper with default settings:

```bash
python facebook_scraper_all.py
```

This will:
1. Launch the Firefox browser
2. Prompt you to manually log in to Facebook
3. Scrape the pages listed in `pages.txt`
4. Save posts, images, and comments to the PostgreSQL database
5. Download images to the `images/` folder
6. Take screenshots of posts

### Command Line Options

The scraper supports several command-line options:

```bash
python facebook_scraper_all.py [options]
```

| Option | Description |
|--------|-------------|
| `--pages PAGE1 PAGE2` | List of Facebook page names to scrape |
| `--pages-file FILE` | File containing Facebook page names (one per line) |
| `--max-posts N` | Maximum number of posts to scrape per page (0 = all) |
| `--headless` | Run browser in headless mode (no UI) |
| `--no-images` | Do not download images |
| `--no-comments` | Do not extract comments |
| `--no-screenshots` | Do not take screenshots of posts |
| `--wait-time N` | Maximum time to wait for manual login (seconds) |

### Examples

**Scrape specific pages:**
```bash
python facebook_scraper_all.py --pages Nike Adidas
```

**Scrape with post limit:**
```bash
python facebook_scraper_all.py --max-posts 5
```

**Scrape without images:**
```bash
python facebook_scraper_all.py --no-images
```

**Scrape without comments:**
```bash
python facebook_scraper_all.py --no-comments
```

**Scrape in headless mode:**
```bash
python facebook_scraper_all.py --headless
```

### Enhanced Comment Scraping

For pages with comments that weren't properly scraped, you can use the dedicated comment scraper:

```bash
python scrape_comments.py --max-posts 5
```

This specialized script:

1. Focuses solely on extracting comments from previously scraped posts
2. Uses advanced techniques to access and expand comment sections
3. Handles Facebook's layout more effectively for comment extraction
4. Matches the number of comments shown in the post count
5. Takes debug screenshots of the comment section for troubleshooting

Options:

| Option | Description |
|--------|-------------|
| `--max-posts N` | Maximum number of posts to process for comments (default: 5) |
| `--headless` | Run browser in headless mode (no UI) |

If a post shows comments but none were scraped, running this tool will:

1. Navigate directly to the post URL
2. Click to expand the comment section
3. Scroll and expand all "View more comments" and "View replies" buttons
4. Extract all comments and save them to the database
5. Update the post's comment count in the database

For best results, run with visible browser (without `--headless`) to monitor the comment extraction process.

## Manual Login Process

When you run the scraper, it will:

1. Launch the Firefox browser
2. Navigate to Facebook
3. Prompt you to manually log in:
   ```
   MANUAL LOGIN REQUIRED
   =====================
   1. Log in to Facebook with your credentials in the browser window
   2. Complete any security checks if prompted
   3. Return to this terminal when logged in
   4. Type 'done' and press Enter to continue
   ```
4. After typing 'done', the scraper will check if login was successful
5. If successful, it will continue with scraping

## Viewing and Exporting Comments

### Viewing Comments

To browse and search comments in the database:

```bash
python view_comments.py
```

This will display a menu with options to:
1. View all comments
2. Search comments by keyword
3. Search comments by page
4. Search comments by post

### Exporting Comments

To export comments to text files:

```bash
python export_comments_to_text.py
```

This will:
1. Export all comments from the database to the `exports/` directory
2. Create separate files for each page
3. Include post details and comment metadata

## Working with Comment Extraction

### Comment Extraction Issues

Facebook's comment structure changes frequently, which can lead to issues with comment extraction. The scraper includes several tools to handle this:

#### Using the Comment Fix Tool

If posts are missing comments, run the comment fix tool:

```bash
python comment_fix.py
```

or use the `fix_comments.bat` batch file.

#### Verifying Database Comments

To check if comments are being saved correctly:

```bash
python view_comment_data.py
```

### Troubleshooting Comment Issues

If comments still aren't being extracted properly:

1. **Check the HTML source** - The debug folder contains saved HTML pages
2. **Run the comment fix tool** - It will attempt to repair posts with missing comments
3. **Review the logs** - Check `logs/facebook_scraper.log` for error messages
4. **Test database functionality** - Run `add_test_comments.py` to verify comment saving

## Debugging

The scraper saves debugging information to the `debug/` directory:

- **HTML files**: Complete HTML source of pages
- **Screenshots**: Visual snapshots of the browser state
- **Error logs**: Detailed error information

### Debug File Naming

Debug files follow this naming convention:
- `login_success_[timestamp].html/.png`: Successful login
- `login_failure_[timestamp].html/.png`: Failed login
- `comments_page_[post_id]_[timestamp].html/.png`: Comment page
- `page_not_found_[page_name]_[timestamp].html/.png`: Page not found

## Managing the Database

### Checking Database Status

To check the database status:

```bash
python check_db.py
```

This shows:
- Connection status
- Number of posts stored
- Number of images stored
- Number of comments stored

### Database Backup

To backup the database:

```bash
pg_dump -U postgres facebook_scraper > backup_[date].sql
```

### Database Restore

To restore from a backup:

```bash
psql -U postgres -d facebook_scraper -f backup_file.sql
```

## Advanced Usage

### Running as a Scheduled Task

You can set up the scraper to run automatically on a schedule:

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create a new task
3. Set the program/script to: `path\to\python.exe`
4. Set arguments to: `path\to\facebook_scraper_all.py --headless`
5. Set the schedule as desired

**Linux Cron Job:**
```bash
0 2 * * * cd /path/to/scraper && /path/to/python facebook_scraper_all.py --headless
```

### Using a Proxy

To use a proxy with the scraper, modify `facebook_scraper_all.py` to configure the Firefox proxy settings:

```python
options.set_preference("network.proxy.type", 1)
options.set_preference("network.proxy.http", "proxy_host")
options.set_preference("network.proxy.http_port", proxy_port)
options.set_preference("network.proxy.ssl", "proxy_host") 
options.set_preference("network.proxy.ssl_port", proxy_port)
```

## Error Handling and Recovery

The scraper includes various error handling mechanisms:

- **Login failures**: If login fails, the scraper will save debug information
- **Navigation errors**: If a page can't be accessed, it will move to the next one
- **Extraction failures**: If post data can't be extracted, it logs the error
- **Database errors**: If saving to the database fails, it logs the error

## Performance Tuning

To improve performance:

1. **Limit post count**: Use `--max-posts` to limit the number of posts
2. **Disable images**: Use `--no-images` to skip downloading images
3. **Use headless mode**: Use `--headless` to run without browser UI
4. **Disable screenshots**: Use `--no-screenshots` to skip taking screenshots
