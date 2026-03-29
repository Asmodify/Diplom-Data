from sqlalchemy import create_engine, event, Engine, text, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import Optional, List, Any, Dict
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
        # We're using PostgreSQL permanently, but keeping the conditional for code flexibility
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
        self._session_factory = scoped_session(
            sessionmaker(
                bind=self.engine,
                expire_on_commit=False
            )
        )
        self._session = self._session_factory()

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
            
    def save_post(self, post_data, image_data=None, comment_data=None) -> bool:
        """Save a post with optional images and comments to database
        
        Args:
            post_data (dict or FacebookPost): Post data as dictionary or model instance
            image_data (list): List of dictionaries with image data
            comment_data (list): List of dictionaries with comment data
        """
        try:
            with self.session_scope() as session:
                # Convert dictionary to model if needed
                if isinstance(post_data, dict):
                    post_id = post_data.get('post_id')
                    # Check if post already exists
                    existing_post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                    
                    if existing_post:
                        logger.info(f"Post {post_id} already exists, updating")
                        # Update existing post with new values
                        for key, value in post_data.items():
                            if hasattr(existing_post, key) and value is not None:
                                setattr(existing_post, key, value)
                        post = existing_post
                    else:
                        # Create new post model
                        post = FacebookPost(
                            post_id=post_id,
                            page_name=post_data.get('page_name'),
                            post_url=post_data.get('post_url'),
                            post_text=post_data.get('post_text'),
                            post_time=post_data.get('post_time'),
                            author=post_data.get('author'),
                            likes=post_data.get('likes', 0),
                            shares=post_data.get('shares', 0),
                            comments_count=post_data.get('comments_count', 0),
                            screenshot_path=post_data.get('screenshot_path'),
                            extracted_at=post_data.get('extracted_at')
                        )
                        session.add(post)
                else:
                    # Already a model instance
                    post = post_data
                    post_id = post.post_id
                    
                    # Check if post already exists
                    existing_post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                    if existing_post:
                        # Update existing post
                        for key, value in post.__dict__.items():
                            if key != '_sa_instance_state' and value is not None:
                                setattr(existing_post, key, value)
                        post = existing_post
                    else:
                        session.add(post)
                
                session.flush()  # Flush to get post ID

                # Add images if provided
                if image_data:
                    for img_data in image_data:
                        if isinstance(img_data, dict):
                            # Check if image already exists
                            existing_img = session.query(PostImage).filter_by(
                                post_id=post_id,
                                original_url=img_data.get('original_url')
                            ).first()
                            
                            if not existing_img:
                                # Create model from dictionary
                                img = PostImage(
                                    post_id=post_id,
                                    original_url=img_data.get('original_url'),
                                    local_path=img_data.get('local_path'),
                                    filename=img_data.get('filename'),
                                    downloaded_at=img_data.get('downloaded_at')
                                )
                                session.add(img)
                        else:
                            # Already a model instance
                            if img_data.post_id != post_id:
                                img_data.post_id = post_id
                            
                            # Check if image already exists
                            existing_img = session.query(PostImage).filter_by(
                                post_id=post_id,
                                original_url=img_data.original_url
                            ).first()
                            
                            if not existing_img:
                                session.add(img_data)

                # Add comments if provided
                if comment_data:
                    for cmt_data in comment_data:
                        if isinstance(cmt_data, dict):
                            # Check if comment already exists by text and author
                            existing_comment = session.query(PostComment).filter_by(
                                post_id=post_id,
                                author=cmt_data.get('author'),
                                text=cmt_data.get('text')
                            ).first()
                            
                            if not existing_comment:
                                # Create model from dictionary
                                comment = PostComment(
                                    post_id=post_id,
                                    author=cmt_data.get('author'),
                                    text=cmt_data.get('text'),
                                    comment_time=cmt_data.get('comment_time'),
                                    likes=cmt_data.get('likes', 0),
                                    extracted_at=cmt_data.get('extracted_at')
                                )
                                session.add(comment)
                        else:
                            # Already a model instance
                            if cmt_data.post_id != post_id:
                                cmt_data.post_id = post_id
                            
                            # Check if comment already exists
                            existing_comment = session.query(PostComment).filter_by(
                                post_id=post_id,
                                author=cmt_data.author,
                                text=cmt_data.text
                            ).first()
                            
                            if not existing_comment:
                                session.add(cmt_data)

            image_count = len(image_data) if image_data else 0
            comment_count = len(comment_data) if comment_data else 0
            logger.info(f"Saved post {post_id} with {image_count} images and {comment_count} comments")
            return True
        except Exception as e:
            post_id = post_data.get('post_id') if isinstance(post_data, dict) else getattr(post_data, 'post_id', 'unknown') 
            logger.error(f"Error saving post {post_id}: {e}")
            return False

    def save_posts(self, posts_data: List[Any]) -> bool:
        """Save multiple posts with their images and comments
        
        Args:
            posts_data: List of dictionaries, each containing 'post', 'images', and 'comments' keys,
                       or just post dictionaries themselves
        """
        success_count = 0
        for post_item in posts_data:
            if post_item:
                # Check if this is a structured dict with post/images/comments keys
                if isinstance(post_item, dict) and 'post' in post_item:
                    post = post_item.get('post')
                    images = post_item.get('images', [])
                    comments = post_item.get('comments', [])
                else:
                    # The post_item is the post data itself
                    post = post_item
                    images = []
                    comments = []
                
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
            # For PostgreSQL (since we're using it permanently)
            with self.engine.connect() as connection:
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

    def remove_duplicates(self) -> dict:
        """
        Remove duplicate comments, post pictures, and screenshots.
        A duplicate comment is defined as having the same post_id, author, and text.
        A duplicate image is defined as having the same image_url or file_path.
        
        Returns:
            dict: Count of duplicates removed for each type
        """
        stats = {
            'comments': 0,
            'images': 0,
            'screenshots': 0
        }
        
        try:
            with self.session_scope() as session:
                # 1. Remove duplicate comments
                # Get all comments grouped by post_id, author, and text, keeping only the first one
                subquery = session.query(
                    PostComment.post_id,
                    PostComment.author,
                    PostComment.text,
                    func.min(PostComment.id).label('min_id')
                ).group_by(
                    PostComment.post_id,
                    PostComment.author,
                    PostComment.text
                ).subquery()
                
                # Delete comments that aren't the first occurrence
                deleted_comments = session.query(PostComment).filter(
                    ~PostComment.id.in_(
                        session.query(subquery.c.min_id)
                    )
                ).delete(synchronize_session=False)
                
                stats['comments'] = deleted_comments
                
                # 2. Remove duplicate images
                # First, get duplicate image URLs
                subquery = session.query(
                    PostImage.post_id,
                    PostImage.image_url,
                    func.min(PostImage.id).label('min_id')
                ).filter(PostImage.image_url.isnot(None)).group_by(
                    PostImage.post_id,
                    PostImage.image_url
                ).subquery()
                
                # Delete duplicate images by URL
                deleted_images = session.query(PostImage).filter(
                    PostImage.image_url.isnot(None),
                    ~PostImage.id.in_(
                        session.query(subquery.c.min_id)
                    )
                ).delete(synchronize_session=False)
                
                stats['images'] = deleted_images
                
                # 3. Remove duplicate screenshots
                # First, get duplicate screenshot paths
                subquery = session.query(
                    PostImage.post_id,
                    PostImage.file_path,
                    func.min(PostImage.id).label('min_id')
                ).filter(
                    PostImage.file_path.isnot(None),
                    PostImage.is_screenshot.is_(True)
                ).group_by(
                    PostImage.post_id,
                    PostImage.file_path
                ).subquery()
                
                # Delete duplicate screenshots
                deleted_screenshots = session.query(PostImage).filter(
                    PostImage.file_path.isnot(None),
                    PostImage.is_screenshot.is_(True),
                    ~PostImage.id.in_(
                        session.query(subquery.c.min_id)
                    )
                ).delete(synchronize_session=False)
                
                stats['screenshots'] = deleted_screenshots
                
                # Commit all changes
                session.commit()
                
                logger.info(f"Removed {stats['comments']} duplicate comments")
                logger.info(f"Removed {stats['images']} duplicate post images")
                logger.info(f"Removed {stats['screenshots']} duplicate screenshots")
                
                return stats
                
        except SQLAlchemyError as e:
            logger.error(f"Error removing duplicates: {e}")
            return stats

    @property
    def session(self):
        return self._session

# Add event listeners for query performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = datetime.now()
    logger.debug(f"Starting query: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = datetime.now() - context._query_start_time
    logger.debug(f"Query completed in {total_time.total_seconds():.3f}s")
