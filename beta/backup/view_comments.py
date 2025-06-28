#!/usr/bin/env python
"""
View Facebook Comments Tool
Displays comments from the database with multiple filtering options
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import pandas as pd

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
        print("No Facebook pages found in the database!")
        return None
        
    print("\nAvailable Facebook Pages:")
    print("="*40)
    for i, page in enumerate(pages, 1):
        print(f"{i}. {page}")
    print("="*40)
    
    return pages

def list_posts_for_page(page_name):
    """List all posts for a specific page"""
    db = DatabaseManager()
    posts = []
    
    try:
        with db.session_scope() as session:
            posts = session.query(FacebookPost).filter(
                FacebookPost.page_name == page_name
            ).order_by(FacebookPost.post_time.desc()).all()
            
            if not posts:
                print(f"No posts found for page '{page_name}'!")
                return None
                
            print(f"\nPosts for {page_name}:")
            print("="*80)
            print(f"{'#':<4} {'Post ID':<20} {'Date':<20} {'Likes':<8} {'Comments':<10} {'Text':<50}")
            print("-"*80)
            
            for i, post in enumerate(posts, 1):
                comment_count = session.query(PostComment).filter(
                    PostComment.post_id == post.post_id
                ).count()
                
                post_text = post.post_text or ""
                if len(post_text) > 50:
                    post_text = post_text[:47] + "..."
                    
                post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else "Unknown"
                
                print(f"{i:<4} {post.post_id:<20} {post_date:<20} {post.likes:<8} {comment_count:<10} {post_text:<50}")
            
            print("="*80)
            return posts
            
    except Exception as e:
        logger.error(f"Error listing posts for page {page_name}: {e}")
        return None

def view_comments_for_post(post_id):
    """View all comments for a specific post"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            post = session.query(FacebookPost).filter(
                FacebookPost.post_id == post_id
            ).first()
            
            if not post:
                print(f"Post with ID '{post_id}' not found!")
                return None
                
            comments = session.query(PostComment).filter(
                PostComment.post_id == post_id
            ).order_by(PostComment.comment_time.desc()).all()
            
            if not comments:
                print(f"No comments found for post {post_id}!")
                return None, None
                
            print(f"\nPost from {post.page_name}:")
            print("="*100)
            post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else "Unknown"
            print(f"Date: {post_date}")
            print(f"Likes: {post.likes}, Shares: {post.shares}")
            print("-"*100)
            print(post.post_text)
            print("="*100)
            
            print(f"\nComments ({len(comments)}):")
            print("-"*100)
            
            comments_table = []
            for comment in comments:
                comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else "Unknown"
                comments_table.append([
                    comment.author, 
                    comment_date, 
                    comment.likes, 
                    comment.text
                ])
            
            print(tabulate(
                comments_table, 
                headers=["Author", "Date", "Likes", "Comment"], 
                tablefmt="grid"
            ))
            
            return post, comments
            
    except Exception as e:
        logger.error(f"Error viewing comments for post {post_id}: {e}")
        return None, None

