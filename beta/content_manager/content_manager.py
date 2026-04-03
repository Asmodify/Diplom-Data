from pathlib import Path
import os
import json
import shutil
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from db.database import DatabaseManager
from db.models import FacebookPost, PostImage, PostComment

logger = logging.getLogger(__name__)

class ContentSaver:
    """Handles saving and organizing scraped content"""
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "images"
        self.screenshots_dir = self.base_dir / "screenshots"
        self.exports_dir = self.base_dir / "exports"
        self.db = DatabaseManager()
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.images_dir, self.screenshots_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def save_post(self, post_data: Dict[str, Any], page_name: str) -> bool:
        """
        Save post data to database and download associated media
        
        Args:
            post_data: Dictionary containing post information
            page_name: Name of the Facebook page
            
        Returns:
            bool: Whether save was successful
        """
        try:
            post_id = post_data.get('post_id') or f"{page_name}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            post_url = post_data.get('post_url') or f"https://www.facebook.com/{page_name}"

            # Create post record
            post = FacebookPost(
                page_name=page_name,
                post_id=post_id,
                post_url=post_url,
                content=post_data.get('content', ''),
                timestamp=post_data.get('timestamp'),
                likes=post_data.get('likes', 0),
                shares=post_data.get('shares', 0),
                comment_count=len(post_data.get('comments', []))
            )
            
            # Save images if any
            for img_url in post_data.get('images', []):
                image = PostImage(
                    image_url=img_url,
                    local_path=self._download_image(img_url, page_name, post_id)
                )
                post.images.append(image)
                
            # Save comments if any
            for comment_data in post_data.get('comments', []):
                comment_id = comment_data.get('comment_id') or f"{post_id}_c_{len(post.comments)+1}"
                comment = PostComment(
                    comment_id=comment_id,
                    author_name=comment_data.get('author', ''),
                    author_url=comment_data.get('author_url', ''),
                    content=comment_data.get('content', ''),
                    timestamp=comment_data.get('timestamp'),
                    likes=comment_data.get('likes', 0)
                )
                self.db.session.add(comment)
                self.db.session.flush()  # Assigns an ID to comment
                # Handle replies
                if 'replies' in comment_data:
                    for reply_data in comment_data['replies']:
                        reply_comment_id = reply_data.get('comment_id') or f"{comment_id}_r_{len(post.comments)+1}"
                        reply = PostComment(
                            comment_id=reply_comment_id,
                            author_name=reply_data.get('author', ''),
                            author_url=reply_data.get('author_url', ''),
                            content=reply_data.get('content', ''),
                            timestamp=reply_data.get('timestamp'),
                            likes=reply_data.get('likes', 0),
                            reply_to_id=comment.id
                        )
                        post.comments.append(reply)
                post.comments.append(comment)
                
            # Save to database via managed SQLAlchemy session
            self.db.session.add(post)
            self.db.session.commit()
            
            logger.info(f"Saved post {post_id} from {page_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving post: {str(e)}")
            self.db.session.rollback()
            return False
            
    def save_screenshot(self, screenshot_data: bytes, post_id: str, page_name: str) -> Optional[str]:
        """Save a screenshot of a post"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name}_{post_id}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            # Save screenshot
            with open(filepath, 'wb') as f:
                f.write(screenshot_data)
                
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving screenshot: {str(e)}")
            return None
            
    def _download_image(self, image_url: str, page_name: str, post_id: str) -> Optional[str]:
        """Download an image and save it locally"""
        try:
            # Create filename
            ext = image_url.split('.')[-1].split('?')[0]  # Get extension before query params
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'  # Default to jpg
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name}_{post_id}_{timestamp}.{ext}"
            filepath = self.images_dir / filename
            
            # Download image
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return str(filepath)
                
            return None
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
            
    def export_posts(self, page_name: str, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> str:
        """Export posts to JSON file"""
        try:
            # Query posts
            query = self.db.session.query(FacebookPost).filter(FacebookPost.page_name == page_name)
            if start_date:
                query = query.filter(FacebookPost.timestamp >= start_date)
            if end_date:
                query = query.filter(FacebookPost.timestamp <= end_date)
                
            posts = query.all()
            
            # Convert to dictionary
            export_data = []
            for post in posts:
                post_dict = {
                    'post_id': post.post_id,
                    'url': post.post_url,
                    'content': post.content,
                    'timestamp': post.timestamp.isoformat() if post.timestamp else None,
                    'likes': post.likes,
                    'shares': post.shares,
                    'images': [{'url': img.image_url, 'local_path': img.local_path}
                             for img in post.images],
                    'comments': []
                }
                
                # Add comments
                for comment in post.comments:
                    comment_dict = {
                        'comment_id': comment.comment_id,
                        'author': comment.author_name,
                        'content': comment.content,
                        'timestamp': comment.timestamp.isoformat() if comment.timestamp else None,
                        'likes': comment.likes,
                        'replies': [{
                            'comment_id': reply.comment_id,
                            'author': reply.author_name,
                            'content': reply.content,
                            'timestamp': reply.timestamp.isoformat() if reply.timestamp else None,
                            'likes': reply.likes
                        } for reply in comment.replies]
                    }
                    post_dict['comments'].append(comment_dict)
                    
                export_data.append(post_dict)
                
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name}_posts_{timestamp}.json"
            filepath = self.exports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting posts: {str(e)}")
            return None
