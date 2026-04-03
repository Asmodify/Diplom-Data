"""
FastAPI Server Module
RESTful API for accessing Facebook scraper data and ML analysis
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uvicorn

# Import local modules
try:
    from db.firebase_db import get_firebase_db, FirebaseDB
    from ml.analyzer import DataAnalyzer
    from integrations.google_sheets import GoogleSheetsExporter
except ImportError:
    # Fallback for different import contexts
    from .db.firebase_db import get_firebase_db, FirebaseDB
    from .ml.analyzer import DataAnalyzer
    from .integrations.google_sheets import GoogleSheetsExporter


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
    description="API for accessing scraped Facebook data with ML analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
sheets_exporter: Optional[GoogleSheetsExporter] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global firebase_db, analyzer, sheets_exporter
    
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
        "firebase": firebase_db is not None,
        "analyzer": analyzer is not None,
        "sheets": sheets_exporter is not None
    }


# ==================== Posts Endpoints ====================

@app.get("/posts", response_model=List[PostResponse])
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
