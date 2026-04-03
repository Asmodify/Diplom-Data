#!/usr/bin/env python3
"""
Facebook Scraper v2.0 - Main Entry Point
=========================================

Usage:
    python run.py                    # Interactive mode
    python run.py scrape <url>       # Scrape single page
    python run.py scrape --file pages.txt   # Scrape from file
    python run.py auto               # Auto-scraper (continuous)
    python run.py api                # Start API server
    python run.py analyze <post_id>  # Analyze post comments
    python run.py export             # Export data
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config
from utils.helpers import setup_logging


def setup_environment():
    """Setup environment and logging."""
    config = get_config()
    
    # Setup logging
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    log_file = None
    
    if config.logging.log_to_file:
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"scraper_{datetime.now():%Y%m%d}.log"
        
    setup_logging(level=log_level, log_file=str(log_file) if log_file else None)
    
    return config


def cmd_scrape(args):
    """Handle scrape command."""
    from db.database import DatabaseManager
    from core.scraper import Scraper
    
    logger = logging.getLogger(__name__)
    config = setup_environment()
    
    scraper = Scraper(config)
    
    try:
        # Start the scraper
        if not scraper.start():
            logger.error("Failed to start scraper")
            return
            
        # Login to Facebook
        if not scraper.login():
            logger.error("Failed to login to Facebook")
            return
            
        if args.file:
            # Scrape from file
            logger.info(f"Scraping pages from file: {args.file}")
            results = scraper.scrape_from_file(
                args.file,
                max_posts_per_page=args.max_posts,
            )
            logger.info(f"Completed. Scraped {len(results)} pages.")
            
        elif args.url:
            # Scrape single URL
            logger.info(f"Scraping: {args.url}")
            posts_scraped = scraper.scrape_page(
                args.url,
                max_posts=args.max_posts,
            )
            if posts_scraped > 0:
                logger.info(f"Success: {posts_scraped} posts scraped")
            else:
                logger.error("Scraping failed or no posts found")
                
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping error: {e}", exc_info=True)
    finally:
        scraper.stop()
        

def cmd_auto(args):
    """Handle auto-scraper command."""
    from db.database import DatabaseManager
    from core.scraper import AutoScraper
    
    logger = logging.getLogger(__name__)
    config = setup_environment()
    
    db = DatabaseManager()
    auto_scraper = AutoScraper(db)
    
    try:
        logger.info("Starting auto-scraper...")
        logger.info(f"Interval: {args.interval} minutes")
        
        auto_scraper.run(
            pages_file=args.file or "pages.txt",
            interval_minutes=args.interval,
        )
        
    except KeyboardInterrupt:
        logger.info("Auto-scraper stopped by user")
    except Exception as e:
        logger.error(f"Auto-scraper error: {e}", exc_info=True)
    finally:
        auto_scraper.stop()
        

def cmd_api(args):
    """Handle API server command."""
    import uvicorn
    
    logger = logging.getLogger(__name__)
    config = setup_environment()
    
    logger.info(f"Starting API server on {args.host}:{args.port}")
    
    uvicorn.run(
        "api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    

def cmd_analyze(args):
    """Handle analyze command."""
    from db.database import DatabaseManager
    from ml.analyzer import DataAnalyzer
    from ml.ai_analyzer import AIAnalyzer
    
    logger = logging.getLogger(__name__)
    config = setup_environment()
    
    db = DatabaseManager()
    
    try:
        if args.ai:
            # AI-powered comprehensive analysis
            ai_analyzer = AIAnalyzer(config)
            
            # Get posts and comments from database
            posts = db.get_all_posts(limit=args.limit)
            all_comments = []
            for post in posts:
                comments = db.get_comments_by_post(post.get('post_id') or post.get('id'))
                if comments:
                    all_comments.extend(comments)
            
            logger.info(f"Running AI analysis on {len(posts)} posts and {len(all_comments)} comments...")
            
            # Run comprehensive analysis
            analysis = ai_analyzer.analyze_all(posts, all_comments)
            
            # Generate and print report
            report = ai_analyzer.generate_report(analysis)
            print(report)
            
            # Export if requested
            if args.output:
                ai_analyzer.export_analysis(analysis, args.output, 'json')
                logger.info(f"Analysis exported to {args.output}")
                
        elif args.post_id:
            # Analyze single post
            analyzer = DataAnalyzer(config)
            comments = db.get_comments_by_post(args.post_id)
            if not comments:
                logger.error(f"No comments found for post {args.post_id}")
                return
                
            result = analyzer.analyze_comments(comments)
            
            print("\n=== Analysis Results ===")
            print(f"Total Comments: {result['total_comments']}")
            print(f"Analyzed: {result['analyzed_count']}")
            print(f"Average Sentiment: {result['avg_sentiment']:.3f}")
            print(f"\nDistribution:")
            for label, count in result['sentiment_distribution'].items():
                print(f"  {label}: {count}")
            print(f"\nTop Keywords:")
            for word, count in result['keywords'][:10]:
                print(f"  {word}: {count}")
                
        elif args.all:
            # Analyze all posts with basic analyzer
            analyzer = DataAnalyzer(config)
            posts = db.get_all_posts(limit=args.limit)
            logger.info(f"Analyzing {len(posts)} posts...")
            
            for post in posts:
                comments = db.get_comments_by_post(post.get('post_id') or post.get('id'))
                if comments:
                    result = analyzer.analyze_comments(comments)
                    # Update post sentiment in DB
                    db.update_post_sentiment(post['id'], result['avg_sentiment'])
                    
            logger.info("Analysis complete")
            
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        

def cmd_export(args):
    """Handle export command."""
    from db.database import DatabaseManager
    import json
    import csv
    
    logger = logging.getLogger(__name__)
    config = setup_environment()
    
    db = DatabaseManager()
    export_dir = PROJECT_ROOT / "exports"
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if args.type == 'pages' or args.type == 'all':
            pages = db.get_pages(limit=10000)
            output_file = export_dir / f"pages_{timestamp}.{args.format}"
            _export_data(pages, output_file, args.format)
            logger.info(f"Exported {len(pages)} pages to {output_file}")
            
        if args.type == 'posts' or args.type == 'all':
            posts = db.get_all_posts(limit=10000)
            output_file = export_dir / f"posts_{timestamp}.{args.format}"
            _export_data(posts, output_file, args.format)
            logger.info(f"Exported {len(posts)} posts to {output_file}")
            
        if args.type == 'comments' or args.type == 'all':
            comments = db.get_all_comments(limit=50000)
            output_file = export_dir / f"comments_{timestamp}.{args.format}"
            _export_data(comments, output_file, args.format)
            logger.info(f"Exported {len(comments)} comments to {output_file}")
            
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        

def _export_data(data: list, output_file: Path, format: str):
    """Export data to file."""
    if format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    elif format == 'csv':
        if not data:
            return
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


def cmd_interactive(args):
    """Interactive mode."""
    config = setup_environment()
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("  Facebook Scraper v2.0 - Interactive Mode")
    print("="*60)
    print("\nCommands:")
    print("  1. Scrape single page")
    print("  2. Scrape from file")
    print("  3. Start auto-scraper")
    print("  4. Start API server")
    print("  5. Analyze data")
    print("  6. Export data")
    print("  7. Database status")
    print("  0. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter command number: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                url = input("Enter Facebook page URL: ").strip()
                if url:
                    class Args:
                        pass
                    a = Args()
                    a.url = url
                    a.file = None
                    a.max_posts = 10
                    a.max_comments = 50
                    a.no_comments = False
                    cmd_scrape(a)
            elif choice == '2':
                file = input("Enter file path [pages.txt]: ").strip() or "pages.txt"
                class Args:
                    pass
                a = Args()
                a.url = None
                a.file = file
                a.max_posts = 10
                a.max_comments = 50
                a.no_comments = False
                cmd_scrape(a)
            elif choice == '3':
                class Args:
                    pass
                a = Args()
                a.file = "pages.txt"
                a.interval = 60
                cmd_auto(a)
            elif choice == '4':
                class Args:
                    pass
                a = Args()
                a.host = "0.0.0.0"
                a.port = 8000
                a.reload = False
                cmd_api(a)
            elif choice == '5':
                print("\nAnalysis options:")
                print("  1. Analyze single post")
                print("  2. Analyze all posts (basic)")
                print("  3. AI-powered comprehensive analysis")
                analyze_choice = input("Select option: ").strip()
                
                class Args:
                    pass
                a = Args()
                a.ai = False
                a.output = None
                
                if analyze_choice == '1':
                    post_id = input("Enter post ID: ").strip()
                    a.post_id = int(post_id)
                    a.all = False
                    a.limit = 100
                elif analyze_choice == '2':
                    a.post_id = None
                    a.all = True
                    a.limit = 100
                elif analyze_choice == '3':
                    a.post_id = None
                    a.all = False
                    a.ai = True
                    a.limit = int(input("Max posts to analyze [100]: ").strip() or 100)
                    output = input("Export to file (leave blank to skip): ").strip()
                    a.output = output if output else None
                else:
                    print("Invalid option")
                    continue
                cmd_analyze(a)
            elif choice == '6':
                class Args:
                    pass
                a = Args()
                a.type = 'all'
                a.format = 'json'
                cmd_export(a)
            elif choice == '7':
                from db.database import DatabaseManager
                db = DatabaseManager()
                stats = db.get_statistics()
                print("\n=== Database Status ===")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print()
            else:
                print("Invalid command")
                
        except KeyboardInterrupt:
            print("\nInterrupted")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Facebook Scraper v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape Facebook pages')
    scrape_parser.add_argument('url', nargs='?', help='Page URL to scrape')
    scrape_parser.add_argument('--file', '-f', help='File with page URLs')
    scrape_parser.add_argument('--max-posts', '-p', type=int, default=10, help='Max posts per page')
    scrape_parser.add_argument('--max-comments', '-c', type=int, default=50, help='Max comments per post')
    scrape_parser.add_argument('--no-comments', action='store_true', help='Skip comments')
    
    # Auto command
    auto_parser = subparsers.add_parser('auto', help='Start auto-scraper')
    auto_parser.add_argument('--file', '-f', default='pages.txt', help='Pages file')
    auto_parser.add_argument('--interval', '-i', type=int, default=60, help='Interval in minutes')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start API server')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host address')
    api_parser.add_argument('--port', '-p', type=int, default=8000, help='Port number')
    api_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze data')
    analyze_parser.add_argument('post_id', nargs='?', type=int, help='Post ID to analyze')
    analyze_parser.add_argument('--all', '-a', action='store_true', help='Analyze all posts')
    analyze_parser.add_argument('--ai', action='store_true', help='Use AI-powered comprehensive analysis')
    analyze_parser.add_argument('--limit', '-l', type=int, default=100, help='Limit for all mode')
    analyze_parser.add_argument('--output', '-o', help='Output file for AI analysis results')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--type', '-t', default='all', choices=['pages', 'posts', 'comments', 'all'])
    export_parser.add_argument('--format', '-f', default='json', choices=['json', 'csv'])
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        if not args.url and not args.file:
            scrape_parser.error("Either URL or --file is required")
        cmd_scrape(args)
    elif args.command == 'auto':
        cmd_auto(args)
    elif args.command == 'api':
        cmd_api(args)
    elif args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'export':
        cmd_export(args)
    else:
        # Interactive mode
        cmd_interactive(args)


if __name__ == "__main__":
    main()
