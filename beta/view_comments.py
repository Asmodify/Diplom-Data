#!/usr/bin/env python
"""
View Facebook Comments Tool
Displays comments from the database with multiple filtering options
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import pandas as pd

# Add project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from db.database import DatabaseManager
from db.config import LOGS_DIR
from db.models import FacebookPost, PostImage, PostComment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'view_comments.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_pages_from_db():
    """Get list of all pages in the database"""
    db = DatabaseManager()
    pages = []
    
    try:
        with db.session_scope() as session:
            pages = session.query(FacebookPost.page_name).distinct().all()
            return [page[0] for page in pages if page[0]]
    except Exception as e:
        logger.error(f"Error getting pages from database: {e}")
        return []

def list_pages():
    """List all available pages in the database"""
    pages = get_pages_from_db()
    
    if not pages:
        print("No pages found in the database.")
        return
        
    print("\nAvailable Pages:")
    print("="*50)
    for i, page in enumerate(pages, 1):
        print(f"{i}. {page}")

def list_posts_for_page(page_name):
    """List all posts for a specific page"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            posts = session.query(
                FacebookPost.post_id,
                FacebookPost.post_text,
                FacebookPost.post_time,
                FacebookPost.likes
            ).filter(FacebookPost.page_name == page_name).order_by(
                FacebookPost.post_time.desc()
            ).all()
            
            if not posts:
                print(f"No posts found for page '{page_name}'")
                return
                
            print(f"\nPosts for '{page_name}':")
            print("="*80)
            
            headers = ["#", "Post ID", "Text Preview", "Date", "Likes"]
            table_data = []
            
            for i, post in enumerate(posts, 1):
                text_preview = post.post_text[:50] + "..." if post.post_text and len(post.post_text) > 50 else post.post_text or "(No text)"
                post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else "Unknown"
                
                table_data.append([
                    i,
                    post.post_id,
                    text_preview,
                    post_date,
                    post.likes
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            return [post.post_id for post in posts]
    except Exception as e:
        logger.error(f"Error listing posts for '{page_name}': {e}")
        return []

def view_comments_for_post(post_id):
    """View all comments for a specific post"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            # Get post details first
            post = session.query(
                FacebookPost
            ).filter(
                FacebookPost.post_id == post_id
            ).first()
            
            if not post:
                print(f"No post found with ID '{post_id}'")
                return
                
            # Get comments for this post
            comments = session.query(
                PostComment
            ).filter(
                PostComment.post_id == post_id
            ).order_by(
                PostComment.likes.desc(),  # Show most popular comments first
                PostComment.comment_time.desc()
            ).all()
            
            # Display post info
            print("\n" + "="*80)
            print(f"COMMENTS FOR POST")
            print("="*80)
            print(f"Page: {post.page_name}")
            print(f"Post ID: {post.post_id}")
            if post.post_url:
                print(f"URL: {post.post_url}")
            print(f"Date: {post.post_time}")
            print(f"Likes: {post.likes}, Shares: {post.shares}")
            
            # Display post text
            print("\nPOST CONTENT:")
            print("-"*80)
            print(post.post_text or "(No text content)")
            print("-"*80)
            
            # Get post images
            images = session.query(PostImage).filter(PostImage.post_id == post_id).all()
            if images:
                print(f"\nPost has {len(images)} images")
                for img in images:
                    print(f"- {img.local_path}")
            
            # Display comments
            print(f"\nCOMMENTS ({len(comments)}):")
            print("="*80)
            
            if not comments:
                print("No comments found for this post.")
                return
                
            for i, comment in enumerate(comments, 1):
                print(f"#{i} | Author: {comment.author}")
                print(f"    Likes: {comment.likes} | Time: {comment.comment_time}")
                print(f"    {comment.text}")
                print("-"*80)
                
            # Ask if user wants to export comments
            export = input("\nExport comments? (csv/txt/both/n): ").strip().lower()
            if export == 'csv':
                export_comments_to_csv(post, comments)
            elif export == 'txt':
                export_comments_to_txt(post, comments)
            elif export == 'both':
                export_comments_to_csv(post, comments)
                export_comments_to_txt(post, comments)
    except Exception as e:
        logger.error(f"Error viewing comments for post '{post_id}': {e}")

def view_all_comments_for_page(page_name):
    """View all comments for a specific page"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            # Get all post IDs for this page
            post_ids = session.query(
                FacebookPost.post_id
            ).filter(
                FacebookPost.page_name == page_name
            ).all()
            
            post_ids = [p.post_id for p in post_ids if p.post_id]
            
            if not post_ids:
                print(f"No posts found for page '{page_name}'")
                return
            
            # Get all comments for these posts
            comments = session.query(
                PostComment
            ).filter(
                PostComment.post_id.in_(post_ids)
            ).order_by(
                PostComment.comment_time.desc()
            ).all()
            
            print(f"\nALL COMMENTS FOR PAGE '{page_name}'")
            print("="*80)
            print(f"Found {len(comments)} comments across {len(post_ids)} posts")
            print("="*80)
            
            if not comments:
                print("No comments found.")
                return
                
            for i, comment in enumerate(comments, 1):
                print(f"#{i} | Post ID: {comment.post_id}")
                print(f"    Author: {comment.author} | Likes: {comment.likes}")
                print(f"    Time: {comment.comment_time}")
                print(f"    {comment.text}")
                print("-"*80)
                
                # Break after every 20 comments and ask to continue
                if i % 20 == 0:
                    cont = input(f"Showing {i}/{len(comments)} comments. Continue? (y/n): ").strip().lower()
                    if cont != 'y':
                        break
              # Ask if user wants to export comments
            export = input("\nExport comments? (csv/txt/both/n): ").strip().lower()
            if export == 'csv':
                export_page_comments_to_csv(page_name, comments)
            elif export == 'txt':
                export_page_comments_to_txt(page_name, comments)
            elif export == 'both':
                export_page_comments_to_csv(page_name, comments)
                export_page_comments_to_txt(page_name, comments)
                
    except Exception as e:
        logger.error(f"Error viewing comments for page '{page_name}': {e}")

def export_comments_to_csv(post, comments):
    """Export comments for a post to CSV file"""
    try:
        # Create DataFrame
        comments_data = []
        for comment in comments:
            comments_data.append({
                'Post ID': comment.post_id,
                'Author': comment.author,
                'Comment': comment.text,
                'Time': comment.comment_time,
                'Likes': comment.likes
            })
        
        df = pd.DataFrame(comments_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comments_{post.page_name}_{post.post_id[:10]}_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Comments exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting comments to CSV: {e}")

def export_comments_to_txt(post, comments):
    """Export comments for a post to TXT file"""
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comments_{post.page_name}_{post.post_id[:10]}_{timestamp}.txt"
        
        # Write to text file
        with open(filename, 'w', encoding='utf-8') as f:
            # Write post information
            f.write("="*80 + "\n")
            f.write(f"COMMENTS FOR POST\n")
            f.write("="*80 + "\n")
            f.write(f"Page: {post.page_name}\n")
            f.write(f"Post ID: {post.post_id}\n")
            if post.post_url:
                f.write(f"URL: {post.post_url}\n")
            f.write(f"Date: {post.post_time}\n")
            f.write(f"Likes: {post.likes}, Shares: {post.shares}\n\n")
            
            # Write post content
            f.write("POST CONTENT:\n")
            f.write("-"*80 + "\n")
            f.write(f"{post.post_text or '(No text content)'}\n")
            f.write("-"*80 + "\n\n")
            
            # Write comments
            f.write(f"COMMENTS ({len(comments)}):\n")
            f.write("="*80 + "\n\n")
            
            if not comments:
                f.write("No comments found for this post.\n")
            else:
                for i, comment in enumerate(comments, 1):
                    f.write(f"#{i} | Author: {comment.author}\n")
                    f.write(f"    Likes: {comment.likes} | Time: {comment.comment_time}\n")
                    f.write(f"    {comment.text}\n")
                    f.write("-"*80 + "\n\n")
        
        print(f"Comments exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting comments to TXT: {e}")

def export_page_comments_to_csv(page_name, comments):
    """Export all comments for a page to CSV file"""
    try:
        # Create DataFrame
        comments_data = []
        for comment in comments:
            comments_data.append({
                'Post ID': comment.post_id,
                'Author': comment.author,
                'Comment': comment.text,
                'Time': comment.comment_time,
                'Likes': comment.likes
            })
        
        df = pd.DataFrame(comments_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_comments_{page_name}_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Comments exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting page comments to CSV: {e}")
        
def export_page_comments_to_txt(page_name, comments):
    """Export all comments for a page to TXT file"""
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_comments_{page_name}_{timestamp}.txt"
        
        # Write to text file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"\nALL COMMENTS FOR PAGE '{page_name}'\n")
            f.write("="*80 + "\n")
            f.write(f"Found {len(comments)} comments\n")
            f.write("="*80 + "\n\n")
            
            if not comments:
                f.write("No comments found.\n")
            else:
                for i, comment in enumerate(comments, 1):
                    f.write(f"#{i} | Post ID: {comment.post_id}\n")
                    f.write(f"    Author: {comment.author} | Likes: {comment.likes}\n")
                    f.write(f"    Time: {comment.comment_time}\n")
                    f.write(f"    {comment.text}\n")
                    f.write("-"*80 + "\n\n")
        
        print(f"Comments exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting page comments to TXT: {e}")

def search_comments(search_term):
    """Search for comments containing a specific term"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            comments = session.query(
                PostComment,
                FacebookPost.page_name
            ).join(
                FacebookPost,
                FacebookPost.post_id == PostComment.post_id
            ).filter(
                PostComment.text.like(f'%{search_term}%')
            ).order_by(
                PostComment.comment_time.desc()
            ).all()
            
            print(f"\nSEARCH RESULTS FOR '{search_term}'")
            print("="*80)
            print(f"Found {len(comments)} matching comments")
            print("="*80)
            
            if not comments:
                print("No matching comments found.")
                return
                
            for i, (comment, page_name) in enumerate(comments, 1):
                print(f"#{i} | Page: {page_name}")
                print(f"    Post ID: {comment.post_id}")
                print(f"    Author: {comment.author} | Likes: {comment.likes}")
                print(f"    Time: {comment.comment_time}")
                print(f"    {comment.text}")
                print("-"*80)
                
                # Break after every 20 comments and ask to continue
                if i % 20 == 0:
                    cont = input(f"Showing {i}/{len(comments)} comments. Continue? (y/n): ").strip().lower()
                    if cont != 'y':
                        break
              # Ask if user wants to export results
            export = input("\nExport search results? (csv/txt/both/n): ").strip().lower()
            if export == 'csv':
                export_search_results_to_csv(search_term, comments)
            elif export == 'txt':
                export_search_results_to_txt(search_term, comments)
            elif export == 'both':
                export_search_results_to_csv(search_term, comments)
                export_search_results_to_txt(search_term, comments)
                
    except Exception as e:
        logger.error(f"Error searching comments for '{search_term}': {e}")

def export_search_results_to_csv(search_term, comments):
    """Export search results to CSV file"""
    try:
        # Create DataFrame
        comments_data = []
        for comment, page_name in comments:
            comments_data.append({
                'Page': page_name,
                'Post ID': comment.post_id,
                'Author': comment.author,
                'Comment': comment.text,
                'Time': comment.comment_time,
                'Likes': comment.likes
            })
        
        df = pd.DataFrame(comments_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_search_term = ''.join(c if c.isalnum() else '_' for c in search_term)
        filename = f"search_{safe_search_term}_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Search results exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting search results to CSV: {e}")

def export_search_results_to_txt(search_term, comments):
    """Export search results to TXT file"""
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_search_term = ''.join(c if c.isalnum() else '_' for c in search_term)
        filename = f"search_{safe_search_term}_{timestamp}.txt"
        
        # Write to text file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"\nSEARCH RESULTS FOR '{search_term}'\n")
            f.write("="*80 + "\n")
            f.write(f"Found {len(comments)} matching comments\n")
            f.write("="*80 + "\n\n")
            
            if not comments:
                f.write("No matching comments found.\n")
            else:
                for i, (comment, page_name) in enumerate(comments, 1):
                    f.write(f"#{i} | Page: {page_name}\n")
                    f.write(f"    Post ID: {comment.post_id}\n")
                    f.write(f"    Author: {comment.author} | Likes: {comment.likes}\n")
                    f.write(f"    Time: {comment.comment_time}\n")
                    f.write(f"    {comment.text}\n")
                    f.write("-"*80 + "\n\n")
        
        print(f"Search results exported to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting search results to TXT: {e}")

def interactive_mode():
    """Run in interactive mode with menu options"""
    while True:
        print("\n" + "="*50)
        print("FACEBOOK COMMENTS VIEWER")
        print("="*50)
        print("1. List all available pages")
        print("2. View all comments for a specific page")
        print("3. View comments for a specific post")
        print("4. Search comments by keyword")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-4): ").strip()
        
        if choice == '0':
            print("Exiting...")
            break
            
        elif choice == '1':
            list_pages()
            
        elif choice == '2':
            pages = get_pages_from_db()
            
            if not pages:
                print("No pages found in the database.")
                continue
                
            print("\nAvailable Pages:")
            for i, page in enumerate(pages, 1):
                print(f"{i}. {page}")
            
            page_choice = input("\nEnter page number or name: ").strip()
            
            # Handle either number or name
            selected_page = None
            if page_choice.isdigit():
                idx = int(page_choice) - 1
                if 0 <= idx < len(pages):
                    selected_page = pages[idx]
            else:
                if page_choice in pages:
                    selected_page = page_choice
            
            if selected_page:
                view_all_comments_for_page(selected_page)
            else:
                print("Invalid page selection.")
                
        elif choice == '3':
            pages = get_pages_from_db()
            
            if not pages:
                print("No pages found in the database.")
                continue
                
            print("\nAvailable Pages:")
            for i, page in enumerate(pages, 1):
                print(f"{i}. {page}")
                
            page_choice = input("\nEnter page number or name: ").strip()
            
            # Handle either number or name
            selected_page = None
            if page_choice.isdigit():
                idx = int(page_choice) - 1
                if 0 <= idx < len(pages):
                    selected_page = pages[idx]
            else:
                if page_choice in pages:
                    selected_page = page_choice
            
            if selected_page:
                post_ids = list_posts_for_page(selected_page)
                
                if post_ids:
                    post_choice = input("\nEnter post number or ID: ").strip()
                    
                    # Handle either number or ID
                    selected_post = None
                    if post_choice.isdigit():
                        idx = int(post_choice) - 1
                        if 0 <= idx < len(post_ids):
                            selected_post = post_ids[idx]
                    else:
                        if post_choice in post_ids:
                            selected_post = post_choice
                    
                    if selected_post:
                        view_comments_for_post(selected_post)
                    else:
                        print("Invalid post selection.")
                
            else:
                print("Invalid page selection.")
                
        elif choice == '4':
            search_term = input("Enter search keyword: ").strip()
            if search_term:
                search_comments(search_term)
            else:
                print("Search term cannot be empty.")
                
        else:
            print("Invalid choice. Please enter a number between 0 and 4.")

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description='View Facebook comments from the database')
    parser.add_argument('--page', type=str, help='View all comments for a specific page')
    parser.add_argument('--post', type=str, help='View comments for a specific post ID')
    parser.add_argument('--search', type=str, help='Search comments containing a specific keyword')
    parser.add_argument('--list-pages', action='store_true', help='List all available pages')
    
    args = parser.parse_args()
    
    # Check database connection
    db = DatabaseManager()
    if not db.health_check():
        logger.error("Database connection failed!")
        return 1
    
    # Handle command line arguments
    if args.list_pages:
        list_pages()
        return 0
        
    if args.page:
        view_all_comments_for_page(args.page)
        return 0
        
    if args.post:
        view_comments_for_post(args.post)
        return 0
        
    if args.search:
        search_comments(args.search)
        return 0
    
    # If no specific arguments, run in interactive mode
    interactive_mode()
    return 0

if __name__ == "__main__":
    try:
        print("Starting view_comments.py...")
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
