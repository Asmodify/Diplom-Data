from pathlib import Path
import os
import json
import shutil
from datetime import datetime
import logging

ROOT_DIR = Path(__file__).parent.parent

class ContentManager:
    def __init__(self):
        self.base_dir = ROOT_DIR
        self.images_dir = self.base_dir / "images"
        self.screenshots_dir = self.base_dir / "screenshots"
        self.exports_dir = self.base_dir / "exports"
        
        # Create directories
        self.images_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.exports_dir.mkdir(exist_ok=True)
        
    def save_post_content(self, post_data):
        """Save post content, screenshots, and comments"""
        try:
            # Create page directory
            page_dir = self.images_dir / post_data['page_name']
            page_dir.mkdir(exist_ok=True)
            
            # Save screenshots
            if post_data.get('screenshot'):
                screenshot_path = self.screenshots_dir / f"post_{post_data['post_id']}.png"
                shutil.copy2(post_data['screenshot'], str(screenshot_path))
                
            # Save images
            if post_data.get('images'):
                for idx, img in enumerate(post_data['images']):
                    img_path = page_dir / f"post_{post_data['post_id']}_{idx}.jpg"
                    shutil.copy2(img, str(img_path))
                    
            # Save comments
            if post_data.get('comments'):
                comment_file = self.exports_dir / f"comments_{post_data['post_id']}.json"
                with open(comment_file, 'w', encoding='utf-8') as f:
                    json.dump(post_data['comments'], f, ensure_ascii=False, indent=2)
                    
            # Save post data
            post_file = self.exports_dir / f"post_{post_data['post_id']}.json"
            with open(post_file, 'w', encoding='utf-8') as f:
                # Remove large data before saving
                post_data_clean = post_data.copy()
                post_data_clean.pop('screenshot', None)
                post_data_clean.pop('images', None)
                post_data_clean.pop('comments', None)
                json.dump(post_data_clean, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving content for post {post_data.get('post_id')}: {e}")
            
    def get_post_data(self, post_id):
        """Retrieve saved post data"""
        try:
            post_file = self.exports_dir / f"post_{post_id}.json"
            if not post_file.exists():
                return None
                
            with open(post_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error retrieving post data for {post_id}: {e}")
            return None
