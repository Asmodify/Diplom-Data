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
    """Handles saving and organizing scraped content, images, and comments"""
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.posts_dir = self.base_dir / "posts"
        self.images_dir = self.base_dir / "images"
        self.comments_dir = self.base_dir / "comments"
        self.posts_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.comments_dir.mkdir(exist_ok=True)

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
            if not hasattr(self, 'db'):
                self.db = DatabaseManager()
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

    def save_image(self, image_bytes: bytes, image_name: str) -> bool:
        try:
            file_path = self.images_dir / image_name
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"Saved image to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return False

    def save_comment(self, comment_data: Dict[str, Any], post_id: str) -> bool:
        try:
            file_path = self.comments_dir / f"{post_id}.json"
            comments = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    comments = json.load(f)
            comments.append(comment_data)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved comment for post {post_id} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save comment: {e}")
            return False

    def export_posts_csv(self, export_path: str) -> None:
        files = list(self.posts_dir.glob('*.txt'))
        with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['post_id', 'content'])
            for file in files:
                post_id = file.stem
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                writer.writerow([post_id, content])
        logger.info(f"Exported posts to {export_path}")

    def export_comments_json(self, export_path: str) -> None:
        all_comments = []
        for file in self.comments_dir.glob('*.json'):
            with open(file, 'r', encoding='utf-8') as f:
                comments = json.load(f)
                all_comments.extend(comments)
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        logger.info(f"Exported comments to {export_path}")
