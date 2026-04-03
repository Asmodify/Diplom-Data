"""
FastAPI Server Module
RESTful API for accessing Facebook scraper data and ML analysis
Version: 2.0.0 - Enhanced with API versioning, auth, and advanced sentiment analysis
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import Counter
import os
import uvicorn

# Import local modules
try:
    from db.firebase_db import get_firebase_db, FirebaseDB
    from ml.analyzer import DataAnalyzer
    from ml.advanced_sentiment import get_advanced_analyzer, AdvancedSentimentAnalyzer
    from integrations.google_sheets import GoogleSheetsExporter
except ImportError:
    # Fallback for different import contexts
    from .db.firebase_db import get_firebase_db, FirebaseDB
    from .ml.analyzer import DataAnalyzer
    from .ml.advanced_sentiment import get_advanced_analyzer, AdvancedSentimentAnalyzer
    from .integrations.google_sheets import GoogleSheetsExporter

# Security
security = HTTPBearer(auto_error=False)

# API token (set via environment variable or default for development)
API_TOKEN = os.environ.get("FB_SCRAPER_API_TOKEN", "dev-token-change-in-production")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify Bearer token for protected endpoints"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return True


# ==================== Pydantic Models ====================

class PostBase(BaseModel):
    page_name: str
    post_id: str
    post_url: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[datetime] = None
    likes: int = 0
    shares: int = 0
    comment_count: int = 0


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: str
    scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    author_name: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[datetime] = None
    likes: int = 0


class CommentCreate(CommentBase):
    comment_id: Optional[str] = None


class ImageBase(BaseModel):
    image_url: str
    local_path: Optional[str] = None


class AnalysisRequest(BaseModel):
    post_ids: Optional[List[str]] = None
    analysis_types: List[str] = Field(
        default=["sentiment", "topic", "engagement"],
        description="Types of analysis: sentiment, topic, engagement"
    )
    use_advanced: bool = Field(
        default=True,
        description="Use advanced BERT-based sentiment analysis"
    )


class SentimentRequest(BaseModel):
    """Request for single text sentiment analysis"""
    text: str = Field(..., description="Text to analyze")
    language: str = Field(default="en", description="Language code")


class BatchSentimentRequest(BaseModel):
    """Request for batch sentiment analysis"""
    texts: List[str] = Field(..., description="List of texts to analyze")
    language: str = Field(default="en", description="Language code")


class TrendResponse(BaseModel):
    """Response for trending topics"""
    trend: str
    platform: str = "facebook"
    mentions: int
    sentiment: Optional[str] = None


class TopicResponse(BaseModel):
    """Response for popular topics"""
    topic: str
    mentions: int
    platform: str = "facebook"
    avg_engagement: float = 0.0

class AnalysisResponse(BaseModel):
    post_id: str
    analysis_type: str
    result: Dict[str, Any]
    analyzed_at: datetime


class ExportRequest(BaseModel):
    spreadsheet_name: str
    page_filter: Optional[str] = None
    include_analysis: bool = True


class StatsResponse(BaseModel):
    total_posts: int
    total_pages: int
    total_comments: int
    avg_likes: float
    avg_shares: float
    avg_comments: float
    sentiment_distribution: Optional[Dict[str, int]] = None


# ==================== FastAPI App ====================

app = FastAPI(
    title="Facebook Scraper API",
    description="""
API for accessing scraped Facebook data with ML analysis.

## Authentication
Protected endpoints require Bearer token authentication.
Set the `FB_SCRAPER_API_TOKEN` environment variable or use the default dev token.

