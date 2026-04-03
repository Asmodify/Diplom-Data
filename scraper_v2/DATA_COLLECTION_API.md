# Data Collection Module - API Documentation

## Overview

The Data Collection Module provides a unified, platform-agnostic interface for collecting data from multiple social media platforms (Facebook, Twitter/X, Instagram). It supports keyword-based search, time range filtering, and structured data storage.

## Architecture

```
DataCollectionManager (Orchestrator)
├── PlatformFactory (Creator)
│   ├── FacebookCollector (Facebook Strategy)
│   ├── TwitterCollector (Twitter/X Strategy)
│   └── InstagramCollector (Instagram Strategy)
├── CollectionParams (Configuration)
├── CollectedPost, CollectedComment (Data Models)
└── CollectionResult (Status/Summary)
```

## Core Components

### 1. CollectionParams

Configuration object for collection requests.

```python
from core.data_collection_module import CollectionParams, Platform

params = CollectionParams(
    platform=Platform.FACEBOOK,           # Required: Target platform
    keywords=["AI", "machine learning"],  # Optional: Keywords to search
    start_date=datetime(2024, 1, 1),      # Optional: Start date for timeline
    end_date=datetime(2024, 12, 31),      # Optional: End date for timeline
    max_posts=500,                         # Max posts to collect (default: 100)
    max_comments_per_post=100,             # Max comments per post (default: 50)
    collect_interactions=True,             # Collect likes, shares, etc.
    collect_user_data=True,                # Collect author information
    language="en"                          # Optional: Language filter
)

# Validate parameters
is_valid, error_msg = params.validate()
```

### 2. DataCollectionManager

High-level orchestrator for multi-platform collection.

```python
from core.data_collection_module import DataCollectionManager, Platform
from datetime import datetime, timedelta

# Initialize manager
manager = DataCollectionManager(config=your_config_object)

# Collect from multiple platforms
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK, Platform.TWITTER, Platform.INSTAGRAM],
    keywords=["AI", "data science"],
    start_date=start_date,
    end_date=end_date,
    max_posts=500,
    max_comments_per_post=50
)

# Results are CollectionResult objects
for result in results:
    print(f"{result.platform.value}: {result.posts_collected} posts collected")
    if not result.success:
        print(f"  Errors: {result.errors}")
```

### 3. Platform-Specific Collectors

Each platform collector implements the same interface.

#### FacebookCollector

```python
from core.data_collection_module import (
    PlatformFactory,
    Platform,
    CollectionParams
)

# Create Facebook collector
params = CollectionParams(
    platform=Platform.FACEBOOK,
    keywords=["trending topic"],
    max_posts=200
)
collector = PlatformFactory.create_collector(
    Platform.FACEBOOK,
    params,
    config=your_config
)

# Execute collection
result = collector.collect()

# Get collected data
posts = collector.get_posts()  # Returns List[Dict]
comments = collector.get_comments()  # Returns List[Dict]
```

**Authentication**: Requires `fb_credentials.py` with `FB_EMAIL` and `FB_PASSWORD`.

**Features**:
- Selenium-based browser automation
- Anti-detection measures
- Search via Facebook search URL: `https://www.facebook.com/search/posts/?q={keyword}`
- Comment collection from posts
- Interaction metrics (likes, shares, comments)

#### TwitterCollector

```python
params = CollectionParams(
    platform=Platform.TWITTER,
    keywords=["#Python", "#DataScience"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now(),
    max_posts=500
)
collector = PlatformFactory.create_collector(
    Platform.TWITTER,
    params
)

result = collector.collect()
```

**Authentication**: Requires `TWITTER_BEARER_TOKEN` environment variable.

**Features**:
- Twitter API v2 integration
- Search recent tweets: `GET /tweets/search/recent`
- Search all tweets with date range: `GET /tweets/search/all`
- Support for retweets and reply chains
- Author and engagement metrics

#### InstagramCollector

```python
params = CollectionParams(
    platform=Platform.INSTAGRAM,
    keywords=["#photography", "#digital"],  # Uses as hashtags
    max_posts=300
)
collector = PlatformFactory.create_collector(
    Platform.INSTAGRAM,
    params
)

result = collector.collect()
```

**Authentication**: Requires `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD` environment variables.

