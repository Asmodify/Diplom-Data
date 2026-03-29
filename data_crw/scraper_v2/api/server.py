"""
FastAPI Server v2.0
===================
REST API for Facebook Scraper with authentication.

Features:
- Bearer token authentication
- Scraping endpoints
- Analysis endpoints
- Database management
- Export functionality
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
from functools import wraps
import threading

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic Models
# ==============================================================================

class ScrapeRequest(BaseModel):
    """Request model for scraping."""
    page_url: str = Field(..., description="Facebook page URL")
    max_posts: int = Field(10, ge=1, le=100, description="Max posts to scrape")
    include_comments: bool = Field(True, description="Include comments")
    max_comments: int = Field(50, ge=1, le=500, description="Max comments per post")
    
    
class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping."""
    page_urls: List[str] = Field(..., description="List of page URLs")
    max_posts: int = Field(10, ge=1, le=100)
    include_comments: bool = Field(True)
    
    
class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    text: str = Field(..., description="Text to analyze")
    method: str = Field("textblob", description="Analysis method")
    
    
class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""
    texts: List[str] = Field(..., description="Texts to analyze")
    method: str = Field("textblob")


class ScrapeResult(BaseModel):
    """Model for scrape results."""
    success: bool
    message: str
    page_url: Optional[str] = None
    posts_count: int = 0
    comments_count: int = 0
    duration_seconds: float = 0.0
    
    
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    services: Dict[str, bool]
    
    
class PageInfo(BaseModel):
    """Page information model."""
    id: int
    url: str
    name: Optional[str]
    created_at: Optional[str]
    post_count: int
    
    
class PostInfo(BaseModel):
    """Post information model."""
    id: int
    page_id: int
    text: Optional[str]
    likes: int
    comments_count: int
    created_at: Optional[str]
    sentiment_score: Optional[float]


# ==============================================================================
# Security
# ==============================================================================

security = HTTPBearer()

