#!/usr/bin/env python3
"""
AI Analysis Runner
Analyzes all scraped data from the database and generates comprehensive AI reports
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ml.ai_analyzer import AIAnalyzer


def load_data_from_db():
    """Load scraped data from database"""
    try:
        from db.database import SessionLocal, Post, Comment
        
        session = SessionLocal()
        
        # Load posts
        posts = session.query(Post).all()
        posts_data = [
            {
                "id": p.id,
                "content": p.content,
                "text": p.text if hasattr(p, 'text') else p.content,
                "likes": p.likes if hasattr(p, 'likes') else 0,
                "shares": p.shares if hasattr(p, 'shares') else 0,
                "comments_count": p.comments_count if hasattr(p, 'comments_count') else 0,
                "date": str(p.created_at) if hasattr(p, 'created_at') else None,
                "page_name": p.page_name if hasattr(p, 'page_name') else 'Unknown'
            }
            for p in posts
        ]
        
        # Load comments
        comments = session.query(Comment).all()
        comments_data = [
            {
                "id": c.id,
                "text": c.text if hasattr(c, 'text') else c.content if hasattr(c, 'content') else '',
                "author": c.author if hasattr(c, 'author') else '',
                "post_id": c.post_id if hasattr(c, 'post_id') else None
            }
            for c in comments
        ]
        
        session.close()
        return posts_data, comments_data
        
    except Exception as e:
        print(f"⚠ Could not load from database: {e}")
        return [], []


def load_data_from_json(file_path: str):
    """Load data from JSON export file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # Assume it's posts
            return data, []
        elif isinstance(data, dict):
            posts = data.get('posts', [])
            comments = data.get('comments', [])
            return posts, comments
        
        return [], []
    except Exception as e:
        print(f"⚠ Could not load from JSON: {e}")
        return [], []


def load_sample_data():
    """Load sample data for demonstration"""
    posts = [
        {
            "content": "🚀 Exciting news! Our new product launch has exceeded all expectations. Thank you to our amazing community for your support! #Success #Innovation",
            "likes": 2500,
            "shares": 450,
            "comments_count": 320,
            "date": "2026-02-01 10:30:00",
            "page_name": "TechStartup"
        },
        {
            "content": "We're aware of the technical issues some users are experiencing. Our team is working around the clock to resolve this. Updates coming soon.",
            "likes": 150,
            "shares": 25,
            "comments_count": 890,
            "date": "2026-02-02 14:00:00",
            "page_name": "TechStartup"
        },
        {
            "content": "Behind the scenes look at our development team! These folks work tirelessly to bring you the best experience. 💪 #TeamWork #BehindTheScenes",
            "likes": 1800,
            "shares": 120,
            "comments_count": 95,
            "date": "2026-02-03 09:15:00",
            "page_name": "TechStartup"
        },
        {
            "content": "New feature alert! 🎉 You can now customize your dashboard with widgets. Check out our blog for the full tutorial.",
            "likes": 980,
            "shares": 200,
            "comments_count": 75,
            "date": "2026-02-04 11:45:00",
            "page_name": "TechStartup"
        },
        {
            "content": "Happy Friday everyone! What features would you like to see next? Drop your suggestions in the comments 👇",
            "likes": 650,
            "shares": 30,
            "comments_count": 420,
            "date": "2026-02-05 16:00:00",
            "page_name": "TechStartup"
        }
    ]
    
    comments = [
        {"text": "This is amazing! Love the new features!", "author": "user_alice"},
        {"text": "When will this be available in Europe?", "author": "user_bob"},
        {"text": "Great work team! Keep it up 🔥", "author": "user_charlie"},
        {"text": "Having issues with login. Please help!", "author": "user_david"},
        {"text": "Best product I've ever used. Highly recommended!", "author": "user_eve"},
        {"text": "The customer support is terrible...", "author": "user_frank"},
        {"text": "Any plans for mobile app?", "author": "user_grace"},
        {"text": "Thanks for listening to our feedback!", "author": "user_alice"},
        {"text": "This update broke my workflow 😤", "author": "user_henry"},
        {"text": "Can't wait for the next release!", "author": "user_ivy"},
        {"text": "Please add dark mode!", "author": "user_jack"},
        {"text": "Awesome feature request system", "author": "user_kate"},
        {"text": "Why is the pricing so high?", "author": "user_leo"},
        {"text": "Integration with Slack would be great", "author": "user_maya"},
        {"text": "Love this community! 💖", "author": "user_nina"},
    ]
    
    return posts, comments


def main():
    parser = argparse.ArgumentParser(
        description="AI Analysis of Facebook Scraper Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ai_analysis.py --source db
  python run_ai_analysis.py --source json --input data/posts.json
  python run_ai_analysis.py --source sample --output reports/
  python run_ai_analysis.py --source db --format both
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        choices=['db', 'json', 'sample'],
        default='sample',
        help='Data source: db (database), json (file), sample (demo data)'
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input JSON file path (required for json source)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='reports',
        help='Output directory for reports (default: reports/)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'txt', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 AI ANALYSIS - Facebook Data Analyzer")
    print("=" * 60)
    print()
    
    # Load data based on source
    print(f"📥 Loading data from: {args.source}")
    
    if args.source == 'db':
        posts, comments = load_data_from_db()
    elif args.source == 'json':
        if not args.input:
            print("❌ Error: --input required for json source")
            sys.exit(1)
        posts, comments = load_data_from_json(args.input)
    else:
        posts, comments = load_sample_data()
    
    if not posts:
        print("❌ No data to analyze!")
        sys.exit(1)
    
    print(f"  ✓ Loaded {len(posts)} posts and {len(comments)} comments")
    print()
    
    # Initialize AI Analyzer
    print("🧠 Initializing AI Analyzer...")
    analyzer = AIAnalyzer()
    print()
    
    # Run analysis
    print("🔬 Running comprehensive AI analysis...")
    analysis = analyzer.analyze_all(posts, comments)
    print("  ✓ Analysis complete!")
    print()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export results
    print("📤 Exporting results...")
    
    if args.format in ['json', 'both']:
        json_path = output_dir / f"ai_analysis_{timestamp}.json"
        analyzer.export_analysis(analysis, str(json_path), format='json')
    
    if args.format in ['txt', 'both']:
        txt_path = output_dir / f"ai_report_{timestamp}.txt"
        report = analyzer.generate_report(analysis, str(txt_path))
        
        # Also print report to console
        print()
        print(report)
    
    print()
    print("=" * 60)
    print("✅ AI Analysis Complete!")
    print(f"📁 Reports saved to: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
