# 📖 API Usage Guide

## Overview

Your API is now deployed on Render and ready to use!

**Base URL:** `https://diplom-data-api.onrender.com`

**Authentication:** All endpoints (except `/health`) require a Bearer token in the Authorization header.

---

## Table of Contents

1. [Health Check](#health-check)
2. [Posts](#posts)
3. [Comments](#comments)
4. [Images](#images)
5. [Analysis](#analysis)
6. [Sentiment Analysis](#sentiment-analysis)
7. [Trends & Topics](#trends--topics)
8. [Statistics](#statistics)
9. [Authentication](#authentication)
10. [Error Handling](#error-handling)

---

## Health Check

**Test if API is online** (no authentication required)

```bash
GET /health

# Example
curl https://diplom-data-api.onrender.com/health

# Response
{
  "status": "healthy",
  "version": "2.0.0",
  "firebase": true,
  "analyzer": true,
  "advanced_analyzer": false,
  "sheets": false
}
```

---

## Posts

### Get All Posts

```bash
GET /api/v1/posts?limit=100&page_name=optional_page

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://diplom-data-api.onrender.com/api/v1/posts?limit=50"

# Query Parameters:
# - limit: Max number of posts (default 100, max 1000)
# - page_name: Filter by Facebook page name (optional)

# Response:
[
  {
    "id": "post_123",
    "page_name": "BBC News",
    "post_id": "456_789",
    "content": "Breaking news...",
    "timestamp": "2024-04-03T10:30:00",
    "likes": 150,
    "shares": 20,
    "comment_count": 45
  }
]
```

### Get Single Post

```bash
GET /api/v1/posts/{post_id}

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://diplom-data-api.onrender.com/api/v1/posts/456_789"

# Response:
{
  "id": "post_123",
  "page_name": "BBC News",
  "post_id": "456_789",
  ...
}
```

### Create Post

```bash
POST /api/v1/posts

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_name": "BBC News",
    "post_id": "456_789",
    "content": "Breaking news...",
    "likes": 150,
    "shares": 20,
    "comment_count": 45
  }' \
  https://diplom-data-api.onrender.com/api/v1/posts

# Response:
{
  "id": "post_123",
  "status": "success"
}
```

### Delete Post

```bash
DELETE /api/v1/posts/{post_id}

curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/posts/456_789

# Response:
{
  "message": "Post deleted successfully"
}
```

---

## Comments

### Get Comments for Post

```bash
GET /api/v1/posts/{post_id}/comments

curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/posts/456_789/comments

# Response:
[
  {
    "id": "comment_123",
    "author_name": "John Doe",
    "content": "Great article!",
    "timestamp": "2024-04-03T11:00:00",
    "likes": 5
  }
]
```

### Add Comment

```bash
POST /api/v1/posts/{post_id}/comments

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "author_name": "John Doe",
    "content": "Great article!",
    "likes": 0
  }' \
  https://diplom-data-api.onrender.com/api/v1/posts/456_789/comments

# Response:
{
  "comment_id": "comment_123",
  "message": "Comment saved"
}
```

---

## Images

### Get Images for Post

```bash
GET /api/v1/posts/{post_id}/images

curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/posts/456_789/images

# Response:
[
  {
    "id": "image_123",
    "image_url": "https://facebook.com/image.jpg",
    "local_path": "./images/image_123.jpg"
  }
]
```

### Add Image to Post

```bash
POST /api/v1/posts/{post_id}/images

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://facebook.com/image.jpg",
    "local_path": "./images/image_123.jpg"
  }' \
  https://diplom-data-api.onrender.com/api/v1/posts/456_789/images

# Response:
{
  "image_id": "image_123",
  "message": "Image saved"
}
```

---

## Analysis

### Run ML Analysis on Posts

```bash
POST /api/v1/analyze

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "post_ids": ["456_789", "456_790"],
    "analysis_types": ["sentiment", "topic", "engagement"],
    "use_advanced": true
  }' \
  https://diplom-data-api.onrender.com/api/v1/analyze

# Body options:
# - post_ids: Specific posts to analyze (null = all posts)
# - analysis_types: "sentiment", "topic", "engagement"
# - use_advanced: true = BERT (slower, accurate), false = TextBlob (fast)

# Response:
{
  "message": "Analysis completed for 2 posts",
  "results_count": 6,
  "results": [
    {
      "post_id": "456_789",
      "analysis_type": "sentiment",
      "result": {
        "sentiment": "positive",
        "score": 0.85
      }
    }
  ]
}
```

### Get Analysis Results

```bash
GET /api/v1/analysis/{post_id}?analysis_type=sentiment

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://diplom-data-api.onrender.com/api/v1/analysis/456_789?analysis_type=sentiment"

# Query Parameters:
# - analysis_type: "sentiment", "topic", or "engagement" (optional)

# Response:
[
  {
    "analysis_type": "sentiment",
    "result": {
      "sentiment": "positive",
      "score": 0.85,
      ...
    },
    "analyzed_at": "2024-04-03T10:30:00"
  }
]
```

---

## Sentiment Analysis

### Analyze Single Text

```bash
POST /api/v1/sentiment

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I absolutely love this product!",
    "language": "en"
  }' \
  https://diplom-data-api.onrender.com/api/v1/sentiment

# Response:
{
  "status": "success",
  "data": {
    "sentiment": "positive",
    "confidence": 0.95,
    "emotion": "joy",
    "sarcasm_detected": false
  }
}
```

### Analyze Multiple Texts (Batch)

```bash
POST /api/v1/sentiment/batch

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "I love this!",
      "This is terrible",
      "It was okay"
    ],
    "language": "en"
  }' \
  https://diplom-data-api.onrender.com/api/v1/sentiment/batch

# Max 100 texts per batch

# Response:
{
  "status": "success",
  "data": [
    {
      "sentiment": "positive",
      "confidence": 0.9,
      ...
    },
    {
      "sentiment": "negative",
      "confidence": 0.87,
      ...
    },
    {
      "sentiment": "neutral",
      "confidence": 0.72,
      ...
    }
  ],
  "count": 3
}
```

---

## Trends & Topics

### Get Trending Topics

```bash
GET /api/v1/trends?platform=facebook&limit=10

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://diplom-data-api.onrender.com/api/v1/trends?limit=10"

# Query Parameters:
# - platform: "facebook" (default)
# - limit: Max number of trends (1-50, default 10)

# Response:
{
  "status": "success",
  "data": [
    {
      "trend": "#covid19",
      "platform": "facebook",
      "mentions": 456,
      "type": "hashtag"
    },
    {
      "trend": "politics",
      "platform": "facebook",
      "mentions": 123,
      "type": "keyword"
    }
  ],
  "total_posts_analyzed": 1000
}
```

### Get Popular Topics

```bash
GET /api/v1/topics?limit=10&start_date=2024-04-01&end_date=2024-04-03

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://diplom-data-api.onrender.com/api/v1/topics?limit=10"

# Query Parameters:
# - limit: Max results (1-50)
# - start_date: ISO format "YYYY-MM-DD" (optional)
# - end_date: ISO format "YYYY-MM-DD" (optional)
# - platform: "facebook" (default)

# Response:
{
  "status": "success",
  "data": [
    {
      "topic": "technology",
      "mentions": 234,
      "platform": "facebook",
      "avg_engagement": 45.5
    }
  ],
  "total_posts_analyzed": 500
}
```

---

## Statistics

### Get Overall Stats

```bash
GET /api/v1/stats

curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/stats

# Response:
{
  "total_posts": 15000,
  "total_pages": 42,
  "total_comments": 95000,
  "avg_likes": 250.5,
  "avg_shares": 42.3,
  "avg_comments": 6.3,
  "sentiment_distribution": {
    "positive": 5000,
    "neutral": 7000,
    "negative": 3000
  }
}
```

---

## Authentication

### Bearer Token

All protected endpoints require an `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/posts
```

### Get Your Token

- For development: Token is set in `.env` file
- For production (Render): Check your service environment variables

### Generate New Token

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: OpenSSL
openssl rand -hex 32

# Option 3: Online generator
# https://randomkeygen.com/
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Descriptive error message"
}
```

### Common Errors

| Status Code | Message | Solution |
|-------------|---------|----------|
| 200 | Success | Request completed normally |
| 400 | Bad Request | Invalid parameters or body |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Invalid authentication token |
| 404 | Not Found | Resource doesn't exist |
| 503 | Service Unavailable | Firebase or analyzer not initialized |

### Example Error Response

```bash
# Invalid token
curl -H "Authorization: Bearer wrong_token" \
  https://diplom-data-api.onrender.com/api/v1/posts

# Response (403):
{
  "detail": "Invalid authentication token"
}
```

---

## Code Examples

### JavaScript/TypeScript

```typescript
const API_URL = "https://diplom-data-api.onrender.com";
const TOKEN = "YOUR_API_TOKEN";

// Fetch posts
async function getPosts(limit = 50) {
  const response = await fetch(
    `${API_URL}/api/v1/posts?limit=${limit}`,
    {
      headers: {
        "Authorization": `Bearer ${TOKEN}`,
        "Content-Type": "application/json"
      }
    }
  );
  return response.json();
}

// Analyze sentiment
async function analyzeSentiment(text) {
  const response = await fetch(`${API_URL}/api/v1/sentiment`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text: text,
      language: "en"
    })
  });
  return response.json();
}

// Usage
getPosts(100).then(data => console.log(data));
analyzeSentiment("This is great!").then(result => console.log(result));
```

### Python

```python
import requests

API_URL = "https://diplom-data-api.onrender.com"
TOKEN = "YOUR_API_TOKEN"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get posts
response = requests.get(
    f"{API_URL}/api/v1/posts?limit=50",
    headers=headers
)
posts = response.json()
print(posts)

# Analyze sentiment
data = {
    "text": "This is amazing!",
    "language": "en"
}
response = requests.post(
    f"{API_URL}/api/v1/sentiment",
    json=data,
    headers=headers
)
result = response.json()
print(result)
```

### cURL

```bash
TOKEN="YOUR_API_TOKEN"
API_URL="https://diplom-data-api.onrender.com"

# Get stats
curl -H "Authorization: Bearer $TOKEN" \
  $API_URL/api/v1/stats | jq

# Get trends
curl -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/trends?limit=5" | jq

# Analyze text
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Great news!","language":"en"}' \
  $API_URL/api/v1/sentiment | jq
```

---

## Rate Limiting

- Free tier: 100 requests/minute per IP
- Standard tier: 1000 requests/minute
- Pro tier: 10000 requests/minute

---

## Support

- **API Docs:** https://diplom-data-api.onrender.com/docs
- **FastAPI Help:** https://fastapi.tiangolo.com
- **Render Docs:** https://render.com/docs

---

## Next Steps

1. ✅ API is deployed
2. 📱 Connect your frontend
3. 📊 Start using the endpoints
4. 📈 Monitor with Render dashboard
5. 🔄 Add more data/pages as needed
