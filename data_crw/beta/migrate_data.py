"""
Data Migration Script
Interactive script to migrate data between PostgreSQL, Firebase, and Google Sheets
"""
import sys
import os
sys.path.insert(0, '.')

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_prerequisites():
    """Check that required credentials are available"""
    print_header("CHECKING PREREQUISITES")
    
    issues = []
    
    # Check Firebase
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    firebase_paths = [
        Path(__file__).parent / 'firebase_credentials.json',
        Path(__file__).parent / 'serviceAccountKey.json',
    ]
    firebase_found = False
    for path in firebase_paths:
        if path.exists():
            print(f"✓ Firebase credentials: {path.name}")
            firebase_found = True
            break
    if not firebase_found and firebase_creds and Path(firebase_creds).exists():
        print(f"✓ Firebase credentials: {firebase_creds}")
        firebase_found = True
    if not firebase_found:
        print("✗ Firebase credentials NOT found")
        issues.append("Firebase")
    
    # Check Google Sheets
    sheets_creds = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    sheets_paths = [
        Path(__file__).parent / 'google_credentials.json',
        Path(__file__).parent / 'service_account.json',
    ]
    sheets_found = False
    for path in sheets_paths:
        if path.exists():
            print(f"✓ Google Sheets credentials: {path.name}")
            sheets_found = True
            break
    if not sheets_found and sheets_creds and Path(sheets_creds).exists():
        print(f"✓ Google Sheets credentials: {sheets_creds}")
        sheets_found = True
    if not sheets_found:
        print("⚠ Google Sheets credentials NOT found (optional)")
    
    # Check PostgreSQL
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_db = os.getenv('POSTGRES_DB', 'facebook_scraper')
    print(f"✓ PostgreSQL config: {pg_host}/{pg_db}")
    
    return issues


