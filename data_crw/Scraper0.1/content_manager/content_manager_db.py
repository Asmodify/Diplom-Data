import logging
from pathlib import Path
from typing import Dict, Any, List
import json
import csv
from db.database import DatabaseManager
from db.models import FacebookPost, PostImage, PostComment
from sqlalchemy.exc import IntegrityError
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentSaver:
    """Handles saving and organizing scraped content, images, comments, and saving to DB"""
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.posts_dir = self.base_dir / "posts"
        self.images_dir = self.base_dir / "images"
        self.comments_dir = self.base_dir / "comments"
        self.posts_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.comments_dir.mkdir(exist_ok=True)
        self.db = DatabaseManager()

    def save_post(self, post_data: Dict[str, Any], page_url: str) -> bool:
        # Save to file as before
        try:
            post_id = post_data.get('url', 'unknown').split('/')[-1]
            file_path = self.posts_dir / f"{post_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(post_data.get('content', ''))
            logger.info(f"Saved post to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save post: {e}")
        # Save to database
        try:
            session = self.db.Session()
            post = FacebookPost(
                page_name=page_url.rstrip('/').split('/')[-1],
                post_id=post_id,
                post_url=post_data.get('url'),
                content=post_data.get('content'),
                timestamp=datetime.fromisoformat(post_data['date']) if post_data.get('date') else datetime.utcnow()
            )
            session.merge(post)  # merge to avoid duplicate post_id
            # Save images
            for img_path in post_data.get('images', []):
                img = PostImage(post_id=post_id, image_url=None, local_path=img_path)
                session.add(img)
            # Save comments
            for comment in post_data.get('comments', []):
                c = PostComment(
                    post_id=post_id,
                    comment_text=comment.get('text'),
                    timestamp=datetime.fromisoformat(comment['date']) if comment.get('date') else datetime.utcnow()
                )
                session.add(c)
            session.commit()
            session.close()
            logger.info(f"Saved post {post_id} to database.")
            return True
        except IntegrityError:
            logger.warning(f"Post {post_id} already exists in database.")
            return False
        except Exception as e:
            logger.error(f"Failed to save post to database: {e}")
            return False

    # ...existing code for save_image, save_comment, export_posts_csv, export_comments_json...
