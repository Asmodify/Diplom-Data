from sqlalchemy import create_engine, event, Engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import Optional, List, Any
from contextlib import contextmanager
import logging

from .config import get_database_url, USE_SQLITE
from .models import Base, FacebookPost, PostImage, PostComment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # SQLite doesn't support all the connection pool options
        if USE_SQLITE:
            self.engine = create_engine(
                get_database_url(),
                connect_args={"check_same_thread": False}
            )
        else:
            self.engine = create_engine(
                get_database_url(),
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
        
        # Create session factory
        self.Session = scoped_session(
            sessionmaker(
                bind=self.engine,
                expire_on_commit=False
            )
        )

    def init_db(self) -> None:
        """Initialize database tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def save_post(self, post, images=None, comments=None) -> bool:
        """Save a post with optional images and comments to database"""
        try:
            with self.session_scope() as session:
                # Check if post already exists
                existing_post = session.query(FacebookPost).filter_by(post_id=post.post_id).first()
                
                if existing_post:
                    logger.info(f"Post {post.post_id} already exists, updating")
                    # Update existing post
                    for key, value in post.__dict__.items():
                        if key != '_sa_instance_state' and value is not None:
                            setattr(existing_post, key, value)
                    post = existing_post
                else:
                    # Add new post
                    session.add(post)
                    session.flush()  # Flush to get post ID

                # Add images if provided
                if images:
                    for image_data in images:
                        # Check if image already exists
                        existing_img = session.query(PostImage).filter_by(
                            post_id=post.post_id,
                            original_url=image_data.original_url
                        ).first()
                        
                        if not existing_img:
                            image_data.post_id = post.post_id
                            session.add(image_data)

                # Add comments if provided
                if comments:
                    for comment_data in comments:
                        # Check if comment already exists by text and author
                        existing_comment = session.query(PostComment).filter_by(
                            post_id=post.post_id,
                            author=comment_data.author,
                            text=comment_data.text
                        ).first()
                        
                        if not existing_comment:
                            comment_data.post_id = post.post_id
                            session.add(comment_data)

            logger.info(f"Saved post {post.post_id} with {len(images) if images else 0} images and {len(comments) if comments else 0} comments")
            return True
        except Exception as e:
            logger.error(f"Error saving post {post.post_id if post else 'unknown'}: {e}")
            return False

    def save_posts(self, posts_data: List[Any]) -> bool:
        """Save multiple posts with their images and comments"""
        success_count = 0
        for post_data in posts_data:
            if post_data:
                post = post_data.get('post')
                images = post_data.get('images', [])
                comments = post_data.get('comments', [])
                
                if self.save_post(post, images, comments):
                    success_count += 1
        
        logger.info(f"Saved {success_count} out of {len(posts_data)} posts")
        return success_count > 0

    def get_latest_posts(self, limit: int = 10) -> List[FacebookPost]:
        """Get the latest posts from the database"""
        try:
            with self.session_scope() as session:
                latest_posts = session.query(FacebookPost).order_by(
                    FacebookPost.extracted_at.desc()
                ).limit(limit).all()
                
                return latest_posts
        except Exception as e:
            logger.error(f"Error getting latest posts: {e}")
            return []

    def get_posts_by_page(self, page_name: str) -> List[FacebookPost]:
        """Get all posts for a specific page"""
        try:
            with self.session_scope() as session:
                posts = session.query(FacebookPost).filter_by(
                    page_name=page_name
                ).order_by(FacebookPost.post_time.desc()).all()
                
                return posts
        except Exception as e:
            logger.error(f"Error getting posts for page {page_name}: {e}")
            return []

    def cleanup_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with self.session_scope() as session:
                deleted_count = session.query(FacebookPost).filter(
                    FacebookPost.extracted_at < cutoff_date
                ).delete()
                
                logger.info(f"Deleted {deleted_count} old records")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0

    def health_check(self) -> bool:
        """Check if database is accessible and tables exist"""
        try:
            # For SQLite, just check if we can connect and query tables
            with self.engine.connect() as connection:
                if USE_SQLITE:
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = [row[0] for row in result]
                    
                    required_tables = ['facebook_posts', 'post_images', 'post_comments']
                    missing_tables = [table for table in required_tables if table not in tables]
                    
                    if missing_tables:
                        logger.warning(f"Missing tables: {missing_tables}")
                        return False
                    else:
                        logger.info(f"Database health check passed. Tables present: {tables}")
                        return True
                else:
                    # For PostgreSQL
                    result = connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
                    tables = [row[0] for row in result]
                    
                    required_tables = ['facebook_posts', 'post_images', 'post_comments']
                    missing_tables = [table for table in required_tables if table not in tables]
                    
                    if missing_tables:
                        logger.warning(f"Missing tables: {missing_tables}")
                        return False
                    else:
                        logger.info(f"Database health check passed. Tables present: {tables}")
                        return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Add event listeners for query performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = datetime.now()
    logger.debug(f"Starting query: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = datetime.now() - context._query_start_time
    logger.debug(f"Query completed in {total_time.total_seconds():.3f}s")
