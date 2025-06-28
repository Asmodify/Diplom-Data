#!/usr/bin/env python
"""
Quick script to check database comment counts
"""

from db.database import DatabaseManager
from db.models import FacebookPost, PostComment, PostImage

def main():
    db = DatabaseManager()
    try:
        with db.session_scope() as session:
            post_count = session.query(FacebookPost).count()
            comment_count = session.query(PostComment).count()
            image_count = session.query(PostImage).count()
            
            print(f"Database Summary:")
            print(f"================")
            print(f"Total posts:    {post_count}")
            print(f"Total comments: {comment_count}")
            print(f"Total images:   {image_count}")
            
            if post_count > 0:
                # Get some post details
                posts = session.query(FacebookPost).order_by(FacebookPost.id.desc()).limit(5).all()
                print("\nLatest 5 posts:")
                for post in posts:
                    comment_count = session.query(PostComment).filter_by(post_id=post.post_id).count()
                    print(f"- Post ID: {post.post_id}")
                    print(f"  Page: {post.page_name}")
                    print(f"  Text: {post.post_text[:100]}..." if post.post_text else "  Text: None")
                    print(f"  Comments count: {comment_count}")
                    print()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
