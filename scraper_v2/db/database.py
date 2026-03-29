"""
Database Manager v2.0
======================
Unified database management supporting multiple backends.

Backends:
- SQLite (default/fallback)
- PostgreSQL (production)
- Firebase (optional cloud sync)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .models import Base, Page, Post, PostComment, ScrapeLog, AnalysisResult

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Unified database manager with multiple backend support.
    
    Features:
    - Automatic table creation
    - Connection pooling
    - Session management
    - Fallback to SQLite if PostgreSQL unavailable
    """
    
    def __init__(self, config=None):
        """
        Initialize DatabaseManager.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        if config is None:
            from config import get_config
            config = get_config()
            
        self.config = config
        self.engine = None
        self.Session = None
        self._firebase = None
        
        # Connect
        self._connect()
        
    def _connect(self):
        """Establish database connection."""
        db_config = self.config.database
        
        # Try PostgreSQL first
        if db_config.postgres_enabled:
            try:
                url = (
                    f"postgresql://{db_config.postgres_user}:{db_config.postgres_password}"
                    f"@{db_config.postgres_host}:{db_config.postgres_port}/{db_config.postgres_database}"
                )
                self.engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=db_config.pool_size,
                    max_overflow=db_config.max_overflow,
                    pool_timeout=db_config.pool_timeout,
                )
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Connected to PostgreSQL database")
                
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}")
                self.engine = None
                
        # Fall back to SQLite
        if self.engine is None and db_config.sqlite_enabled:
            try:
                os.makedirs(os.path.dirname(db_config.sqlite_database) or '.', exist_ok=True)
                url = f"sqlite:///{db_config.sqlite_database}"
                self.engine = create_engine(url, echo=False)
                logger.info(f"Connected to SQLite database: {db_config.sqlite_database}")
            except Exception as e:
                logger.error(f"SQLite connection failed: {e}")
                raise
                
        if self.engine is None:
            raise RuntimeError("No database connection available")
            
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/verified")
        
        # Initialize Firebase if enabled
        if db_config.firebase_enabled:
            self._init_firebase()
            
    def _init_firebase(self):
        """Initialize Firebase connection."""
        try:
            from .firebase_db import FirebaseManager
            self._firebase = FirebaseManager(self.config)
            logger.info("Firebase connection established")
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
            self._firebase = None
            
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
            
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
        
    # =========================================================================
    # PAGE OPERATIONS
    # =========================================================================
    
    def add_page(self, name: str, url: str, **kwargs) -> Optional[Page]:
        """Add a new page to track."""
        with self.session_scope() as session:
            # Check if exists
            existing = session.query(Page).filter_by(url=url).first()
            if existing:
                logger.debug(f"Page already exists: {url}")
                return existing
                
            page = Page(name=name, url=url, **kwargs)
            session.add(page)
            session.flush()
            logger.info(f"Added page: {name}")
            return page
            
    def get_pages(self, active_only: bool = True, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Get all tracked pages as dictionaries."""
        with self.session_scope() as session:
            query = session.query(Page)
            if active_only:
                query = query.filter_by(is_active=True)
            pages = query.offset(offset).limit(limit).all()
            return [self._page_to_dict(p) for p in pages]
    
    def get_page(self, page_id: int) -> Optional[Dict]:
        """Get a single page by ID."""
        with self.session_scope() as session:
            page = session.query(Page).get(page_id)
            return self._page_to_dict(page) if page else None
    
    def _page_to_dict(self, page: Page) -> Dict:
        """Convert Page model to dictionary."""
        return {
            'id': page.id,
            'page_id': page.page_id,
            'name': page.name,
            'url': page.url,
            'category': page.category,
            'followers': page.followers,
            'is_active': page.is_active,
            'last_scraped': page.last_scraped.isoformat() if page.last_scraped else None,
            'scrape_count': page.scrape_count,
            'error_count': page.error_count,
            'created_at': page.created_at.isoformat() if page.created_at else None,
        }
            
    def update_page_scraped(self, page_id: int):
        """Update page's last scraped timestamp."""
        with self.session_scope() as session:
            page = session.query(Page).get(page_id)
            if page:
                page.last_scraped = datetime.utcnow()
                page.scrape_count += 1
                
    # =========================================================================
    # POST OPERATIONS
    # =========================================================================
    
    def add_post(self, post_data: Dict[str, Any]) -> Optional[Post]:
        """Add or update a post."""
        with self.session_scope() as session:
            post_id = post_data.get('post_id')
            if not post_id:
                logger.warning("Post data missing post_id")
                return None
                
            # Check if exists
            existing = session.query(Post).filter_by(post_id=post_id).first()
            if existing:
                # Update existing
                for key, value in post_data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                return existing
                
            # Create new
            post = Post(**{k: v for k, v in post_data.items() if hasattr(Post, k)})
            session.add(post)
            session.flush()
            return post
            
    def get_posts(self, page_id: int = None, limit: int = 100) -> List[Post]:
        """Get posts, optionally filtered by page."""
        with self.session_scope() as session:
            query = session.query(Post)
            if page_id:
                query = query.filter_by(page_id=page_id)
            return query.order_by(Post.scraped_at.desc()).limit(limit).all()
    
    def get_all_posts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all posts as dictionaries."""
        with self.session_scope() as session:
            posts = session.query(Post).order_by(
                Post.scraped_at.desc()
            ).offset(offset).limit(limit).all()
            return [self._post_to_dict(p) for p in posts]
    
    def get_posts_by_page(self, page_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get posts for a specific page as dictionaries."""
        with self.session_scope() as session:
            posts = session.query(Post).filter_by(
                page_id=page_id
            ).order_by(Post.scraped_at.desc()).offset(offset).limit(limit).all()
            return [self._post_to_dict(p) for p in posts]
    
    def _post_to_dict(self, post: Post) -> Dict:
        """Convert Post model to dictionary."""
        return {
            'id': post.id,
            'post_id': post.post_id,
            'page_id': post.page_id,
            'content': post.content,
            'content_type': post.content_type,
            'url': post.url,
            'likes': post.likes,
            'comments_count': post.comments_count,
            'shares': post.shares,
            'reactions': post.reactions,
            'image_urls': post.image_urls,
            'video_url': post.video_url,
            'post_date': post.post_date.isoformat() if post.post_date else None,
            'scraped_at': post.scraped_at.isoformat() if post.scraped_at else None,
            'sentiment_score': post.sentiment_score,
            'sentiment_label': post.sentiment_label,
        }
            
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        """Get a post by its Facebook post ID."""
        with self.session_scope() as session:
            return session.query(Post).filter_by(post_id=post_id).first()
            
    # =========================================================================
    # COMMENT OPERATIONS
    # =========================================================================
    
    def save_comments(self, comments: List[Dict], post_id: str) -> int:
        """
        Save comments for a post.
        Handles deduplication automatically.
        
        Returns:
            Number of new comments saved
        """
        if not comments:
            return 0
            
        saved = 0
        with self.session_scope() as session:
            for comment_data in comments:
                text = comment_data.get('text', '').strip()
                if not text or len(text) < 3:
                    continue
                    
                # Check for duplicate
                existing = session.query(PostComment).filter_by(
                    post_id=post_id, comment_text=text
                ).first()
                
                if existing:
                    continue
                    
                comment = PostComment(
                    post_id=post_id,
                    comment_text=text,
                    author=comment_data.get('author'),
                    author_id=comment_data.get('author_id'),
                    likes=comment_data.get('likes', 0),
                    comment_date=comment_data.get('date'),
                    timestamp=datetime.utcnow()
                )
                session.add(comment)
                saved += 1
                
        logger.info(f"Saved {saved} new comments for post {post_id}")
        
        # Sync to Firebase if enabled
        if self._firebase and comments:
            self._firebase.sync_comments(comments, post_id)
            
        return saved
        
    def get_comments(self, post_id: str) -> List[PostComment]:
        """Get all comments for a post."""
        with self.session_scope() as session:
            return session.query(PostComment).filter_by(post_id=post_id).all()
    
    def get_comments_by_post(self, post_id, limit: int = 500) -> List[Dict]:
        """Get comments for a post as dictionaries."""
        with self.session_scope() as session:
            comments = session.query(PostComment).filter_by(
                post_id=str(post_id)
            ).limit(limit).all()
            return [self._comment_to_dict(c) for c in comments]
    
    def _comment_to_dict(self, comment: PostComment) -> Dict:
        """Convert PostComment model to dictionary."""
        return {
            'id': comment.id,
            'post_id': comment.post_id,
            'comment_id': comment.comment_id,
            'text': comment.comment_text,
            'comment_text': comment.comment_text,
            'author': comment.author,
            'author_id': comment.author_id,
            'likes': comment.likes,
            'reply_count': comment.reply_count,
            'comment_date': comment.comment_date.isoformat() if comment.comment_date else None,
            'timestamp': comment.timestamp.isoformat() if comment.timestamp else None,
            'sentiment_score': comment.sentiment_score,
            'sentiment_label': comment.sentiment_label,
            'parent_comment_id': comment.parent_comment_id,
        }
            
    def get_all_comments(self, limit: int = 1000) -> List[Dict]:
        """Get all comments across all posts as dictionaries."""
        with self.session_scope() as session:
            comments = session.query(PostComment).order_by(
                PostComment.timestamp.desc()
            ).limit(limit).all()
            return [self._comment_to_dict(c) for c in comments]
            
    # =========================================================================
    # LOGGING
    # =========================================================================
    
    def log_operation(self, operation: str, status: str, **kwargs) -> ScrapeLog:
        """Log a scraping operation."""
        with self.session_scope() as session:
            log = ScrapeLog(operation=operation, status=status, **kwargs)
            session.add(log)
            session.flush()
            return log
            
    def update_log(self, log_id: int, **kwargs):
        """Update a log entry."""
        with self.session_scope() as session:
            log = session.query(ScrapeLog).get(log_id)
            if log:
                for key, value in kwargs.items():
                    if hasattr(log, key):
                        setattr(log, key, value)
                        
    # =========================================================================
    # ANALYSIS
    # =========================================================================
    
    def save_analysis(self, analysis_type: str, model_name: str, **kwargs) -> AnalysisResult:
        """Save an analysis result."""
        with self.session_scope() as session:
            result = AnalysisResult(
                analysis_type=analysis_type,
                model_name=model_name,
                **kwargs
            )
            session.add(result)
            session.flush()
            return result
            
    def get_analysis(self, post_id: str = None) -> List[AnalysisResult]:
        """Get analysis results."""
        with self.session_scope() as session:
            query = session.query(AnalysisResult)
            if post_id:
                query = query.filter_by(post_id=post_id)
            return query.all()
            
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.session_scope() as session:
            return {
                'pages': session.query(Page).count(),
                'posts': session.query(Post).count(),
                'comments': session.query(PostComment).count(),
                'analysis_results': session.query(AnalysisResult).count(),
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        stats = self.get_stats()
        stats['database_type'] = 'PostgreSQL' if 'postgresql' in str(self.engine.url) else 'SQLite'
        stats['firebase_enabled'] = self._firebase is not None
        return stats
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def update_post_sentiment(self, post_id: int, sentiment_score: float):
        """Update sentiment score for a post."""
        with self.session_scope() as session:
            post = session.query(Post).get(post_id)
            if post:
                post.sentiment_score = sentiment_score
                if sentiment_score > 0.1:
                    post.sentiment_label = 'positive'
                elif sentiment_score < -0.1:
                    post.sentiment_label = 'negative'
                else:
                    post.sentiment_label = 'neutral'
                post.analyzed_at = datetime.utcnow()
            
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
