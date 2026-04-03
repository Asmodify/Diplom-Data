# ML & Cloud Integration Guide

This guide explains how to use the new ML analysis, Firebase, FastAPI, and Google Sheets features.

## 🚀 Quick Start

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

---

## 🔥 Firebase Firestore Setup

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Firestore Database (in test mode for development)

### Step 2: Get Service Account Credentials
1. Go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the JSON file as `firebase_credentials.json` in the project root

### Step 3: Set Environment Variable
```bash
# In .env file
FIREBASE_CREDENTIALS=firebase_credentials.json
```

### Usage
```python
from db.firebase_db import get_firebase_db

# Initialize Firebase
db = get_firebase_db()

# Save a post
db.save_post({
    'post_id': '123',
    'page_name': 'CNN',
    'content': 'Breaking news...',
    'likes': 100
})

# Get all posts
posts = db.get_all_posts()

# Save analysis results
db.save_analysis_result('123', 'sentiment', {'sentiment': 'positive', 'score': 0.8})
```

---

## 📊 Google Sheets Setup

### Step 1: Enable Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Sheets API" and "Google Drive API"

### Step 2: Create Service Account
1. Go to APIs & Services → Credentials
2. Create Service Account
3. Download JSON key file as `google_credentials.json`

### Step 3: Set Environment Variable
```bash
# In .env file
GOOGLE_SHEETS_CREDENTIALS=google_credentials.json
```

### Usage
```python
from integrations.google_sheets import GoogleSheetsExporter

# Initialize exporter
exporter = GoogleSheetsExporter()

# Export posts to a spreadsheet
url = exporter.export_posts(posts, "My Facebook Data")
print(f"Spreadsheet: {url}")

# Create real-time logging spreadsheet
log_url = exporter.create_realtime_log()
```

---

## 🤖 ML Analysis

The ML analyzer provides three types of analysis:

### 1. Sentiment Analysis
Classifies post content as positive, neutral, or negative.

### 2. Topic Classification
Uses LDA (Latent Dirichlet Allocation) to identify topics in posts.

### 3. Engagement Prediction
Uses CatBoost/Gradient Boosting to predict engagement levels.

### Usage
```python
from ml.analyzer import DataAnalyzer

# Initialize analyzer
analyzer = DataAnalyzer()

# Prepare posts (list of dictionaries)
posts = [
    {'post_id': '1', 'content': 'Great news!', 'likes': 100, 'shares': 50},
    {'post_id': '2', 'content': 'Terrible weather today', 'likes': 10, 'shares': 2}
]

# Run individual analyses
sentiment_results = analyzer.analyze_sentiment(posts)
topic_results = analyzer.classify_topics(posts)
engagement_results = analyzer.predict_engagement(posts)

# Or run all analyses at once
all_results = analyzer.analyze_all(posts)

# Get summary statistics
stats = analyzer.get_summary_stats(posts)
print(stats)
```

---

## 🌐 FastAPI Server

The API server provides REST endpoints for accessing data and running analyses.

### Start the Server
```bash
# Using Python
python api_server.py

# Or with uvicorn directly
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/posts` | Get all posts |
| GET | `/posts/{post_id}` | Get single post |
| POST | `/posts` | Create new post |
| DELETE | `/posts/{post_id}` | Delete post |
| GET | `/posts/{post_id}/comments` | Get comments |
| GET | `/posts/{post_id}/images` | Get images |
| POST | `/analyze` | Run ML analysis |
| GET | `/analysis/{post_id}` | Get analysis results |
| GET | `/stats` | Get statistics |
| POST | `/export/sheets` | Export to Google Sheets |

### Example API Calls
```bash
# Get all posts
curl http://localhost:8000/posts

# Run analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_types": ["sentiment", "topic", "engagement"]}'

# Export to Google Sheets
curl -X POST http://localhost:8000/export/sheets \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_name": "My Export", "include_analysis": true}'
```

---