## Features
- Posts, comments, and images CRUD
- Advanced sentiment analysis with BERT
- Emotion detection and sarcasm detection
- Topic classification
- Trend detection
- Google Sheets export
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Create versioned router
api_v1 = APIRouter(prefix="/api/v1")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
firebase_db: Optional[FirebaseDB] = None
analyzer: Optional[DataAnalyzer] = None
advanced_analyzer: Optional[AdvancedSentimentAnalyzer] = None
sheets_exporter: Optional[GoogleSheetsExporter] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global firebase_db, analyzer, advanced_analyzer, sheets_exporter
    
    try:
        firebase_db = get_firebase_db()
        print("✓ Firebase initialized")
    except Exception as e:
        print(f"⚠ Firebase not initialized: {e}")
    
    try:
        analyzer = DataAnalyzer()
        print("✓ ML Analyzer initialized")
    except Exception as e:
        print(f"⚠ ML Analyzer not initialized: {e}")
    
    try:
        advanced_analyzer = get_advanced_analyzer()
        print("✓ Advanced Sentiment Analyzer initialized")
    except Exception as e:
        print(f"⚠ Advanced Sentiment Analyzer not initialized: {e}")
    
    try:
        sheets_exporter = GoogleSheetsExporter()
        print("✓ Google Sheets exporter initialized")
    except Exception as e:
        print(f"⚠ Google Sheets not initialized: {e}")


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Check API health status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "firebase": firebase_db is not None,
        "analyzer": analyzer is not None,
        "advanced_analyzer": advanced_analyzer is not None,
        "sheets": sheets_exporter is not None
    }


# ==================== New Sentiment Endpoints (v1) ====================

