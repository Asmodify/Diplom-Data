from sqlalchemy import create_engine, event, Engine, text, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import Optional, List, Any, Dict
from contextlib import contextmanager
import logging
import json

from .config import get_database_url, USE_SQLITE
from .models import Base, FacebookPost, PostImage, PostComment, AnalysisResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== HELPER CONVERTERS ====================

def post_to_dict(post: FacebookPost) -> Dict[str, Any]:
    if not post:
        return {}
    return {
        "id": post.post_id,
        "post_id": post.post_id,
        "page_name": post.page_name,
        "post_url": post.post_url,
        "content": post.content,
        "timestamp": post.timestamp,
        "likes": post.likes,
        "shares": post.shares,
        "comment_count": post.comment_count,
        "scraped_at": post.scraped_at
    }

def comment_to_dict(cmt: PostComment) -> Dict[str, Any]:
    if not cmt:
        return {}
    return {
        "id": cmt.comment_id,
        "comment_id": cmt.comment_id,
        "author_name": cmt.author_name,
        "author_url": cmt.author_url,
        "content": cmt.content,
        "timestamp": cmt.timestamp,
        "likes": cmt.likes,
        "reply_to_id": cmt.reply_to_id,
        "scraped_at": cmt.scraped_at
    }

def image_to_dict(img: PostImage) -> Dict[str, Any]:
    if not img:
        return {}
    return {
        "id": str(img.id),
        "image_url": img.image_url,
        "local_path": img.local_path,
        "downloaded_at": img.downloaded_at
    }

