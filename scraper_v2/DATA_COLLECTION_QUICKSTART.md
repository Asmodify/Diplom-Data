# Data Collection Module - Quick Start Guide

## 5-Minute Setup

### 1. Install Base Dependencies
All dependencies are already in `scraper_v2/requirements.txt`. If needed:

```bash
cd scraper_v2
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file in `scraper_v2/`:

```bash
# Facebook
FB_EMAIL="your_email@facebook.com"
FB_PASSWORD="your_app_password"

# Twitter (optional)
TWITTER_BEARER_TOKEN="your_bearer_token"

# Instagram (optional)
INSTAGRAM_USERNAME="your_username"
INSTAGRAM_PASSWORD="your_password"
```

### 3. Quick Python Example

```python
# test_collection.py
from core.data_collection_module import DataCollectionManager, Platform
from datetime import datetime, timedelta

# Initialize manager
manager = DataCollectionManager()

# Collect from Facebook only (simplest example)
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["AI machine learning"],  # Search for these keywords
    max_posts=10,                       # Get max 10 posts
    max_comments_per_post=5             # Max 5 comments per post
)

# Display results
for result in results:
    print(f"✓ {result.platform.value}")
    print(f"  Posts: {result.posts_collected}")
    print(f"  Comments: {result.comments_collected}")
    if result.errors:
        print(f"  Errors: {result.errors}")

# Export collected data
data = manager.export_data()
print(f"\nTotal posts collected: {len(data['posts'])}")
print(f"Total comments collected: {len(data['comments'])}")

# Save to JSON
import json
with open('collected_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, default=str)
print("✓ Data saved to collected_data.json")
```

Run it:
```bash
cd scraper_v2
python test_collection.py
```

## Common Use Cases

### Case 1: Search by Keywords (Any Platform)

```python
from core.data_collection_module import DataCollectionManager, Platform

manager = DataCollectionManager()

# Search Facebook for posts about AI
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["artificial intelligence", "machine learning"],
    max_posts=100
)

print(f"Found {results[0].posts_collected} posts")
```

### Case 2: Collect from Time Range

```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)  # Last 7 days

results = manager.collect_from_platforms(
    platforms=[Platform.TWITTER],
    start_date=start_date,
    end_date=end_date,
    max_posts=500
)

print(f"Collected {results[0].posts_collected} tweets from last week")
```

### Case 3: Multi-Platform Collection

```python
# Collect from all three platforms simultaneously
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK, Platform.TWITTER, Platform.INSTAGRAM],
    keywords=["data science"],
    max_posts=200,
    max_comments_per_post=50
)

# View summary
summary = manager.get_collection_summary()
print(f"Total posts: {summary['total_posts']}")
print(f"Total comments: {summary['total_comments']}")
print(f"Success rate: {summary['successful_collections']}/{len(results)}")
```

### Case 4: Process with AI Analysis

```python
from core.data_collection_module import DataCollectionManager, Platform
from ml.ai_analyzer import AIAnalyzer

# Collect data
manager = DataCollectionManager()
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["technology"],
    max_posts=50
)

# Analyze with AI
analyzer = AIAnalyzer()
collected_data = manager.export_data()

analysis_results = []
for post in collected_data['posts']:
    # Prepare comments for analysis
    related_comments = [c for c in collected_data['comments'] if c['post_id'] == post['post_id']]
    
    # Run comprehensive AI analysis
    analysis = analyzer.analyze_all({
        'content': post['content'],
        'comments': [c['content'] for c in related_comments]
    })
    
    analysis_results.append({
        'post': post['content'][:50] + '...',
        'sentiment': analysis.get('sentiment_label', 'unknown'),
        'engagement_score': analysis.get('engagement_score_prediction', 0),
        'topics': analysis.get('topics_lda', [])
    })
    
    # Print results
    print(f"\nPost: {analysis_results[-1]['post']}")
    print(f"  Sentiment: {analysis_results[-1]['sentiment']}")
    print(f"  Engagement: {analysis_results[-1]['engagement_score']:.2f}")
    print(f"  Topics: {', '.join(analysis_results[-1]['topics'][:3])}")
```

### Case 5: Save to Different Formats

```python
import json
import csv

manager = DataCollectionManager()
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["trending"],
    max_posts=100
)

data = manager.export_data()