**Features**:
- Hashtag-based search (Instagram doesn't support keyword search)
- Comment collection
- Engagement metrics (likes, comments, saves)
- Media URL collection

## Data Models

### CollectedPost

Represents a collected post from any platform.

```python
@dataclass
class CollectedPost:
    post_id: str                        # Unique post ID
    platform: Platform                  # Source platform
    content: str                        # Post text content
    author: str                         # Post author/creator
    author_id: str                      # Author's platform ID
    url: str                            # Direct link to post
    timestamp: datetime                 # When post was created
    
    # Engagement metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    retweets: int = 0                  # Twitter-specific
    views: int = 0                     # Twitter/Instagram-specific
    
    # Content analysis
    keywords_matched: List[str]         # Keywords found in content
    language: Optional[str] = None
    media_urls: List[str]               # Images, videos
    hashtags: List[str]                 # All hashtags found
    mentions: List[str]                 # User mentions
    
    # Collection metadata
    collected_at: datetime              # When we collected it
    source: str = ""                    # "search", "timeline", "hashtag", etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/database storage"""
        ...
```

### CollectedComment

Represents a comment on a post.

```python
@dataclass
class CollectedComment:
    comment_id: str
    post_id: str                        # Parent post ID
    platform: Platform
    author: str                         # Commenter's name
    author_id: str
    content: str                        # Comment text
    timestamp: datetime                 # When comment was created
    likes: int = 0
    replies: int = 0
    
    # For nested comments
    is_reply_to: Optional[str] = None   # ID of parent comment
    level: int = 0                      # Nesting level (0 = top-level)
    
    collected_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        ...
```

### CollectionResult

Summary of collection operation.

```python
@dataclass
class CollectionResult:
    platform: Platform
    posts_collected: int
    comments_collected: int
    interactions_collected: int
    errors: List[str]                   # Any errors during collection
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """How long collection took"""
        ...
    
    @property
    def success(self) -> bool:
        """Whether collection completed without errors"""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        ...
```

## Usage Examples

### Example 1: Search across all platforms for trending topic

```python
from core.data_collection_module import DataCollectionManager, Platform
from datetime import datetime, timedelta

manager = DataCollectionManager(config)

results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK, Platform.TWITTER, Platform.INSTAGRAM],
    keywords=["climate change"],
    max_posts=1000,
    max_comments_per_post=50
)

summary = manager.get_collection_summary()
print(f"✓ Total posts: {summary['total_posts']}")
print(f"✓ Total comments: {summary['total_comments']}")
print(f"✓ Platforms: {summary['platforms_used']}")

# Export to JSON
data = manager.export_data()
# data['posts'] - list of collected posts
# data['comments'] - list of collected comments
# data['summary'] - collection statistics
```

### Example 2: Search within specific date range

```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)  # Last 30 days

results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    start_date=start_date,
    end_date=end_date,
    max_posts=500
)
```

### Example 3: Collect with interaction data

```python
results = manager.collect_from_platforms(
    platforms=[Platform.TWITTER, Platform.INSTAGRAM],
    keywords=["AI", "machine learning"],
    max_posts=300,
    max_comments_per_post=100
)

# Data includes engagement metrics, hashtags, mentions, media
for result in results:
    if result.success:
        posts = manager.all_posts
        for post in posts:
            print(f"Post: {post.content[:50]}...")
            print(f"  Likes: {post.likes}")
            print(f"  Comments: {post.comments}")
            print(f"  Hashtags: {post.hashtags}")
```

### Example 4: Export collected data

```python
# Export to JSON
exported = manager.export_data()

import json
with open('collected_data.json', 'w', encoding='utf-8') as f:
    json.dump(exported, f, indent=2, default=str)

# Save to database
from db.database import DatabaseManager
db = DatabaseManager(config)

for post in exported['posts']:
    db.add_post(post)

for comment in exported['comments']:
    db.add_comment(comment)
```

## REST API Endpoints

You can also access the data collection through FastAPI endpoints:

### POST /api/v1/collect

**Request**:
```json
{
  "platforms": ["facebook", "twitter"],
  "keywords": ["AI", "data science"],
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "max_posts": 500,
  "max_comments_per_post": 50,
  "collect_interactions": true
}
```

**Response**:
```json
{
  "status": "success",
  "total_posts_collected": 1250,
  "total_comments_collected": 8542,
  "platforms": {
    "facebook": {
      "posts": 600,
      "comments": 4200,
      "errors": []
    },
    "twitter": {
      "posts": 650,
      "comments": 4342,
      "errors": []
    }
  },
  "export_url": "/api/v1/collect/results/abc123"
}
```

### GET /api/v1/collect/results/{result_id}

Retrieve previously collected data.

**Response**:
```json
{
  "posts": [...],
  "comments": [...],
  "summary": {...},
  "export_timestamp": "2024-03-29T12:34:56Z"
}
```

## Error Handling

```python
from core.data_collection_module import CollectionParams

params = CollectionParams(
    platform=Platform.FACEBOOK,
    keywords=["test"]
)

# Validate before collection
is_valid, error_msg = params.validate()
if not is_valid:
    print(f"Invalid parameters: {error_msg}")
    # Handle error

# Or check result for errors
result = collector.collect()
if not result.success:
    print(f"Collection failed: {result.errors}")
else:
    print(f"Success: {result.posts_collected} posts")
```

## Environment Variables

Required for authentication:

```bash
# Facebook
FB_EMAIL="your_email@example.com"
FB_PASSWORD="your_password"

# Twitter
TWITTER_BEARER_TOKEN="your_bearer_token_here"

# Instagram
INSTAGRAM_USERNAME="your_username"
INSTAGRAM_PASSWORD="your_password"
```

## Integration with ML Pipeline

After collection, data flows to AI analysis:

```python
from core.data_collection_module import DataCollectionManager, Platform
from ml.ai_analyzer import AIAnalyzer

# Step 1: Collect data
manager = DataCollectionManager(config)
results = manager.collect_from_platforms(
    platforms=[Platform.FACEBOOK],
    keywords=["trending"],
    max_posts=100
)

# Step 2: Analyze with AI
analyzer = AIAnalyzer(config)
collected_data = manager.export_data()

for post in collected_data['posts']:
    analysis = analyzer.analyze_all({
        'content': post['content'],
        'comments': collected_data['comments']
    })
    
    print(f"Sentiment: {analysis['sentiment_score']}")
    print(f"Topics: {analysis['topics_lda']}")
    print(f"Engagement prediction: {analysis['engagement_score_prediction']}")
```

## Performance Considerations

- **Rate Limiting**: Respect platform rate limits (Facebook: slower; Twitter: 450 req/15min; Instagram: API dependent)
- **Timeout**: Default timeout is 30 seconds per request (configurable)
- **Batch Processing**: Collect in batches to avoid memory issues
- **Storage**: Use streaming to database for large collections

```python
# Batch collection
for i in range(0, 1000, 100):
    results = manager.collect_from_platforms(
        platforms=[Platform.FACEBOOK],
        keywords=["keyword"],
        max_posts=100
    )
    
    # Save results immediately
    data = manager.export_data()
    db.batch_insert(data['posts'], data['comments'])
    
    # Clear for next batch
    manager.all_posts = []
    manager.all_comments = []
```

## Troubleshooting

### Facebook Collection Issues

- **"Failed to login"**: Check FB_EMAIL and FB_PASSWORD
- **"No posts found"**: Try different keywords; some pages may be private
- **Slow collection**: Add delays between requests to avoid rate limiting

### Twitter Collection Issues

- **"Invalid Bearer Token"**: Regenerate token from Twitter API dashboard
- **"Not enough permissions"**: Ensure API has v2 access

### Instagram Collection Issues

- **"Account blocked temporarily"**: Wait before retrying; too many requests
- **"Private account"**: Can't collect from private accounts

## Thread Safety

The module is **not thread-safe** by default. For concurrent collection:

```python
import threading
from queue import Queue

def collect_platform(platform, queue):
    manager = DataCollectionManager(config)
    result = manager.collect_from_platforms(
        platforms=[platform],
        keywords=["keyword"]
    )
    queue.put(result)

queue = Queue()
threads = []
for platform in [Platform.FACEBOOK, Platform.TWITTER]:
    t = threading.Thread(target=collect_platform, args=(platform, queue))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

results = []
while not queue.empty():
    results.append(queue.get())
```

## Future Extensions

- [ ] TikTok support
- [ ] Reddit support
- [ ] YouTube comments
- [ ] Kafka streaming integration
- [ ] GraphQL API
- [ ] Webhook notifications on collection completion