def view_all_comments_for_page(page_name):
    """View all comments for a specific page"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            # Get all posts for the page
            posts = session.query(FacebookPost).filter(
                FacebookPost.page_name == page_name
            ).all()
            
            if not posts:
                print(f"No posts found for page '{page_name}'!")
                return None
                
            post_ids = [post.post_id for post in posts]
            
            # Get all comments for these posts
            comments = session.query(PostComment).filter(
                PostComment.post_id.in_(post_ids)
            ).order_by(PostComment.comment_time.desc()).all()
            
            if not comments:
                print(f"No comments found for any posts on page '{page_name}'!")
                return None
                
            print(f"\nAll Comments for {page_name} ({len(comments)} comments):")
            print("="*100)
            
            # Group comments by post for better readability
            comments_by_post = {}
            for comment in comments:
                if comment.post_id not in comments_by_post:
                    comments_by_post[comment.post_id] = []
                comments_by_post[comment.post_id].append(comment)
            
            all_comments_data = []
            for post in posts:
                if post.post_id in comments_by_post:
                    post_comments = comments_by_post[post.post_id]
                    post_date = post.post_time.strftime("%Y-%m-%d") if post.post_time else "Unknown"
                    
                    print(f"\nPost: {post_date} - {post.post_text[:50]}{'...' if len(post.post_text or '') > 50 else ''}")
                    print(f"Comments: {len(post_comments)}")
                    print("-"*100)
                    
                    comments_table = []
                    for comment in post_comments:
                        comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else "Unknown"
                        comments_table.append([
                            comment.author, 
                            comment_date, 
                            comment.likes, 
                            comment.text
                        ])
                        
                        # Add to the all comments data for export
                        all_comments_data.append({
                            'post_id': post.post_id,
                            'post_date': post_date,
                            'post_text': post.post_text,
                            'author': comment.author,
                            'comment_date': comment_date,
                            'likes': comment.likes,
                            'comment': comment.text
                        })
                    
                    print(tabulate(
                        comments_table, 
                        headers=["Author", "Date", "Likes", "Comment"], 
                        tablefmt="grid"
                    ))
            
            print("="*100)
            return all_comments_data
            
    except Exception as e:
        logger.error(f"Error viewing all comments for page {page_name}: {e}")
        return None

def export_comments_to_csv(post, comments):
    """Export comments for a single post to CSV file"""
    if not post or not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = EXPORTS_DIR / f"comments_{post.page_name}_{timestamp}.csv"
        
        data = []
        for comment in comments:
            comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else ""
            post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else ""
            
            data.append({
                'post_id': post.post_id,
                'page_name': post.page_name,
                'post_date': post_date,
                'post_text': post.post_text,
                'author': comment.author,
                'comment_date': comment_date,
                'likes': comment.likes,
                'comment_text': comment.text
            })
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\nComments successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting comments to CSV: {e}")
        return False

def export_comments_to_txt(post, comments):
    """Export comments for a single post to text file"""
    if not post or not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = EXPORTS_DIR / f"comments_{post.page_name}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"FACEBOOK COMMENTS FROM {post.page_name.upper()}\n")
            f.write("="*80 + "\n\n")
            
            # Post info
            post_date = post.post_time.strftime("%Y-%m-%d %H:%M") if post.post_time else "Unknown"
            f.write(f"POST DATE: {post_date}\n")
            f.write(f"POST ID: {post.post_id}\n")
            f.write(f"LIKES: {post.likes}\n")
            f.write(f"SHARES: {post.shares}\n")
            f.write("\n")
            f.write("POST TEXT:\n")
            f.write("-"*80 + "\n")
            f.write(f"{post.post_text}\n")
            f.write("-"*80 + "\n\n")
            
            # Comments
            f.write(f"COMMENTS ({len(comments)}):\n")
            f.write("="*80 + "\n\n")
            
            for i, comment in enumerate(comments, 1):
                comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else "Unknown"
                f.write(f"COMMENT #{i} - By {comment.author} on {comment_date} (Likes: {comment.likes})\n")
                f.write("-"*80 + "\n")
                f.write(f"{comment.text}\n")
                f.write("-"*80 + "\n\n")
        
        print(f"\nComments successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting comments to text file: {e}")
        return False

def export_page_comments_to_csv(page_name, comments):
    """Export all comments for a page to CSV file"""
    if not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = EXPORTS_DIR / f"all_comments_{page_name}_{timestamp}.csv"
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(comments)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\nAll comments for {page_name} successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting page comments to CSV: {e}")
        return False
        
def export_page_comments_to_txt(page_name, comments):
    """Export all comments for a page to text file"""
    if not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = EXPORTS_DIR / f"all_comments_{page_name}_{timestamp}.txt"
        
        # Group comments by post for better organization
        comments_by_post = {}
        for comment in comments:
            post_id = comment['post_id']
            if post_id not in comments_by_post:
                comments_by_post[post_id] = {
                    'post_text': comment['post_text'],
                    'post_date': comment['post_date'],
                    'comments': []
                }
            comments_by_post[post_id]['comments'].append(comment)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"ALL FACEBOOK COMMENTS FROM {page_name.upper()}\n")
            f.write("="*80 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Comments: {len(comments)}\n")
            f.write("="*80 + "\n\n")
            
            # Write comments organized by post
            for post_id, post_data in comments_by_post.items():
                f.write(f"POST: {post_data['post_date']}\n")
                f.write("-"*80 + "\n")
                f.write(f"{post_data['post_text']}\n")
                f.write("-"*80 + "\n")
                
                for comment in post_data['comments']:
                    f.write(f"\nAuthor: {comment['author']} on {comment['comment_date']} (Likes: {comment['likes']})\n")
                    f.write(f"{comment['comment']}\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        print(f"\nAll comments for {page_name} successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting page comments to text file: {e}")
        return False

def search_comments(search_term):
    """Search for comments containing specific text"""
    db = DatabaseManager()
    
    try:
        with db.session_scope() as session:
            # Search for comments containing the search term
            comments = session.query(PostComment, FacebookPost).join(
                FacebookPost, PostComment.post_id == FacebookPost.post_id
            ).filter(
                PostComment.text.like(f"%{search_term}%")
            ).order_by(PostComment.comment_time.desc()).all()
            
            if not comments:
                print(f"No comments found containing '{search_term}'!")
                return None
                
            print(f"\nSearch Results for '{search_term}' - {len(comments)} comments found:")
            print("="*100)
            
            search_results = []
            for comment, post in comments:
                comment_date = comment.comment_time.strftime("%Y-%m-%d %H:%M") if comment.comment_time else "Unknown"
                post_date = post.post_time.strftime("%Y-%m-%d") if post.post_time else "Unknown"
                
                # Add to results for potential export
                search_results.append({
                    'post_id': post.post_id,
                    'page_name': post.page_name,
                    'post_date': post_date,
                    'post_text': post.post_text,
                    'author': comment.author,
                    'comment_date': comment_date,
                    'likes': comment.likes,
                    'comment': comment.text
                })
            
            # Organize results by page for display
            results_by_page = {}
            for result in search_results:
                page_name = result['page_name']
                if page_name not in results_by_page:
                    results_by_page[page_name] = []
                results_by_page[page_name].append(result)
            
            # Display results grouped by page
            for page_name, results in results_by_page.items():
                print(f"\n{page_name} - {len(results)} results:")
                print("-"*100)
                
                comments_table = []
                for result in results:
                    comments_table.append([
                        result['author'],
                        result['comment_date'],
                        result['likes'],
                        result['comment']
                    ])
                
                print(tabulate(
                    comments_table,
                    headers=["Author", "Date", "Likes", "Comment"],
                    tablefmt="grid"
                ))
            
            return search_results
            
    except Exception as e:
        logger.error(f"Error searching comments for '{search_term}': {e}")
        return None

def export_search_results_to_csv(search_term, comments):
    """Export search results to CSV file"""
    if not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_term = search_term.replace(" ", "_")[:20]  # Sanitize search term for filename
        filename = EXPORTS_DIR / f"search_{sanitized_term}_{timestamp}.csv"
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(comments)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\nSearch results successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting search results to CSV: {e}")
        return False

def export_search_results_to_txt(search_term, comments):
    """Export search results to text file"""
    if not comments:
        return False
    
    try:
        # Make sure directory exists
        EXPORTS_DIR = ROOT_DIR / "exports"
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_term = search_term.replace(" ", "_")[:20]  # Sanitize search term for filename
        filename = EXPORTS_DIR / f"search_{sanitized_term}_{timestamp}.txt"
        
        # Group search results by page for better readability
        results_by_page = {}
        for result in comments:
            page_name = result['page_name']
            if page_name not in results_by_page:
                results_by_page[page_name] = []
            results_by_page[page_name].append(result)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"FACEBOOK COMMENTS SEARCH RESULTS FOR '{search_term}'\n")
            f.write("="*80 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Results: {len(comments)}\n")
            f.write("="*80 + "\n\n")
            
            # Write results organized by page
            for page_name, results in results_by_page.items():
                f.write(f"PAGE: {page_name} - {len(results)} results\n")
                f.write("-"*80 + "\n\n")
                
                for result in results:
                    f.write(f"Post Date: {result['post_date']}\n")
                    f.write(f"Post: {result['post_text'][:50]}{'...' if len(result['post_text'] or '') > 50 else ''}\n")
                    f.write(f"Author: {result['author']} on {result['comment_date']} (Likes: {result['likes']})\n")
                    f.write(f"Comment: {result['comment']}\n")
                    f.write("-"*80 + "\n\n")
                
                f.write("\n")
        
        print(f"\nSearch results successfully exported to: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting search results to text file: {e}")
        return False

def interactive_mode():
    """Run the tool in interactive mode"""
    print("\n" + "="*80)
    print("FACEBOOK COMMENTS VIEWER - INTERACTIVE MODE")
    print("="*80 + "\n")
    
    while True:
        print("\nMAIN MENU:")
        print("1. View pages")
        print("2. View posts for a page")
        print("3. View comments for a post")
        print("4. View all comments for a page")
        print("5. Search comments")
        print("0. Exit")
        
        try:
            choice = input("\nEnter your choice (0-5): ").strip()
            
            if choice == "0":
                print("\nExiting Facebook Comments Viewer. Goodbye!")
                break
                
            elif choice == "1":
                pages = list_pages()
                if pages:
                    sub_choice = input("\nDo you want to view posts for a page? (y/n): ").strip().lower()
                    if sub_choice == 'y':
                        page_num = int(input(f"Enter page number (1-{len(pages)}): ").strip())
                        if 1 <= page_num <= len(pages):
                            list_posts_for_page(pages[page_num-1])
                
            elif choice == "2":
                pages = list_pages()
                if pages:
                    page_num = int(input(f"Enter page number (1-{len(pages)}): ").strip())
                    if 1 <= page_num <= len(pages):
                        selected_page = pages[page_num-1]
                        posts = list_posts_for_page(selected_page)
                        
                        if posts:
                            sub_choice = input("\nDo you want to view comments for a post? (y/n): ").strip().lower()
                            if sub_choice == 'y':
                                post_num = int(input(f"Enter post number (1-{len(posts)}): ").strip())
                                if 1 <= post_num <= len(posts):
                                    post, comments = view_comments_for_post(posts[post_num-1].post_id)
                                    
                                    if post and comments:
                                        export_choice = input("\nDo you want to export these comments? (csv/txt/no): ").strip().lower()
                                        if export_choice == 'csv':
                                            export_comments_to_csv(post, comments)
                                        elif export_choice == 'txt':
                                            export_comments_to_txt(post, comments)
                
            elif choice == "3":
                post_id = input("Enter the Post ID: ").strip()
                post, comments = view_comments_for_post(post_id)
                
                if post and comments:
                    export_choice = input("\nDo you want to export these comments? (csv/txt/no): ").strip().lower()
                    if export_choice == 'csv':
                        export_comments_to_csv(post, comments)
                    elif export_choice == 'txt':
                        export_comments_to_txt(post, comments)
                
            elif choice == "4":
                pages = list_pages()
                if pages:
                    page_num = int(input(f"Enter page number (1-{len(pages)}): ").strip())
                    if 1 <= page_num <= len(pages):
                        selected_page = pages[page_num-1]
                        comments_data = view_all_comments_for_page(selected_page)
                        
                        if comments_data:
                            export_choice = input("\nDo you want to export all these comments? (csv/txt/no): ").strip().lower()
                            if export_choice == 'csv':
                                export_page_comments_to_csv(selected_page, comments_data)
                            elif export_choice == 'txt':
                                export_page_comments_to_txt(selected_page, comments_data)
                
            elif choice == "5":
                search_term = input("Enter search term: ").strip()
                if search_term:
                    search_results = search_comments(search_term)
                    
                    if search_results:
                        export_choice = input("\nDo you want to export these search results? (csv/txt/no): ").strip().lower()
                        if export_choice == 'csv':
                            export_search_results_to_csv(search_term, search_results)
                        elif export_choice == 'txt':
                            export_search_results_to_txt(search_term, search_results)
                            
            else:
                print("Invalid choice. Please enter a number between 0-5.")
                
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"An error occurred: {e}")
            logger.error(f"Error in interactive mode: {e}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Facebook Comments Viewer')
    parser.add_argument('--page', type=str, help='View posts for a specific page')
    parser.add_argument('--post', type=str, help='View comments for a specific post ID')
    parser.add_argument('--search', type=str, help='Search for comments containing text')
    parser.add_argument('--export', choices=['csv', 'txt'], help='Export results to CSV or text file')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    return parser.parse_args()

def main():
    """Main function"""
    # Ensure directories exist
    EXPORTS_DIR = ROOT_DIR / "exports"
    EXPORTS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Parse command line arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "="*80)
    print("FACEBOOK COMMENTS VIEWER")
    print("="*80)
    
    # Check database connection
    db = DatabaseManager()
    if not db.health_check():
        print("Error: Database connection failed. Check configuration.")
        return 1
    
    # Interactive mode
    if args.interactive or (not args.page and not args.post and not args.search):
        interactive_mode()
        return 0
    
    # Handle command line options
    if args.page:
        if args.post:
            # View specific post
            post, comments = view_comments_for_post(args.post)
            if post and comments and args.export:
                if args.export == 'csv':
                    export_comments_to_csv(post, comments)
                elif args.export == 'txt':
                    export_comments_to_txt(post, comments)
        else:
            # View all posts/comments for a page
            posts = list_posts_for_page(args.page)
            
            if posts and args.export:
                all_comments = view_all_comments_for_page(args.page)
                if all_comments:
                    if args.export == 'csv':
                        export_page_comments_to_csv(args.page, all_comments)
                    elif args.export == 'txt':
                        export_page_comments_to_txt(args.page, all_comments)
    
    elif args.post:
        # View specific post's comments
        post, comments = view_comments_for_post(args.post)
        if post and comments and args.export:
            if args.export == 'csv':
                export_comments_to_csv(post, comments)
            elif args.export == 'txt':
                export_comments_to_txt(post, comments)
    
    elif args.search:
        # Search for comments
        search_results = search_comments(args.search)
        if search_results and args.export:
            if args.export == 'csv':
                export_search_results_to_csv(args.search, search_results)
            elif args.export == 'txt':
                export_search_results_to_txt(args.search, search_results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
