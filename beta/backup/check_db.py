#!/usr/bin/env python
"""
Check database contents and export results
"""

import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR
from db.models import FacebookPost, PostImage, PostComment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'check_db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_database_content():
    """Check database content and export results"""
    db = DatabaseManager()
    
    try:
        # Check if tables exist
        try:
            with db.session_scope() as session:
                # Get table names from SQLAlchemy metadata
                tables = list(FacebookPost.__table__.metadata.tables.keys())
                logger.info(f"Database tables: {', '.join(tables)}")
        except Exception as e:
            logger.error(f"Error getting table information: {e}")
            return False
        
        # Check Facebook posts
        try:
            with db.session_scope() as session:
                posts = session.query(FacebookPost).order_by(FacebookPost.extracted_at.desc()).limit(10).all()
                
                if posts:
                    print("\nLatest Posts:")
                    print("-" * 50)
                    for post in posts:
                        print(f"Page: {post.page_name}")
                        print(f"ID: {post.post_id}")
                        print(f"URL: {post.post_url}")
                        print(f"Text: {post.post_text[:100]}...")
                        print(f"Time: {post.post_time}")
                        print(f"Likes: {post.likes}, Shares: {post.shares}")
                        print("-" * 50)
                else:
                    print("\nNo posts found in database.")
        except Exception as e:
            logger.error(f"Error retrieving posts: {e}")
        
        # Check images
        try:
            with db.session_scope() as session:
                images = session.query(PostImage).order_by(PostImage.downloaded_at.desc()).limit(10).all()
                
                if images:
                    print("\nLatest Images:")
                    print("-" * 50)
                    for img in images:
                        print(f"Post ID: {img.post_id}")
                        print(f"Filename: {img.filename}")
                        print(f"Path: {img.local_path}")
                        print("-" * 30)
                else:
                    print("\nNo images found in database.")
        except Exception as e:
            logger.error(f"Error retrieving images: {e}")
        
        # Check comments
        try:
            with db.session_scope() as session:
                comments = session.query(PostComment).order_by(PostComment.extracted_at.desc()).limit(10).all()
                
                if comments:
                    print("\nLatest Comments:")
                    print("-" * 50)
                    for comment in comments:
                        print(f"Post ID: {comment.post_id}")
                        print(f"Author: {comment.author}")
                        print(f"Text: {comment.text[:100]}...")
                        print(f"Time: {comment.comment_time}")
                        print(f"Likes: {comment.likes}")
                        print("-" * 30)
                else:
                    print("\nNo comments found in database.")
        except Exception as e:
            logger.error(f"Error retrieving comments: {e}")
        
        # Check database statistics
        try:
            with db.session_scope() as session:
                post_count = session.query(FacebookPost).count()
                image_count = session.query(PostImage).count()
                comment_count = session.query(PostComment).count()
                
                print("\nDatabase Statistics:")
                print("-" * 50)
                print(f"Total Posts: {post_count}")
                print(f"Total Images: {image_count}")
                print(f"Total Comments: {comment_count}")
                print("-" * 50)
        except Exception as e:
            logger.error(f"Error retrieving database statistics: {e}")
        
        # Export data to CSV if requested
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = ROOT_DIR / f"database_check_{timestamp}.csv"
        
        try:
            with db.session_scope() as session:
                posts = session.query(FacebookPost).order_by(FacebookPost.extracted_at.desc()).all()
                if posts:
                    posts_df = pd.DataFrame([
                        {
                            'page_name': p.page_name,
                            'post_id': p.post_id,
                            'post_url': p.post_url,
                            'post_text': p.post_text,
                            'post_time': p.post_time,
                            'author': p.author,
                            'likes': p.likes,
                            'shares': p.shares,
                            'extracted_at': p.extracted_at
                        } for p in posts
                    ])
                    
                    posts_df.to_csv(export_path, index=False)
                    logger.info(f"Exported data to {export_path}")
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

if __name__ == "__main__":
    if check_database_content():
        logger.info("✅ Database check completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Database check failed")
        sys.exit(1)
