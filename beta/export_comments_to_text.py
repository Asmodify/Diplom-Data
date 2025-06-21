#!/usr/bin/env python
"""
Simple script to export Facebook comments to a text file
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostImage, PostComment

def export_comments_to_text():
    """Export all comments to a text file"""
    print("Exporting Facebook comments to text file...")
    db = DatabaseManager()
    
    try:
        # Check database connection
        if not db.health_check():
            print("Error: Database connection failed")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"facebook_comments_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("FACEBOOK COMMENTS EXPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            with db.session_scope() as session:
                # Get all pages
                pages = session.query(FacebookPost.page_name).distinct().all()
                pages = [page[0] for page in pages if page[0]]
                
                f.write(f"Found {len(pages)} pages\n\n")
                
                # Process each page
                for page_name in pages:
                    f.write(f"PAGE: {page_name}\n")
                    f.write("-" * 80 + "\n\n")
                    
                    # Get posts for this page
                    posts = session.query(FacebookPost).filter(
                        FacebookPost.page_name == page_name
                    ).order_by(FacebookPost.post_time.desc()).all()
                    
                    f.write(f"Found {len(posts)} posts\n\n")
                    
                    # Process each post
                    for post in posts:
                        f.write(f"POST: {post.post_id}\n")
                        f.write(f"Time: {post.post_time}\n")
                        f.write(f"URL: {post.post_url}\n")
                        f.write(f"Likes: {post.likes}, Shares: {post.shares}\n")
                        f.write(f"Content: {post.post_text or '(No text)'}\n\n")
                        
                        # Get comments for this post
                        comments = session.query(PostComment).filter(
                            PostComment.post_id == post.post_id
                        ).order_by(PostComment.comment_time.desc()).all()
                        
                        if comments:
                            f.write(f"COMMENTS ({len(comments)}):\n")
                            for i, comment in enumerate(comments, 1):
                                f.write(f"  {i}. {comment.author}: {comment.text}\n")
                                f.write(f"     Likes: {comment.likes}, Time: {comment.comment_time}\n")
                            f.write("\n")
                        else:
                            f.write("No comments on this post\n\n")
                        
                        f.write("-" * 40 + "\n\n")
                
        print(f"Comments exported to {filename}")
        return True
        
    except Exception as e:
        print(f"Error exporting comments: {e}")
        return False

if __name__ == "__main__":
    export_comments_to_text()