def analysis_to_dict(analysis: AnalysisResult) -> Dict[str, Any]:
    if not analysis:
        return {}
    try:
        res = json.loads(analysis.result)
    except Exception:
        res = analysis.result
    return {
        "id": f"{analysis.post_id}_{analysis.analysis_type}",
        "post_id": analysis.post_id,
        "analysis_type": analysis.analysis_type,
        "result": res,
        "analyzed_at": analysis.analyzed_at
    }

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
        self.Session = scoped_session(
            sessionmaker(
                bind=self.engine,
                expire_on_commit=False
            )
        )
        self._session = self.Session()

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
                        # Map keys to model attributes
                        mapped_data = {
                            'page_name': post_data.get('page_name'),
                            'post_url': post_data.get('post_url'),
                            'content': post_data.get('content') or post_data.get('post_text'),
                            'timestamp': post_data.get('timestamp') or post_data.get('post_time'),
                            'likes': post_data.get('likes'),
                            'shares': post_data.get('shares'),
                            'comment_count': post_data.get('comment_count') or post_data.get('comments_count')
                        }
                        for key, value in mapped_data.items():
                            if value is not None:
                                setattr(existing_post, key, value)
                        post = existing_post
                    else:
                        # Create new post model
                        ts = post_data.get('timestamp') or post_data.get('post_time')
                        if isinstance(ts, str):
                            try:
                                ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                            except:
                                ts = datetime.utcnow()
                        elif not ts:
                            ts = datetime.utcnow()

                        post = FacebookPost(
                            post_id=post_id,
                            page_name=post_data.get('page_name', 'unknown'),
                            post_url=post_data.get('post_url'),
                            content=post_data.get('content') or post_data.get('post_text'),
                            timestamp=ts,
                            likes=post_data.get('likes', 0),
                            shares=post_data.get('shares', 0),
                            comment_count=post_data.get('comment_count') or post_data.get('comments_count', 0),
                            scraped_at=datetime.utcnow()
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
                            if key != '_sa_instance_state' and value is not None and hasattr(existing_post, key):
                                setattr(existing_post, key, value)
                        post = existing_post
                    else:
                        session.add(post)
                
                session.flush()  # Flush to get post ID (post.id)

                # Add images if provided
                if image_data:
                    for img_data in image_data:
                        if isinstance(img_data, dict):
                            img_url = img_data.get('image_url') or img_data.get('original_url')
                            # Check if image already exists for this post
                            existing_img = session.query(PostImage).filter_by(
                                post_id=post.id,
                                image_url=img_url
                            ).first()
                            
                            if not existing_img:
                                # Create model from dictionary
                                img = PostImage(
                                    post_id=post.id,
                                    image_url=img_url,
                                    local_path=img_data.get('local_path') or img_data.get('filename'),
                                    downloaded_at=img_data.get('downloaded_at') or datetime.utcnow()
                                )
                                session.add(img)
                        else:
                            # Already a model instance
                            if img_data.post_id != post.id:
                                img_data.post_id = post.id
                            
                            # Check if image already exists
                            existing_img = session.query(PostImage).filter_by(
                                post_id=post.id,
                                image_url=img_data.image_url
                            ).first()
                            
                            if not existing_img:
                                session.add(img_data)

                # Add comments if provided
                if comment_data:
                    for cmt_data in comment_data:
                        if isinstance(cmt_data, dict):
                            comment_id = cmt_data.get('comment_id')
                            author_name = cmt_data.get('author_name') or cmt_data.get('author')
                            content = cmt_data.get('content') or cmt_data.get('text')
                            # Check if comment already exists by comment_id or by author/content
                            existing_comment = None
                            if comment_id:
                                existing_comment = session.query(PostComment).filter_by(
                                    post_id=post.id,
                                    comment_id=comment_id
                                ).first()
                            if not existing_comment:
                                existing_comment = session.query(PostComment).filter_by(
                                    post_id=post.id,
                                    author_name=author_name,
                                    content=content
                                ).first()
                            
                            if not existing_comment:
                                ts = cmt_data.get('timestamp') or cmt_data.get('comment_time')
                                if isinstance(ts, str):
                                    try:
                                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                                    except:
                                        ts = datetime.utcnow()
                                elif not ts:
                                    ts = datetime.utcnow()

                                # Create model from dictionary
                                comment = PostComment(
                                    post_id=post.id,
                                    comment_id=comment_id,
                                    author_name=author_name,
                                    author_url=cmt_data.get('author_url'),
                                    content=content,
                                    timestamp=ts,
                                    likes=cmt_data.get('likes', 0),
                                    scraped_at=cmt_data.get('scraped_at') or datetime.utcnow()
                                )
                                session.add(comment)
                        else:
                            # Already a model instance
                            if cmt_data.post_id != post.id:
                                cmt_data.post_id = post.id
                            
                            # Check if comment already exists
                            existing_comment = session.query(PostComment).filter_by(
                                post_id=post.id,
                                comment_id=cmt_data.comment_id
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

    def query(self, *args, **kwargs):
        """Delegate query to the SQLAlchemy session for backward compatibility in tests"""
        return self._session.query(*args, **kwargs)

    # ==================== COMPATIBILITY METHODS FOR FIREBASE_DB ====================

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a single post by post_id as a dictionary"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if post:
                    return post_to_dict(post)
                return None
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None

    def get_posts_by_page(self, page_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all posts from a specific Facebook page"""
        try:
            with self.session_scope() as session:
                posts = session.query(FacebookPost).filter_by(
                    page_name=page_name
                ).order_by(FacebookPost.timestamp.desc()).limit(limit).all()
                return [post_to_dict(p) for p in posts]
        except Exception as e:
            logger.error(f"Error getting posts for page {page_name}: {e}")
            return []

    def get_all_posts(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all posts with optional limit"""
        try:
            with self.session_scope() as session:
                posts = session.query(FacebookPost).order_by(
                    FacebookPost.scraped_at.desc()
                ).limit(limit).all()
                return [post_to_dict(p) for p in posts]
        except Exception as e:
            logger.error(f"Error getting all posts: {e}")
            return []

    def delete_post(self, post_id: str) -> bool:
        """Delete a post and its related data"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if post:
                    session.delete(post)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            return False

    def save_image(self, post_id: str, image_data: Dict[str, Any]) -> str:
        """Save an image as relational record for a post"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if not post:
                    raise ValueError(f"Post with post_id {post_id} not found")
                
                img_url = image_data.get('image_url') or image_data.get('original_url')
                existing_img = session.query(PostImage).filter_by(
                    post_id=post.id,
                    image_url=img_url
                ).first()
                
                if existing_img:
                    return str(existing_img.id)
                    
                img = PostImage(
                    post_id=post.id,
                    image_url=img_url,
                    local_path=image_data.get('local_path') or image_data.get('filename'),
                    downloaded_at=image_data.get('downloaded_at') or datetime.utcnow()
                )
                session.add(img)
                session.flush()
                return str(img.id)
        except Exception as e:
            logger.error(f"Error saving image for post {post_id}: {e}")
            raise

    def get_images_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        """Get all images for a specific post"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if not post:
                    return []
                images = session.query(PostImage).filter_by(post_id=post.id).all()
                return [image_to_dict(img) for img in images]
        except Exception as e:
            logger.error(f"Error getting images for post {post_id}: {e}")
            return []

    def save_comment(self, post_id: str, comment_data: Dict[str, Any]) -> str:
        """Save a comment for a post"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if not post:
                    raise ValueError(f"Post with post_id {post_id} not found")
                
                comment_id = comment_data.get('comment_id')
                author_name = comment_data.get('author_name') or comment_data.get('author')
                content = comment_data.get('content') or comment_data.get('text')
                
                existing_comment = None
                if comment_id:
                    existing_comment = session.query(PostComment).filter_by(
                        post_id=post.id,
                        comment_id=comment_id
                    ).first()
                if not existing_comment:
                    existing_comment = session.query(PostComment).filter_by(
                        post_id=post.id,
                        author_name=author_name,
                        content=content
                    ).first()
                    
                if existing_comment:
                    if comment_id:
                        existing_comment.comment_id = comment_id
                    if author_name:
                        existing_comment.author_name = author_name
                    if content:
                        existing_comment.content = content
                    session.flush()
                    return existing_comment.comment_id or str(existing_comment.id)
                
                ts = comment_data.get('timestamp') or comment_data.get('comment_time')
                if isinstance(ts, str):
                    try:
                       ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                    except:
                       ts = datetime.utcnow()
                elif not ts:
                    ts = datetime.utcnow()
                    
                comment = PostComment(
                    post_id=post.id,
                    comment_id=comment_id,
                    author_name=author_name,
                    author_url=comment_data.get('author_url'),
                    content=content,
                    timestamp=ts,
                    likes=comment_data.get('likes', 0),
                    scraped_at=comment_data.get('scraped_at') or datetime.utcnow()
                )
                session.add(comment)
                session.flush()
                return comment.comment_id or str(comment.id)
        except Exception as e:
            logger.error(f"Error saving comment for post {post_id}: {e}")
            raise

    def get_comments_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a specific post"""
        try:
            with self.session_scope() as session:
                post = session.query(FacebookPost).filter_by(post_id=post_id).first()
                if not post:
                    return []
                comments = session.query(PostComment).filter_by(
                    post_id=post.id
                ).order_by(PostComment.timestamp.desc()).all()
                return [comment_to_dict(cmt) for cmt in comments]
        except Exception as e:
            logger.error(f"Error getting comments for post {post_id}: {e}")
            return []

    def save_analysis_result(self, post_id: str, analysis_type: str, result: Dict[str, Any]) -> str:
        """Save ML analysis results for a post"""
        try:
            with self.session_scope() as session:
                doc_id = f"{post_id}_{analysis_type}"
                existing = session.query(AnalysisResult).filter_by(
                    post_id=post_id,
                    analysis_type=analysis_type
                ).first()
                
                result_str = json.dumps(result)
                
                if existing:
                    existing.result = result_str
                    existing.analyzed_at = datetime.utcnow()
                else:
                    analysis = AnalysisResult(
                        post_id=post_id,
                        analysis_type=analysis_type,
                        result=result_str,
                        analyzed_at=datetime.utcnow()
                    )
                    session.add(analysis)
                
                session.flush()
                return doc_id
        except Exception as e:
            logger.error(f"Error saving analysis result for post {post_id}: {e}")
            raise

    def get_analysis_results(self, post_id: str = None, analysis_type: str = None) -> List[Dict[str, Any]]:
        """Get analysis results with optional filters"""
        try:
            with self.session_scope() as session:
                query = session.query(AnalysisResult)
                if post_id:
                    query = query.filter_by(post_id=post_id)
                if analysis_type:
                    query = query.filter_by(analysis_type=analysis_type)
                
                results = query.all()
                return [analysis_to_dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error getting analysis results: {e}")
            return []

    def bulk_save_posts(self, posts: List[Dict[str, Any]]) -> int:
        """Save multiple posts in bulk"""
        count = 0
        for post in posts:
            if self.save_post(post):
                count += 1
        return count

    # ==================== UTILITY METHODS ====================

    def get_latest_posts(self, limit: int = 10) -> List[FacebookPost]:
        """Get the latest posts from the database"""
        try:
            with self.session_scope() as session:
                latest_posts = session.query(FacebookPost).order_by(
                    FacebookPost.scraped_at.desc()
                ).limit(limit).all()
                return latest_posts
        except Exception as e:
            logger.error(f"Error getting latest posts: {e}")
            return []

    def cleanup_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with self.session_scope() as session:
                deleted_count = session.query(FacebookPost).filter(
                    FacebookPost.scraped_at < cutoff_date
                ).delete()
                
                logger.info(f"Deleted {deleted_count} old records")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0

    def health_check(self) -> bool:
        """Check if database is accessible and tables exist"""
        try:
            with self.engine.connect() as connection:
                # Portable check: queries tables in PostgreSQL
                result = connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
                tables = [row[0] for row in result]
                
                required_tables = ['facebook_posts', 'post_images', 'post_comments', 'analysis_results']
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
        Remove duplicate comments and post pictures.
        A duplicate comment is defined as having the same post_id, author_name, and content.
        A duplicate image is defined as having the same image_url or local_path.
        
        Returns:
            dict: Count of duplicates removed for each type
        """
        stats = {
            'comments': 0,
            'images': 0
        }
        
        try:
            with self.session_scope() as session:
                # 1. Remove duplicate comments
                subquery = session.query(
                    PostComment.post_id,
                    PostComment.author_name,
                    PostComment.content,
                    func.min(PostComment.id).label('min_id')
                ).group_by(
                    PostComment.post_id,
                    PostComment.author_name,
                    PostComment.content
                ).subquery()
                
                deleted_comments = session.query(PostComment).filter(
                    ~PostComment.id.in_(
                        session.query(subquery.c.min_id)
                    )
                ).delete(synchronize_session=False)
                
                stats['comments'] = deleted_comments
                
                # 2. Remove duplicate images
                subquery = session.query(
                    PostImage.post_id,
                    PostImage.image_url,
                    func.min(PostImage.id).label('min_id')
                ).filter(PostImage.image_url.isnot(None)).group_by(
                    PostImage.post_id,
                    PostImage.image_url
                ).subquery()
                
                deleted_images = session.query(PostImage).filter(
                    PostImage.image_url.isnot(None),
                    ~PostImage.id.in_(
                        session.query(subquery.c.min_id)
                    )
                ).delete(synchronize_session=False)
                
                stats['images'] = deleted_images
                
                logger.info(f"Removed {stats['comments']} duplicate comments")
                logger.info(f"Removed {stats['images']} duplicate post images")
                
                return stats
                
        except SQLAlchemyError as e:
            logger.error(f"Error removing duplicates: {e}")
            return stats

    @property
    def session(self):
        return self._session

def get_database_manager() -> DatabaseManager:
    """Get a DatabaseManager instance"""
    return DatabaseManager()

# Add event listeners for query performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = datetime.now()
    logger.debug(f"Starting query: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = datetime.now() - context._query_start_time
    logger.debug(f"Query completed in {total_time.total_seconds():.3f}s")
