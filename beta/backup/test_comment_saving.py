#!/usr/bin/env python
"""
Test script to verify PostgreSQL comment saving functionality
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.models import PostComment

print("PostgreSQL Comment Saving Test")
print("============================")

def test_save_comment():
    """Test saving a single comment to the database"""
    db = DatabaseManager()
    
    # Create a test post ID
    post_id = f"test_post_{int(datetime.now().timestamp())}"
    
    # Create test comment data
    comment_data = {
        'post_id': post_id,
        'author': 'Test Author',
        'text': 'This is a test comment to verify PostgreSQL comment saving',
        'likes': 10,
        'comment_time': datetime.now(),
        'extracted_at': datetime.now()
    }
    
    # Create basic post data (needed for foreign key constraint)
    post_data = {
        'post_id': post_id,
        'page_name': 'test_page',
        'post_text': 'Test post for comment saving',
        'post_time': datetime.now(),
        'extracted_at': datetime.now()
    }
    
    print(f"Saving test post with ID: {post_id}")
    result = db.save_post(post_data)
    
    if result:
        print("✅ Test post saved successfully")
    else:
        print("❌ Failed to save test post")
        return False
    
    print(f"Saving test comment for post ID: {post_id}")
    result = db.save_post(post_data, [], [comment_data])
    
    if result:
        print("✅ Test comment saved successfully")
    else:
        print("❌ Failed to save test comment")
        return False
    
    return True

def verify_saved_comment(post_id):
    """Verify that the comment was saved correctly"""
    try:
        db = DatabaseManager()
        
        with db.session_scope() as session:
            comments = session.query(PostComment).filter_by(post_id=post_id).all()
            
            if comments:
                print(f"✅ Found {len(comments)} comments in the database:")
                for i, comment in enumerate(comments, 1):
                    print(f"  Comment {i}: {comment.author} - {comment.text[:50]}...")
                return True
            else:
                print("❌ No comments found in the database")
                return False
    except Exception as e:
        print(f"❌ Error verifying saved comment: {e}")
        return False

if __name__ == "__main__":
    try:
        # Initialize database
        db = DatabaseManager()
        db.init_db()
        
        # Test comment saving
        post_id = f"test_post_{int(datetime.now().timestamp())}"
        if test_save_comment():
            verify_saved_comment(post_id)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