def migrate_postgres_to_firebase():
    """Migrate PostgreSQL data to Firebase"""
    print_header("MIGRATE: PostgreSQL → Firebase")
    
    try:
        from data_exporter import DataExporter
        exporter = DataExporter()
        
        # Connect to PostgreSQL
        print("\n1. Connecting to PostgreSQL...")
        if not exporter.connect_postgres():
            print("   ✗ Failed to connect to PostgreSQL")
            return False
        
        # Connect to Firebase
        print("\n2. Connecting to Firebase...")
        if not exporter.connect_firebase():
            print("   ✗ Failed to connect to Firebase")
            return False
        
        # Get count first
        print("\n3. Counting records in PostgreSQL...")
        data = exporter.get_postgres_data()
        post_count = len(data['posts'])
        image_count = len(data['images'])
        comment_count = len(data['comments'])
        print(f"   Found: {post_count} posts, {image_count} images, {comment_count} comments")
        
        if post_count == 0:
            print("\n   No data to migrate!")
            return True
        
        # Confirm migration
        confirm = input(f"\n4. Migrate all {post_count} posts to Firebase? (y/n): ").strip().lower()
        if confirm != 'y':
            print("   Migration cancelled")
            return False
        
        # Do migration
        print("\n5. Migrating data...")
        counts = exporter.migrate_postgres_to_firebase()
        
        print(f"\n✓ Migration complete!")
        print(f"   Posts migrated: {counts['posts']}")
        print(f"   Images migrated: {counts['images']}")
        print(f"   Comments migrated: {counts['comments']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_to_sheets():
    """Export data to Google Sheets"""
    print_header("EXPORT: Firebase → Google Sheets")
    
    try:
        from data_exporter import DataExporter
        exporter = DataExporter()
        
        # Connect to Firebase
        print("\n1. Connecting to Firebase...")
        if not exporter.connect_firebase():
            print("   ✗ Failed to connect to Firebase")
            return False
        
        # Connect to Google Sheets
        print("\n2. Connecting to Google Sheets...")
        if not exporter.connect_sheets():
            print("   ✗ Failed to connect to Google Sheets")
            return False
        
        # Get spreadsheet name
        default_name = "Facebook Scraper Data Export"
        name = input(f"\n3. Spreadsheet name [{default_name}]: ").strip()
        if not name:
            name = default_name
        
        # Include analysis?
        include_analysis = input("4. Include ML analysis results? (y/n) [y]: ").strip().lower()
        include_analysis = include_analysis != 'n'
        
        # Do export
        print("\n5. Exporting to Google Sheets...")
        url = exporter.migrate_firebase_to_sheets(name, include_analysis)
        
        if url:
            print(f"\n✓ Export complete!")
            print(f"   Spreadsheet URL: {url}")
        else:
            print("\n⚠ Export completed but no URL returned")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_ml_analysis():
    """Run ML analysis on Firebase data"""
    print_header("RUN: ML Analysis on Firebase Data")
    
    try:
        from db.firebase_db import get_firebase_db
        from ml.analyzer import DataAnalyzer
        
        # Connect to Firebase
        print("\n1. Connecting to Firebase...")
        db = get_firebase_db()
        
        # Get posts
        print("\n2. Fetching posts from Firebase...")
        posts = db.get_all_posts(limit=1000)
        post_count = len(posts)
        print(f"   Found {post_count} posts")
        
        if post_count == 0:
            print("\n   No posts to analyze!")
            return True
        
        # Initialize analyzer
        print("\n3. Initializing ML analyzer...")
        analyzer = DataAnalyzer()
        
        # Confirm
        confirm = input(f"\n4. Run analysis on {post_count} posts? (y/n): ").strip().lower()
        if confirm != 'y':
            print("   Analysis cancelled")
            return False
        
        # Run analysis
        print("\n5. Running sentiment analysis...")
        sentiments = analyzer.analyze_sentiment(posts)
        print(f"   Analyzed {len(sentiments)} posts")
        
        print("\n6. Running topic classification...")
        topics = analyzer.classify_topics(posts)
        print(f"   Classified {len(topics)} posts")
        
        print("\n7. Running engagement prediction...")
        engagement = analyzer.predict_engagement(posts)
        print(f"   Predicted {len(engagement)} posts")
        
        # Save results to Firebase
        print("\n8. Saving results to Firebase...")
        saved_count = 0
        for post_id in sentiments:
            try:
                db.save_analysis_result(post_id, 'sentiment', sentiments.get(post_id, {}))
                db.save_analysis_result(post_id, 'topic', topics.get(post_id, {}))
                db.save_analysis_result(post_id, 'engagement', engagement.get(post_id, {}))
                saved_count += 1
            except Exception as e:
                print(f"   ⚠ Failed to save analysis for {post_id}: {e}")
        
        print(f"\n✓ Analysis complete!")
        print(f"   Analyzed and saved: {saved_count} posts")
        
        # Show summary
        stats = analyzer.get_summary_stats(posts)
        print(f"\n   Sentiment distribution: {stats.get('sentiment_distribution', {})}")
        print(f"   Engagement distribution: {stats.get('engagement_distribution', {})}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main interactive menu"""
    print_header("FACEBOOK SCRAPER DATA MIGRATION TOOL")
    
    # Check prerequisites
    issues = check_prerequisites()
    
    if issues:
        print(f"\n⚠ Missing credentials: {', '.join(issues)}")
        print("   See ML_CLOUD_GUIDE.md for setup instructions")
    
    while True:
        print("\n" + "-" * 40)
        print("OPTIONS:")
        print("  1. Migrate PostgreSQL → Firebase")
        print("  2. Export Firebase → Google Sheets")
        print("  3. Run ML Analysis on Firebase data")
        print("  4. Test Firebase connection")
        print("  5. Test Google Sheets connection")
        print("  6. Test API server")
        print("  0. Exit")
        print("-" * 40)
        
        choice = input("Select option: ").strip()
        
        if choice == '0':
            print("\nGoodbye!")
            break
        elif choice == '1':
            migrate_postgres_to_firebase()
        elif choice == '2':
            export_to_sheets()
        elif choice == '3':
            run_ml_analysis()
        elif choice == '4':
            import test_firebase
            test_firebase.test_firebase_connection()
        elif choice == '5':
            import test_sheets
            test_sheets.test_google_sheets_connection()
        elif choice == '6':
            import test_api
            test_api.test_api_endpoints()
        else:
            print("Invalid option. Please try again.")


if __name__ == '__main__':
    main()