@api_v1.post("/sentiment")
async def analyze_sentiment_text(
    request: SentimentRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Analyze sentiment of a single text using advanced BERT-based analysis.
    
    Returns sentiment label, confidence, emotion detection, and sarcasm detection.
    """
    if advanced_analyzer is None and analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    if advanced_analyzer:
        result = advanced_analyzer.analyze(request.text, request.language)
    else:
        # Fallback to basic analyzer
        posts = [{"post_id": "temp", "content": request.text}]
        results = analyzer.analyze_sentiment(posts)
        result = results.get("temp", {"sentiment": "neutral", "polarity": 0})
    
    return {
        "status": "success",
        "data": result
    }


@api_v1.post("/sentiment/batch")
async def analyze_sentiment_batch(
    request: BatchSentimentRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Analyze sentiment of multiple texts in batch for efficiency.
    """
    if advanced_analyzer is None and analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")
    
    if advanced_analyzer:
        results = advanced_analyzer.analyze_batch(request.texts, request.language)
    else:
        # Fallback to basic analyzer
        posts = [{"post_id": f"temp_{i}", "content": text} for i, text in enumerate(request.texts)]
        analysis = analyzer.analyze_sentiment(posts)
        results = [analysis.get(f"temp_{i}", {}) for i in range(len(request.texts))]
    
    return {
        "status": "success",
        "data": results,
        "count": len(results)
    }


@api_v1.get("/trends", response_model=Dict[str, Any])
async def get_trends(
    platform: Optional[str] = Query(default="facebook", description="Platform filter"),
    limit: int = Query(default=10, le=50, description="Number of trends to return"),
    authenticated: bool = Depends(verify_token)
):
    """
    Get trending topics/hashtags from scraped data.
    
    Analyzes post content to identify frequently mentioned topics and hashtags.
    """
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Get recent posts
    posts = firebase_db.get_all_posts(limit=1000)
    
    if not posts:
        return {"status": "success", "data": []}
    
    # Extract hashtags and keywords
    import re
    hashtags = Counter()
    keywords = Counter()
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
                  'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    for post in posts:
        content = post.get('content', '') or ''
        
        # Find hashtags
        found_hashtags = re.findall(r'#(\w+)', content.lower())
        hashtags.update(found_hashtags)
        
        # Find significant words (5+ chars, not stopwords)
        words = re.findall(r'\b[a-zA-Z]{5,}\b', content.lower())
        meaningful_words = [w for w in words if w not in stop_words]
        keywords.update(meaningful_words)
    
    # Combine and rank trends
    trends = []
    
    # Add top hashtags
    for tag, count in hashtags.most_common(limit // 2):
        trends.append({
            "trend": f"#{tag}",
            "platform": platform,
            "mentions": count,
            "type": "hashtag"
        })
    
    # Add top keywords
    for word, count in keywords.most_common(limit - len(trends)):
        trends.append({
            "trend": word,
            "platform": platform,
            "mentions": count,
            "type": "keyword"
        })
    
    # Sort by mentions
    trends.sort(key=lambda x: x['mentions'], reverse=True)
    
    return {
        "status": "success",
        "data": trends[:limit],
        "total_posts_analyzed": len(posts)
    }


@api_v1.get("/topics")
async def get_popular_topics(
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    platform: Optional[str] = Query(default="facebook", description="Platform filter"),
    limit: int = Query(default=10, le=50),
    authenticated: bool = Depends(verify_token)
):
    """
    Get popular discussion topics from the scraped data.
    
    Uses topic modeling to identify main themes in the content.
    """
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    # Get posts
    posts = firebase_db.get_all_posts(limit=500)
    
    if not posts:
        return {"status": "success", "data": []}
    
    # Filter by date if provided
    if start_date or end_date:
        filtered_posts = []
        for post in posts:
            post_date = post.get('timestamp')
            if post_date:
                if isinstance(post_date, str):
                    try:
                        post_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                    except:
                        continue
                
                if start_date:
                    start = datetime.fromisoformat(start_date)
                    if post_date.replace(tzinfo=None) < start:
                        continue
                
                if end_date:
                    end = datetime.fromisoformat(end_date)
                    if post_date.replace(tzinfo=None) > end:
                        continue
                
                filtered_posts.append(post)
        posts = filtered_posts if filtered_posts else posts
    
    # Use analyzer to classify topics
    try:
        topic_results = analyzer.classify_topics(posts)
        
        # Count topics
        topic_counts = Counter()
        topic_engagement = {}
        
        for post_id, result in topic_results.items():
            topic = result.get('topic', 'unknown')
            topic_counts[topic] += 1
            
            # Track engagement
            if topic not in topic_engagement:
                topic_engagement[topic] = []
            
            # Find post engagement
            for post in posts:
                if post.get('post_id') == post_id:
                    engagement = (post.get('likes', 0) + 
                                 post.get('shares', 0) * 2 + 
                                 post.get('comment_count', 0))
                    topic_engagement[topic].append(engagement)
                    break
        
        # Format response
        topics = []
        for topic, count in topic_counts.most_common(limit):
            avg_eng = sum(topic_engagement.get(topic, [0])) / max(len(topic_engagement.get(topic, [1])), 1)
            topics.append({
                "topic": topic,
                "mentions": count,
                "platform": platform,
                "avg_engagement": round(avg_eng, 2)
            })
        
        return {
            "status": "success",
            "data": topics,
            "total_posts_analyzed": len(posts)
        }
    except Exception as e:
        # Fallback to basic keyword extraction
        return {
            "status": "success",
            "data": [],
            "error": str(e)
        }


# ==================== Posts Endpoints ====================

@app.get("/posts", response_model=List[PostResponse])
@api_v1.get("/posts", response_model=List[PostResponse])
async def get_posts(
    page_name: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get all posts, optionally filtered by page"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if page_name:
        posts = firebase_db.get_posts_by_page(page_name, limit)
    else:
        posts = firebase_db.get_all_posts(limit)
    
    return posts


@app.get("/posts/{post_id}", response_model=PostResponse)
@api_v1.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    """Get a single post by ID"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    post = firebase_db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post


@app.post("/posts", response_model=PostResponse)
async def create_post(post: PostCreate):
    """Create a new post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    post_data = post.model_dump()
    post_id = firebase_db.save_post(post_data)
    
    return firebase_db.get_post(post_id)


@app.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    """Delete a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    success = firebase_db.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or delete failed")
    
    return {"message": "Post deleted successfully"}


# ==================== Comments Endpoints ====================

@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: str):
    """Get all comments for a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    return firebase_db.get_comments_for_post(post_id)


@app.post("/posts/{post_id}/comments")
async def create_comment(post_id: str, comment: CommentCreate):
    """Add a comment to a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    comment_data = comment.model_dump()
    comment_id = firebase_db.save_comment(post_id, comment_data)
    
    return {"comment_id": comment_id, "message": "Comment saved"}


# ==================== Images Endpoints ====================

@app.get("/posts/{post_id}/images")
async def get_images(post_id: str):
    """Get all images for a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    return firebase_db.get_images_for_post(post_id)


@app.post("/posts/{post_id}/images")
async def add_image(post_id: str, image: ImageBase):
    """Add an image to a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    image_data = image.model_dump()
    image_id = firebase_db.save_image(post_id, image_data)
    
    return {"image_id": image_id, "message": "Image saved"}


# ==================== ML Analysis Endpoints ====================

@app.post("/analyze")
async def analyze_posts(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Run ML analysis on posts"""
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Get posts to analyze
    if request.post_ids:
        posts = [firebase_db.get_post(pid) for pid in request.post_ids]
        posts = [p for p in posts if p is not None]
    else:
        posts = firebase_db.get_all_posts(limit=500)
    
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found to analyze")
    
    results = []
    
    for analysis_type in request.analysis_types:
        if analysis_type == "sentiment":
            analysis_results = analyzer.analyze_sentiment(posts)
        elif analysis_type == "topic":
            analysis_results = analyzer.classify_topics(posts)
        elif analysis_type == "engagement":
            analysis_results = analyzer.predict_engagement(posts)
        else:
            continue
        
        # Save results to Firebase
        for post_id, result in analysis_results.items():
            firebase_db.save_analysis_result(post_id, analysis_type, result)
            results.append({
                "post_id": post_id,
                "analysis_type": analysis_type,
                "result": result
            })
    
    return {
        "message": f"Analysis completed for {len(posts)} posts",
        "results_count": len(results),
        "results": results[:50]  # Return first 50 results
    }


@app.get("/analysis/{post_id}")
async def get_analysis(post_id: str, analysis_type: Optional[str] = None):
    """Get analysis results for a post"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    results = firebase_db.get_analysis_results(post_id=post_id, analysis_type=analysis_type)
    return results


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get overall statistics"""
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    posts = firebase_db.get_all_posts(limit=10000)
    
    if not posts:
        return StatsResponse(
            total_posts=0,
            total_pages=0,
            total_comments=0,
            avg_likes=0.0,
            avg_shares=0.0,
            avg_comments=0.0
        )
    
    total_posts = len(posts)
    unique_pages = set(p.get('page_name', '') for p in posts)
    
    total_likes = sum(p.get('likes', 0) for p in posts)
    total_shares = sum(p.get('shares', 0) for p in posts)
    total_comments = sum(p.get('comment_count', 0) for p in posts)
    
    # Get sentiment distribution if available
    sentiment_dist = None
    try:
        analysis_results = firebase_db.get_analysis_results(analysis_type='sentiment')
        if analysis_results:
            sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0}
            for result in analysis_results:
                sentiment = result.get('result', {}).get('sentiment', 'neutral')
                if sentiment in sentiment_dist:
                    sentiment_dist[sentiment] += 1
    except:
        pass
    
    return StatsResponse(
        total_posts=total_posts,
        total_pages=len(unique_pages),
        total_comments=total_comments,
        avg_likes=total_likes / total_posts if total_posts > 0 else 0,
        avg_shares=total_shares / total_posts if total_posts > 0 else 0,
        avg_comments=total_comments / total_posts if total_posts > 0 else 0,
        sentiment_distribution=sentiment_dist
    )


# ==================== Google Sheets Export ====================

@app.post("/export/sheets")
async def export_to_sheets(request: ExportRequest, background_tasks: BackgroundTasks):
    """Export data to Google Sheets"""
    if sheets_exporter is None:
        raise HTTPException(status_code=503, detail="Google Sheets not initialized")
    if firebase_db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Get posts
    if request.page_filter:
        posts = firebase_db.get_posts_by_page(request.page_filter, limit=1000)
    else:
        posts = firebase_db.get_all_posts(limit=1000)
    
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found to export")
    
    # Get analysis results if requested
    analysis_data = None
    if request.include_analysis:
        analysis_data = firebase_db.get_analysis_results()
    
    # Export in background
    try:
        spreadsheet_url = sheets_exporter.export_posts(
            posts, 
            request.spreadsheet_name,
            analysis_data
        )
        
        return {
            "message": "Export successful",
            "spreadsheet_url": spreadsheet_url,
            "posts_exported": len(posts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/export/sheets/list")
async def list_spreadsheets():
    """List all exported spreadsheets"""
    if sheets_exporter is None:
        raise HTTPException(status_code=503, detail="Google Sheets not initialized")
    
    return sheets_exporter.list_spreadsheets()


# ==================== Include Versioned Router ====================

app.include_router(api_v1)


# ==================== Run Server ====================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server(reload=True)