def get_api_key():
    """Get API key from config."""
    try:
        from config import get_config
        config = get_config()
        return config.api.api_key
    except Exception:
        return "default-api-key"


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Bearer token."""
    api_key = get_api_key()
    if credentials.credentials != api_key:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials


# ==============================================================================
# Background Tasks State
# ==============================================================================

class ScraperState:
    """Global state for scraper."""
    def __init__(self):
        self.scraper = None
        self.is_running = False
        self.current_task = None
        self.last_result = None
        self.lock = threading.Lock()
        
    def get_scraper(self):
        """Get or create scraper instance."""
        with self.lock:
            if self.scraper is None:
                try:
                    from core.scraper import Scraper
                    from db.database import DatabaseManager
                    
                    db = DatabaseManager()
                    self.scraper = Scraper(db)
                except Exception as e:
                    logger.error(f"Failed to create scraper: {e}")
                    raise HTTPException(500, f"Scraper initialization failed: {e}")
            return self.scraper


scraper_state = ScraperState()


# ==============================================================================
# FastAPI App
# ==============================================================================

def create_app(title: str = "Facebook Scraper API", version: str = "2.0.0") -> FastAPI:
    """Create FastAPI application."""
    
    app = FastAPI(
        title=title,
        version=version,
        description="REST API for Facebook page scraping and analysis",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app: FastAPI):
    """Register all API routes."""
    
    # --------------------------------------------------------------------------
    # Health & Info
    # --------------------------------------------------------------------------
    
    @app.get("/", tags=["Info"])
    async def root():
        """Root endpoint."""
        return {
            "name": "Facebook Scraper API",
            "version": "2.0.0",
            "docs": "/docs",
        }
        
    @app.get("/health", response_model=HealthResponse, tags=["Info"])
    async def health_check():
        """Health check endpoint."""
        services = {
            'api': True,
            'database': False,
            'scraper': False,
        }
        
        # Check database
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            services['database'] = db.is_connected
        except Exception:
            pass
            
        # Check scraper state
        services['scraper'] = scraper_state.scraper is not None or not scraper_state.is_running
        
        return HealthResponse(
            status="healthy" if all(services.values()) else "degraded",
            version="2.0.0",
            timestamp=datetime.now().isoformat(),
            services=services,
        )
        
    @app.get("/api/v1/status", tags=["Info"], dependencies=[Depends(verify_token)])
    async def api_status():
        """Get API status."""
        return {
            "status": "running",
            "scraper_active": scraper_state.is_running,
            "last_result": scraper_state.last_result,
        }
        
    # --------------------------------------------------------------------------
    # Scraping Endpoints
    # --------------------------------------------------------------------------
    
    @app.post("/api/v1/scrape", tags=["Scraping"], dependencies=[Depends(verify_token)])
    async def scrape_page(request: ScrapeRequest, background_tasks: BackgroundTasks):
        """
        Start scraping a Facebook page.
        
        Runs in background and returns task ID.
        """
        if scraper_state.is_running:
            raise HTTPException(409, "A scraping task is already running")
            
        # Start background task
        background_tasks.add_task(
            run_scrape_task,
            request.page_url,
            request.max_posts,
            request.include_comments,
            request.max_comments,
        )
        
        return {
            "status": "started",
            "message": f"Scraping started for {request.page_url}",
            "page_url": request.page_url,
        }
        
    @app.post("/api/v1/scrape/batch", tags=["Scraping"], dependencies=[Depends(verify_token)])
    async def scrape_pages_batch(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
        """Start batch scraping multiple pages."""
        if scraper_state.is_running:
            raise HTTPException(409, "A scraping task is already running")
            
        background_tasks.add_task(
            run_batch_scrape_task,
            request.page_urls,
            request.max_posts,
            request.include_comments,
        )
        
        return {
            "status": "started",
            "message": f"Batch scraping started for {len(request.page_urls)} pages",
            "pages": request.page_urls,
        }
        
    @app.post("/api/v1/scrape/stop", tags=["Scraping"], dependencies=[Depends(verify_token)])
    async def stop_scraping():
        """Stop current scraping task."""
        if not scraper_state.is_running:
            return {"status": "not_running", "message": "No scraping task is running"}
            
        try:
            if scraper_state.scraper:
                scraper_state.scraper.stop()
            scraper_state.is_running = False
            return {"status": "stopped", "message": "Scraping stopped"}
        except Exception as e:
            raise HTTPException(500, f"Failed to stop: {e}")
            
    @app.get("/api/v1/scrape/result", tags=["Scraping"], dependencies=[Depends(verify_token)])
    async def get_scrape_result():
        """Get last scraping result."""
        return {
            "is_running": scraper_state.is_running,
            "result": scraper_state.last_result,
        }
        
    # --------------------------------------------------------------------------
    # Data Endpoints
    # --------------------------------------------------------------------------
    
    @app.get("/api/v1/pages", tags=["Data"], dependencies=[Depends(verify_token)])
    async def get_pages(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        """Get all scraped pages."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            pages = db.get_pages(limit=limit, offset=offset)
            return {
                "count": len(pages),
                "pages": pages,
            }
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
            
    @app.get("/api/v1/pages/{page_id}", tags=["Data"], dependencies=[Depends(verify_token)])
    async def get_page(page_id: int):
        """Get page by ID."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            page = db.get_page(page_id)
            if not page:
                raise HTTPException(404, "Page not found")
            return page
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
            
    @app.get("/api/v1/pages/{page_id}/posts", tags=["Data"], dependencies=[Depends(verify_token)])
    async def get_page_posts(
        page_id: int,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        """Get posts for a page."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            posts = db.get_posts_by_page(page_id, limit=limit, offset=offset)
            return {
                "page_id": page_id,
                "count": len(posts),
                "posts": posts,
            }
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
            
    @app.get("/api/v1/posts/{post_id}/comments", tags=["Data"], dependencies=[Depends(verify_token)])
    async def get_post_comments(
        post_id: int,
        limit: int = Query(500, ge=1, le=5000),
    ):
        """Get comments for a post."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            comments = db.get_comments_by_post(post_id, limit=limit)
            return {
                "post_id": post_id,
                "count": len(comments),
                "comments": comments,
            }
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
            
    # --------------------------------------------------------------------------
    # Analysis Endpoints
    # --------------------------------------------------------------------------
    
    @app.post("/api/v1/analyze", tags=["Analysis"], dependencies=[Depends(verify_token)])
    async def analyze_text(request: AnalysisRequest):
        """Analyze sentiment of text."""
        try:
            from ml.analyzer import DataAnalyzer
            analyzer = DataAnalyzer()
            result = analyzer.analyze_sentiment(request.text, method=request.method)
            return result
        except Exception as e:
            raise HTTPException(500, f"Analysis error: {e}")
            
    @app.post("/api/v1/analyze/batch", tags=["Analysis"], dependencies=[Depends(verify_token)])
    async def analyze_batch(request: BatchAnalysisRequest):
        """Batch analyze texts."""
        try:
            from ml.analyzer import DataAnalyzer
            analyzer = DataAnalyzer()
            results = analyzer.analyze_batch(request.texts, method=request.method)
            return {
                "count": len(results),
                "results": results,
            }
        except Exception as e:
            raise HTTPException(500, f"Analysis error: {e}")
            
    @app.post("/api/v1/analyze/advanced", tags=["Analysis"], dependencies=[Depends(verify_token)])
    async def analyze_advanced(request: AnalysisRequest):
        """Advanced BERT-based analysis."""
        try:
            from ml.advanced_sentiment import AdvancedSentimentAnalyzer
            analyzer = AdvancedSentimentAnalyzer()
            result = analyzer.analyze(request.text)
            return result
        except Exception as e:
            raise HTTPException(500, f"Analysis error: {e}")
            
    @app.post("/api/v1/analyze/comments/{post_id}", tags=["Analysis"], dependencies=[Depends(verify_token)])
    async def analyze_post_comments(post_id: int):
        """Analyze all comments for a post."""
        try:
            from db.database import DatabaseManager
            from ml.analyzer import DataAnalyzer
            
            db = DatabaseManager()
            comments = db.get_comments_by_post(post_id)
            
            if not comments:
                raise HTTPException(404, "No comments found")
                
            analyzer = DataAnalyzer()
            result = analyzer.analyze_comments(comments)
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Analysis error: {e}")
            
    @app.post("/api/v1/analyze/ai", tags=["Analysis"], dependencies=[Depends(verify_token)])
    async def ai_comprehensive_analysis(
        limit: int = Query(100, ge=1, le=1000, description="Max posts to analyze"),
    ):
        """
        AI-powered comprehensive analysis of all scraped data.
        
        Returns:
        - Sentiment analysis with trends
        - Topic clustering with TF-IDF
        - Engagement metrics analysis
        - Temporal patterns
        - Audience insights
        - AI-generated recommendations
        """
        try:
            from db.database import DatabaseManager
            from ml.ai_analyzer import AIAnalyzer
            
            db = DatabaseManager()
            ai = AIAnalyzer()
            
            # Get data
            posts = db.get_all_posts(limit=limit)
            all_comments = []
            for post in posts:
                post_id = post.get('post_id') or post.get('id')
                comments = db.get_comments_by_post(post_id, limit=100)
                if comments:
                    all_comments.extend(comments)
            
            if not posts:
                raise HTTPException(404, "No data to analyze")
            
            # Run comprehensive analysis
            analysis = ai.analyze_all(posts, all_comments)
            
            return {
                "status": "success",
                "analysis": analysis,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI analysis error: {e}", exc_info=True)
            raise HTTPException(500, f"AI analysis error: {e}")
            
    # --------------------------------------------------------------------------
    # Export Endpoints
    # --------------------------------------------------------------------------
    
    @app.get("/api/v1/export/pages", tags=["Export"], dependencies=[Depends(verify_token)])
    async def export_pages(format: str = Query("json", enum=["json", "csv"])):
        """Export all pages."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            pages = db.get_pages(limit=10000)
            
            if format == "csv":
                # Return CSV format
                import io
                import csv
                output = io.StringIO()
                if pages:
                    writer = csv.DictWriter(output, fieldnames=pages[0].keys())
                    writer.writeheader()
                    writer.writerows(pages)
                return {
                    "format": "csv",
                    "data": output.getvalue(),
                }
            return {
                "format": "json",
                "count": len(pages),
                "data": pages,
            }
        except Exception as e:
            raise HTTPException(500, f"Export error: {e}")
            
    @app.get("/api/v1/export/posts/{page_id}", tags=["Export"], dependencies=[Depends(verify_token)])
    async def export_posts(page_id: int, format: str = Query("json", enum=["json", "csv"])):
        """Export posts for a page."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            posts = db.get_posts_by_page(page_id, limit=10000)
            
            return {
                "format": format,
                "page_id": page_id,
                "count": len(posts),
                "data": posts,
            }
        except Exception as e:
            raise HTTPException(500, f"Export error: {e}")
            
    # --------------------------------------------------------------------------
    # Statistics Endpoints
    # --------------------------------------------------------------------------
    
    @app.get("/api/v1/stats", tags=["Statistics"], dependencies=[Depends(verify_token)])
    async def get_statistics():
        """Get overall statistics."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            stats = db.get_statistics()
            return stats
        except Exception as e:
            raise HTTPException(500, f"Statistics error: {e}")
            
    @app.get("/api/v1/stats/page/{page_id}", tags=["Statistics"], dependencies=[Depends(verify_token)])
    async def get_page_statistics(page_id: int):
        """Get statistics for a specific page."""
        try:
            from db.database import DatabaseManager
            db = DatabaseManager()
            stats = db.get_page_statistics(page_id)
            if not stats:
                raise HTTPException(404, "Page not found")
            return stats
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Statistics error: {e}")