# Save as JSON
with open('posts.json', 'w', encoding='utf-8') as f:
    json.dump(data['posts'], f, indent=2, default=str)

# Save as CSV
with open('posts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=data['posts'][0].keys())
    writer.writeheader()
    writer.writerows(data['posts'])

# Save to database
from db.database import DatabaseManager
db = DatabaseManager()
for post in data['posts']:
    db.add_post(post)

print("✓ Data saved to JSON, CSV, and database")
```

## Troubleshooting

### Issue: "Failed to authenticate with facebook"

**Solution**: Check Facebook credentials in `.env`
```bash
# Make sure these are correct
FB_EMAIL="your_actual_email@facebook.com"
FB_PASSWORD="your_actual_password"
```

### Issue: "No posts found"

**Possible causes**:
- Too specific keywords
- Private page
- No posts matching criteria
- Rate limited (wait a few minutes)

**Solution**: Try different keywords or broader search

### Issue: "TWITTER_BEARER_TOKEN not found"

**Solution**: Get Twitter API credentials
1. Go to https://developer.twitter.com
2. Create an app
3. Get v2 API access
4. Add Bearer token to `.env`

### Issue: KeyError on Instagram

**Solution**: Instagram requires special setup
1. Install instagrapi: `pip install instagrapi`
2. Add `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD` to `.env`
3. Note: Instagram doesn't support keyword search, uses hashtags instead

## API Integration

### Use via FastAPI (if server is running)

```bash
# Start the API server
cd scraper_v2
python -m api.server
```

Then use with curl or Python requests:

```python
import requests
import json

# Trigger collection
response = requests.post(
    "http://localhost:8000/api/v1/collect",
    headers={"Authorization": "Bearer your_token"},
    json={
        "platforms": ["facebook"],
        "keywords": ["AI"],
        "max_posts": 100,
        "max_comments_per_post": 50
    }
)

result = response.json()
print(f"Collection ID: {result['collection_id']}")
print(f"Status: {result['status']}")

# Retrieve results
response = requests.get(
    f"http://localhost:8000/api/v1/collect/results/{result['collection_id']}",
    headers={"Authorization": "Bearer your_token"}
)

data = response.json()
print(f"Posts collected: {len(data['posts'])}")
```

## Advanced Configuration

### Limit Collection Time

```python
import time
from core.data_collection_module import DataCollectionManager, Platform

manager = DataCollectionManager()

# Collect with timeout
start_time = time.time()
timeout_seconds = 60

results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["keyword"],
    max_posts=1000
)

elapsed = time.time() - start_time
if elapsed > timeout_seconds:
    print(f"Warning: Collection took {elapsed}s (timeout was {timeout_seconds}s)")
```

### Batch Processing

```python
from core.data_collection_module import DataCollectionManager, Platform

keywords_list = [
    ["AI", "machine learning"],
    ["data science"],
    ["python programming"],
    ["web development"],
    ["cloud computing"]
]

all_data = []

for keywords in keywords_list:
    print(f"Collecting: {keywords}")
    
    manager = DataCollectionManager()
    results = manager.collect_from_platforms(
        platforms=[Platform.FACEBOOK],
        keywords=keywords,
        max_posts=100
    )
    
    data = manager.export_data()
    all_data.extend(data['posts'])
    
    print(f"  Collected {len(data['posts'])} posts")

print(f"\nTotal: {len(all_data)} posts across all queries")
```

## Next Steps

1. **Read Full Documentation**: See [DATA_COLLECTION_API.md](DATA_COLLECTION_API.md)
2. **Check Implementation**: See [AUTOMATED_DATA_COLLECTION_IMPLEMENTATION.md](../AUTOMATED_DATA_COLLECTION_IMPLEMENTATION.md)
3. **Review Thesis**: See `thesis/main.tex` for academic documentation
4. **Integrate with Analysis**: Use collected data with `AIAnalyzer` for insights
5. **Deploy**: Use admin controls to schedule regular collections

## Support

- **API Docs**: `DATA_COLLECTION_API.md` (in this directory)
- **Implementation Details**: `AUTOMATED_DATA_COLLECTION_IMPLEMENTATION.md` (parent directory)
- **Thesis**: `thesis/main.tex` (academic documentation in Mongolian)
- **Source Code**: `core/data_collection_module.py` (1000+ lines with comments)

---

**Happy collecting!** 🚀

For questions or issues, check the troubleshooting section above or review the source code comments.
