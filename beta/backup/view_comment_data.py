#!/usr/bin/env python
"""
Test tool for viewing comments in the database
"""

import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import FacebookPost, PostComment

def print_comments():
    """Print all comments in the database"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            # Get all comments
            comments = session.query(PostComment).all()
            
            print(f"\nFound {len(comments)} comments in the database:")
            print("="*80)
            
            for i, comment in enumerate(comments, 1):
                print(f"Comment {i}:")
                print(f"  Post ID: {comment.post_id}")
                print(f"  Author: {comment.author}")
                print(f"  Text: {comment.text[:100]}...")
                print(f"  Likes: {comment.likes}")
                print(f"  Time: {comment.comment_time}")
                print("-"*80)
                
            # Get posts with no comments
            posts_with_comments_count = session.query(FacebookPost.post_id, FacebookPost.comments_count).filter(
                FacebookPost.comments_count > 0
            ).all()
            
            print("\nPosts with comments_count > 0:")
            print("="*80)
            for post_id, count in posts_with_comments_count:
                # Count actual comments for this post
                actual_count = session.query(PostComment).filter_by(post_id=post_id).count()
                print(f"Post {post_id}: Expected {count} comments, Actual: {actual_count}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print_comments()
