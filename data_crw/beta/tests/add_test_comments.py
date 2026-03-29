#!/usr/bin/env python
"""
Test script to add a comment to a post in the database
This script helps verify that the database layer is working correctly
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostComment, PostImage

def add_test_comments():
    """Add test comments to verify database functionality"""
    db = DatabaseManager()
    
    try:
        # Get all existing posts
        with db.session_scope() as session:
            posts = session.query(FacebookPost).all()
            
            if not posts:
                print("No posts found in database. Creating a test post...")
                test_post = FacebookPost(
                    post_id="test_post_2",
                    page_name="test_page",
                    post_url="https://facebook.com/testpage/posts/test_post_2",
                    post_text="This is a test post to verify comment saving.",
                    post_time=datetime.now(),
                    author="Test Page",
                    likes=5,
                    shares=2,
                    comments_count=3,
                    extracted_at=datetime.now()
                )
                session.add(test_post)
                session.flush()
                post = test_post
                print(f"Created test post with ID: {post.post_id}")
            else:
                post = posts[0]
                print(f"Using existing post with ID: {post.post_id}")
            
            # Create test comments
            for i in range(3):
                comment = PostComment(
                    post_id=post.post_id,
                    author=f"Test Author {i+1}",
                    text=f"This is test comment #{i+1} to verify database comment saving works correctly.",
                    likes=i*5,
                    comment_time=datetime.now(),
                    extracted_at=datetime.now()
                )
                session.add(comment)
                print(f"Added comment by '{comment.author}': '{comment.text}'")
            
            # Update the post's comment count
            post.comments_count = 3
                
        print("\nTest comments were successfully added to the database.")
        print("Run view_comment_data.py to verify the comments were saved correctly.")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_test_comments()
