# Facebook Scraper v2.0

Advanced Facebook page scraper with sentiment analysis, database storage, and API server.

## Features

- **Smart Scraping**: Selenium-based with Firefox, anti-detection, human-like behavior
- **Robust Login**: 3-tier (cookies → credentials → manual)
- **Comment Extraction**: Multi-strategy modal handling with BeautifulSoup parsing
- **Database**: PostgreSQL (primary) + SQLite (fallback) + Firebase (cloud sync)
- **ML Analysis**: TextBlob/VADER sentiment, optional BERT support
- **REST API**: FastAPI with Bearer token authentication
- **Export**: JSON, CSV, Google Sheets integration

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Edit `fb_credentials.py`:
```python
FB_EMAIL = "your_email@example.com"
FB_PASSWORD = "your_password"
```

### 3. Add Pages to Scrape

Edit `pages.txt`:
```
https://www.facebook.com/page1
https://www.facebook.com/page2
```

### 4. Run

```bash
# Interactive mode
python run.py

# Scrape single page
python run.py scrape https://www.facebook.com/example

# Scrape from file
python run.py scrape --file pages.txt

# Start API server
python run.py api

# Auto-scraper (continuous)
python run.py auto
```

## Project Structure

```
scraper_v2/
├── run.py              # Main entry point
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── fb_credentials.py   # Facebook credentials (NEVER COMMIT!)
├── pages.txt           # Pages to scrape
│
├── core/               # Core scraping logic
│   ├── browser_manager.py   # Browser session management
│   ├── post_scraper.py      # Post/comment extraction
│   └── scraper.py           # Main scraper orchestrator
│
├── db/                 # Database layer
│   ├── models.py       # SQLAlchemy models
│   ├── database.py     # Database manager
│   └── firebase_db.py  # Firebase integration
│
├── ml/                 # Machine learning
│   ├── analyzer.py     # Basic TextBlob/VADER analysis
│   ├── advanced_sentiment.py  # BERT-based analysis
│   └── ai_analyzer.py         # AI-powered comprehensive analysis
│
├── api/                # REST API
│   └── server.py       # FastAPI server
│
├── utils/              # Utilities
│   ├── cookie_helper.py     # Cookie management
│   └── helpers.py           # Common utilities
│
├── integrations/       # External integrations
│   └── google_sheets.py     # Google Sheets export
│
├── data/               # Data storage
├── logs/               # Log files
└── exports/            # Exported data
```

## AI-Powered Analysis

The scraper includes a comprehensive AI analysis module that provides:

- **Sentiment Analysis**: TextBlob, VADER, and optional BERT support
- **Topic Clustering**: TF-IDF vectorization with KMeans clustering
- **Engagement Metrics**: Likes, comments, shares analysis with viral potential detection
- **Temporal Patterns**: Best posting times, frequency analysis
- **Audience Insights**: Community health, top commenters
- **Automated Recommendations**: AI-generated actionable insights

### Using AI Analysis

```bash
# Run comprehensive AI analysis
python run.py analyze --ai --limit 100

# Export analysis to JSON
python run.py analyze --ai --limit 100 --output analysis_report.json
```

### Python API

```python
from ml.ai_analyzer import AIAnalyzer
from db.database import DatabaseManager

db = DatabaseManager()
analyzer = AIAnalyzer()

# Get data
posts = db.get_all_posts(limit=100)
comments = db.get_all_comments(limit=1000)

# Run analysis
analysis = analyzer.analyze_all(posts, comments)

# Generate report
report = analyzer.generate_report(analysis)
print(report)

# Export to JSON
analyzer.export_analysis(analysis, 'analysis.json', 'json')
```

## API Endpoints

Start server: `python run.py api`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/scrape` | POST | Start scraping |
| `/api/v1/pages` | GET | List pages |
| `/api/v1/posts/{id}/comments` | GET | Get comments |
| `/api/v1/analyze` | POST | Analyze text |
| `/api/v1/analyze/ai` | POST | AI-powered comprehensive analysis |
| `/api/v1/export/pages` | GET | Export pages |

Authentication: Bearer token (set in config.py)

## Configuration

Environment variables or `config.py`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL URL | `sqlite:///data/scraper.db` |
| `API_KEY` | API authentication key | Auto-generated |
| `FB_EMAIL` | Facebook email | From fb_credentials.py |
| `FB_PASSWORD` | Facebook password | From fb_credentials.py |
| `HEADLESS` | Run browser headless | `False` |

## Advanced ML (Optional)

For BERT-based sentiment analysis:

```bash
pip install torch transformers
```

Then use `AdvancedSentimentAnalyzer` for advanced sentiment or the `AIAnalyzer` for comprehensive analysis.

## Features Summary

| Feature | Description |
|---------|-------------|
| Smart Scraping | Selenium with anti-detection, human-like behavior |
| 3-Tier Login | Cookies → Credentials → Manual fallback |
| Comment Extraction | Multi-strategy modal handling |
| Database Support | PostgreSQL + SQLite + Firebase |
| Sentiment Analysis | TextBlob, VADER, BERT |
| AI Analysis | Topic clustering, engagement analysis, recommendations |
| REST API | FastAPI with authentication |
| Export | JSON, CSV, Google Sheets |

## Troubleshooting

### Common Issues

1. **Browser not starting**: Install Firefox and geckodriver
2. **Login failing**: Check credentials, may need manual login first
3. **No comments**: Facebook may be rate limiting, increase delays
4. **Database errors**: Check PostgreSQL connection or use SQLite fallback

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run.py scrape https://facebook.com/example
```

## License

MIT