## 📤 Data Migration

The data exporter helps migrate data between systems.

### Migrate PostgreSQL to Firebase
```python
from data_exporter import DataExporter

exporter = DataExporter()
counts = exporter.migrate_postgres_to_firebase()
print(f"Migrated: {counts}")
```

### Full Pipeline (PostgreSQL → Firebase → Analysis → Sheets)
```python
from data_exporter import DataExporter

exporter = DataExporter()
results = exporter.full_pipeline(
    spreadsheet_name="Complete_Export",
    run_analysis=True
)
print(results)
```

### Command Line
```bash
# Full migration with analysis
python data_exporter.py --action full --spreadsheet "My Data"

# Just migrate to Firebase
python data_exporter.py --action migrate

# Export to JSON
python data_exporter.py --action export-json --output data.json
```

---

## 📁 Project Structure

```
project/
├── api_server.py           # FastAPI REST API
├── data_exporter.py        # Data migration utilities
├── db/
│   ├── config.py           # Configuration settings
│   ├── database.py         # PostgreSQL/SQLite handler
│   ├── firebase_db.py      # Firebase Firestore handler
│   └── models.py           # SQLAlchemy models
├── integrations/
│   └── google_sheets.py    # Google Sheets exporter
├── ml/
│   └── analyzer.py         # ML analysis module
├── .env.example            # Environment variables template
└── requirements.txt        # Python dependencies
```

---

## 🧪 Testing & Verification

Before using the system, verify each component is working correctly.

### Quick Start Scripts (Windows)

| Script | Description |
|--------|-------------|
| `run_all_tests.bat` | Run all tests sequentially |
| `test_firebase.bat` | Test Firebase connection |
| `test_sheets.bat` | Test Google Sheets connection |
| `test_api.bat` | Test API endpoints |
| `run_api_server.bat` | Start the FastAPI server |
| `migrate_data.bat` | Interactive migration tool |

### Testing Step by Step

**Step 1: Test Firebase Connection**
```bash
python test_firebase.py
```
This verifies:
- Credentials are found and valid
- Can connect to Firestore
- Can read/write data

**Step 2: Test Google Sheets (optional)**
```bash
python test_sheets.py
```
This verifies:
- Credentials are found and valid
- Can create spreadsheets
- Can export data

**Step 3: Test ML Analyzer**
```bash
python test_ml.py
```
This verifies:
- Sentiment analysis works
- Topic classification works
- Engagement prediction works

**Step 4: Test API Server**
```bash
# Terminal 1: Start server
python api_server.py

# Terminal 2: Run tests
python test_api.py
```

### Interactive Migration Tool

The migration tool provides a menu-driven interface:
```bash
python migrate_data.py
```

Options:
1. Migrate PostgreSQL → Firebase
2. Export Firebase → Google Sheets
3. Run ML Analysis on Firebase data
4. Test Firebase connection
5. Test Google Sheets connection
6. Test API server

---

## 🔧 Troubleshooting

### Firebase Connection Issues
- Ensure `firebase_credentials.json` exists and is valid
- Check that Firestore is enabled in your Firebase project
- Verify the service account has Firestore Admin role

### Google Sheets Issues
- Ensure both Sheets API and Drive API are enabled
- The service account email must have access to the spreadsheet
- Check quota limits on the API

### ML Analysis Errors
- Install NLTK data: `python -c "import nltk; nltk.download('all')"`
- Ensure CatBoost is installed: `pip install catboost`
- Check that TextBlob is installed: `pip install textblob`

---

## 📝 Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_BACKEND` | Database type | `postgresql` |
| `FIREBASE_CREDENTIALS` | Firebase JSON path | None |
| `GOOGLE_SHEETS_CREDENTIALS` | Google JSON path | None |
| `API_HOST` | FastAPI host | `0.0.0.0` |
| `API_PORT` | FastAPI port | `8000` |
| `ML_N_TOPICS` | LDA topics count | `5` |
