#!/usr/bin/env python
"""
Simple script to export Facebook comments to a text file
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR, EXPORTS_DIR
from db.models import FacebookPost, PostImage, PostComment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Facebook Comments Exporter')
    parser.add_argument('--page', type=str, help='Export comments for a specific page only')
    parser.add_argument('--days', type=int, default=30, help='Export comments from the past N days (default: 30, 0 = all)')
    parser.add_argument('--output', type=str, help='Custom output file name')
    parser.add_argument('--format', choices=['txt', 'csv'], default='txt', help='Output format (txt or csv)')
    return parser.parse_args()

def export_comments_to_text(page_name=None, days=30, output_file=None):
    """Export all comments to a text file"""
    print("Exporting Facebook comments to text file...")
    db = DatabaseManager()
    
    try:
        # Check database connection
        if not db.health_check():
            print("Error: Database connection failed")
            logger.error("Database connection failed")
            return False
        
        # Ensure exports directory exists
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_file:
            filename = EXPORTS_DIR / output_file
        else:
            page_part = f"{page_name}_" if page_name else ""
            filename = EXPORTS_DIR / f"{page_part}facebook_comments_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("FACEBOOK COMMENTS EXPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if page_name:
                f.write(f"Page: {page_name}\n")
            if days > 0:
                f.write(f"Period: Last {days} days\n")
            f.write("=" * 80 + "\n\n")
            
            # Get pages to process
            with db.session_scope() as session:
                # Create query with filters
                query = session.query(FacebookPost)
                
                # Filter by page if specified
                if page_name:
                    query = query.filter(FacebookPost.page_name == page_name)
                
                # Filter by date if days specified
                if days > 0:
                    from sqlalchemy import func
                    date_cutoff = func.datetime('now', f'-{days} days')
                    query = query.filter(FacebookPost.post_time >= date_cutoff)
                
                # Get posts ordered by date
                posts = query.order_by(FacebookPost.post_time.desc()).all()
                
                if not posts:
                    message = f"No posts found for the specified criteria"
                    f.write(message + "\n")
                    print(message)
                    return False
                
                # Group posts by page 
                posts_by_page = {}
                for post in posts:
                    if post.page_name not in posts_by_page:
                        posts_by_page[post.page_name] = []
                    posts_by_page[post.page_name].append(post)
                
                # Process each page
                total_comments = 0
                for page_name, page_posts in posts_by_page.items():
                    f.write(f"PAGE: {page_name}\n")
                    f.write("-" * 80 + "\n\n")
                    
                    page_comments_count = 0
                    
                    # Process each post
                    for post in page_posts:
                        post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else "Unknown date"
                        f.write(f"POST: {post_date} (ID: {post.post_id})\n")
                        f.write(f"Likes: {post.likes}, Shares: {post.shares}\n")
                        f.write("-" * 60 + "\n")
                        f.write(f"{post.post_text}\n")
                        f.write("-" * 60 + "\n\n")
                        
                        # Get comments for this post
                        comments = session.query(PostComment).filter(
                            PostComment.post_id == post.post_id
                        ).order_by(PostComment.comment_time.desc()).all()
                        
                        if not comments:
                            f.write("No comments for this post\n\n")
                            continue
                        
                        # Write comments
                        f.write(f"COMMENTS ({len(comments)}):\n\n")
                        
                        for i, comment in enumerate(comments, 1):
                            comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else "Unknown"
                            f.write(f"[{i}] {comment.author} - {comment_date} (Likes: {comment.likes})\n")
                            f.write(f"{comment.text}\n")
                            f.write("-" * 40 + "\n")
                            
                            page_comments_count += 1
                            total_comments += 1
                        
                        f.write("\n" + "=" * 40 + "\n\n")
                        
                    f.write(f"Total comments for {page_name}: {page_comments_count}\n\n")
                    f.write("=" * 80 + "\n\n")
                
                # Write summary at the end
                f.write("\nEXPORT SUMMARY\n")
                f.write("=" * 40 + "\n")
                f.write(f"Pages: {len(posts_by_page)}\n")
                f.write(f"Posts: {len(posts)}\n")
                f.write(f"Comments: {total_comments}\n")
                f.write("=" * 40 + "\n")
                
            print(f"✅ Comments exported to {filename}")
            print(f"Total comments exported: {total_comments}")
            return True
        
    except Exception as e:
        logger.error(f"Error exporting comments: {e}")
        print(f"Error exporting comments: {e}")
        return False

def export_comments_to_csv(page_name=None, days=30, output_file=None):
    """Export all comments to a CSV file"""
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required for CSV export but not installed.")
        print("Please run: pip install pandas")
        return False
        
    print("Exporting Facebook comments to CSV file...")
    db = DatabaseManager()
    
    try:
        # Check database connection
        if not db.health_check():
            print("Error: Database connection failed")
            logger.error("Database connection failed")
            return False
        
        # Ensure exports directory exists
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_file:
            filename = EXPORTS_DIR / output_file
        else:
            page_part = f"{page_name}_" if page_name else ""
            filename = EXPORTS_DIR / f"{page_part}facebook_comments_{timestamp}.csv"
            
        # Prepare data for CSV
        all_comments_data = []
        
        with db.session_scope() as session:
            # Create query with filters
            query = session.query(FacebookPost)
            
            # Filter by page if specified
            if page_name:
                query = query.filter(FacebookPost.page_name == page_name)
            
            # Filter by date if days specified
            if days > 0:
                from sqlalchemy import func
                date_cutoff = func.datetime('now', f'-{days} days')
                query = query.filter(FacebookPost.post_time >= date_cutoff)
            
            # Get posts
            posts = query.all()
            
            if not posts:
                print(f"No posts found for the specified criteria")
                return False
                
            # Process each post
            for post in posts:
                post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else ""
                
                # Get comments for this post
                comments = session.query(PostComment).filter(
                    PostComment.post_id == post.post_id
                ).all()
                
                # Add each comment to the data
                for comment in comments:
                    comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else ""
                    all_comments_data.append({
                        'page': post.page_name,
                        'post_id': post.post_id, 
                        'post_date': post_date,
                        'post_likes': post.likes,
                        'post_shares': post.shares,
                        'post_text': post.post_text,
                        'author': comment.author,
                        'comment_date': comment_date,
                        'comment_likes': comment.likes,
                        'comment_text': comment.text
                    })
            
        # Write to CSV
        if all_comments_data:
            df = pd.DataFrame(all_comments_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Comments exported to {filename}")
            print(f"Total comments exported: {len(all_comments_data)}")
            return True
        else:
            print("No comments found to export")
            return False
        
    except Exception as e:
        logger.error(f"Error exporting comments to CSV: {e}")
        print(f"Error exporting comments to CSV: {e}")
        return False

def main():
    """Main function"""
    # Parse arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("FACEBOOK COMMENTS EXPORTER")
    print("="*80)
    
    # Call appropriate export function
    if args.format.lower() == 'csv':
        success = export_comments_to_csv(
            page_name=args.page,
            days=args.days,
            output_file=args.output
        )
    else:
        success = export_comments_to_text(
            page_name=args.page,
            days=args.days,
            output_file=args.output
        )
    
    if success:
        logger.info("Export completed successfully")
        return 0
    else:
        logger.error("Export failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
