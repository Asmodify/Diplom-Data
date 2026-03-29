# Modular Facebook Scraper - New

A modular Facebook scraper with automated scheduling, content management, and smart scraping features.

## Features

- **Smart Scraping**
  - Automatic post detection and scraping
  - Screenshot capture with post metadata
  - Smart comment handling (100 comment limit)
  - Image extraction and downloading
  - Reply extraction

- **Content Management**
  - Organized storage of posts, comments, and images
  - Screenshot management
  - Export capabilities
  - PostgreSQL database integration

- **Automation**
  - Scheduled scraping
  - Multiple page support
  - Configurable limits and settings
  - Headless mode support

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure PostgreSQL database:
```bash
python setup_postgres_db.py
```

3. Initialize project:
```bash
python init_project.py
```

4. Run the scraper:
```bash
run_fb_scraper.bat
```

Or use the interactive menu:
```bash
facebook_tools.bat
```

## Project Structure

```plaintext
beta/
├── automation/         # Scraping automation
│   └── auto_scraper.py   # Main automation coordinator
├── content_manager/   # Content handling
│   └── content_saver.py  # Content saving/loading
├── scraper/          # Core scraping logic
│   ├── browser_manager.py # Browser session handling
│   └── post_scraper.py   # Post/comment scraping
├── tests/           # Test suite
│   ├── __init__.py
│   ├── run_tests.py
│   └── test_*.py
├── db/             # Database integration
├── run_fb_scraper.bat   # Main scraper entry point
├── facebook_tools.bat   # Interactive menu
└── requirements.txt    # Dependencies
```

## Usage

### Command Line Options
- `--headless`: Run without browser UI
- `--pages FILE`: Use custom pages file
- `--max-comments N`: Set maximum comments per post
- `--no-screenshots`: Disable post screenshots
- `--no-images`: Disable image downloads

Example:
```bash
run_fb_scraper.bat --max-comments 50 --no-images
```

### Interactive Menu Options
1. Initialize Project (first-time setup)
2. Test Database Connection (run tests)
3. Configure Database (PostgreSQL setup)
4. Run Scraper (with options)
5. View Content Manager

## Testing

Run the test suite:
```bash
run_tests.bat
```

## Requirements

- Python 3.9+
- PostgreSQL database
- Firefox browser
- Selenium WebDriver