def run_scrape_task(
    page_url: str,
    max_posts: int,
    include_comments: bool,
    max_comments: int,
):
    """Background scraping task."""
    import time
    start_time = time.time()
    
    scraper_state.is_running = True
    
    try:
        scraper = scraper_state.get_scraper()
        result = scraper.scrape_page(
            page_url,
            max_posts=max_posts,
            scrape_comments=include_comments,
            max_comments=max_comments,
        )
        
        duration = time.time() - start_time
        scraper_state.last_result = {
            "success": True,
            "page_url": page_url,
            "posts_count": result.get('posts_scraped', 0) if result else 0,
            "comments_count": result.get('comments_scraped', 0) if result else 0,
            "duration_seconds": duration,
            "completed_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        scraper_state.last_result = {
            "success": False,
            "page_url": page_url,
            "error": str(e),
            "duration_seconds": time.time() - start_time,
        }
    finally:
        scraper_state.is_running = False


def run_batch_scrape_task(
    page_urls: List[str],
    max_posts: int,
    include_comments: bool,
):
    """Background batch scraping task."""
    import time
    start_time = time.time()
    
    scraper_state.is_running = True
    results = []
    
    try:
        scraper = scraper_state.get_scraper()
        
        for url in page_urls:
            try:
                result = scraper.scrape_page(url, max_posts=max_posts, scrape_comments=include_comments)
                results.append({"url": url, "success": True, "result": result})
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})
                
        scraper_state.last_result = {
            "success": True,
            "pages_processed": len(page_urls),
            "successful": len([r for r in results if r['success']]),
            "failed": len([r for r in results if not r['success']]),
            "results": results,
            "duration_seconds": time.time() - start_time,
            "completed_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Batch scraping failed: {e}")
        scraper_state.last_result = {
            "success": False,
            "error": str(e),
            "duration_seconds": time.time() - start_time,
        }
    finally:
        scraper_state.is_running = False


# Create default app instance
app = create_app()


# ==============================================================================
# Main Entry
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    try:
        from config import get_config
        config = get_config()
        host = config.api.host
        port = config.api.port
    except Exception:
        host = "0.0.0.0"
        port = 8000
        
    uvicorn.run(app, host=host, port=port, reload=True)
