"""
Data Exporter Module
Provides utilities for migrating data between PostgreSQL, Firebase, and Google Sheets
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

# Database imports
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Local imports
try:
    from db.config import get_database_url
    from db.models import FacebookPost, PostImage, PostComment
    from db.firebase_db import FirebaseDB, get_firebase_db
    from integrations.google_sheets import GoogleSheetsExporter
except ImportError:
    from .db.config import get_database_url
    from .db.models import FacebookPost, PostImage, PostComment
    from .db.firebase_db import FirebaseDB, get_firebase_db
    from .integrations.google_sheets import GoogleSheetsExporter


class DataExporter:
    """
    Utility class for migrating and exporting data between different storage systems
    """
    
    def __init__(self):
        """Initialize the data exporter"""
        self.pg_session = None
        self.firebase_db = None
        self.sheets_exporter = None
    
    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL database"""
        if not SQLALCHEMY_AVAILABLE:
            print("⚠ SQLAlchemy not available")
            return False
        
        try:
            engine = create_engine(get_database_url())
            Session = sessionmaker(bind=engine)
            self.pg_session = Session()
            print("✓ Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            return False
    
    def connect_firebase(self, credentials_path: Optional[str] = None) -> bool:
        """Connect to Firebase Firestore"""
        try:
            self.firebase_db = get_firebase_db(credentials_path)
            print("✓ Connected to Firebase")
            return True
        except Exception as e:
            print(f"✗ Firebase connection failed: {e}")
            return False
    
    def connect_sheets(self, credentials_path: Optional[str] = None) -> bool:
        """Connect to Google Sheets"""
        try:
            self.sheets_exporter = GoogleSheetsExporter(credentials_path)
            print("✓ Connected to Google Sheets")
            return True
        except Exception as e:
            print(f"✗ Google Sheets connection failed: {e}")
            return False
    
    # ==================== PostgreSQL Export ====================
    
    def get_postgres_data(self, limit: int = None) -> Dict[str, List[Dict]]:
        """
        Get all data from PostgreSQL
        
        Returns:
            Dictionary with 'posts', 'images', and 'comments' lists
        """
        if not self.pg_session:
            if not self.connect_postgres():
                return {'posts': [], 'images': [], 'comments': []}
        
        # Query posts
        query = self.pg_session.query(FacebookPost)
        if limit:
            query = query.limit(limit)
        posts = query.all()
        
        # Convert to dictionaries
        posts_data = []
        images_data = []
        comments_data = []
        
        for post in posts:
            post_dict = {
                'post_id': post.post_id,
                'page_name': post.page_name,
                'post_url': post.post_url,
                'content': post.content,
                'timestamp': post.timestamp.isoformat() if post.timestamp else None,
                'likes': post.likes or 0,
                'shares': post.shares or 0,
                'comment_count': post.comment_count or 0,
                'scraped_at': post.scraped_at.isoformat() if post.scraped_at else None
            }
            posts_data.append(post_dict)
            
            # Get images
            for image in post.images:
                images_data.append({
                    'post_id': post.post_id,
                    'image_url': image.image_url,
                    'local_path': image.local_path,
                    'downloaded_at': image.downloaded_at.isoformat() if image.downloaded_at else None
                })
            
            # Get comments
            for comment in post.comments:
                comments_data.append({
                    'post_id': post.post_id,
                    'comment_id': comment.comment_id,
                    'author_name': comment.author_name,
                    'author_url': comment.author_url,
                    'content': comment.content,
                    'timestamp': comment.timestamp.isoformat() if comment.timestamp else None,
                    'likes': comment.likes or 0,
                    'reply_to_id': comment.reply_to_id,
                    'scraped_at': comment.scraped_at.isoformat() if comment.scraped_at else None
                })
        
        return {
            'posts': posts_data,
            'images': images_data,
            'comments': comments_data
        }
    
    # ==================== Migration Methods ====================
    
    def migrate_postgres_to_firebase(self, limit: int = None) -> Dict[str, int]:
        """
        Migrate all data from PostgreSQL to Firebase Firestore
        
        Args:
            limit: Optional limit on number of posts to migrate
            
        Returns:
            Dictionary with counts of migrated items
        """
        print("Starting PostgreSQL to Firebase migration...")
        
        # Get PostgreSQL data
        data = self.get_postgres_data(limit)
        
        if not data['posts']:
            print("No data found in PostgreSQL")
            return {'posts': 0, 'images': 0, 'comments': 0}
        
        # Connect to Firebase
        if not self.firebase_db:
            if not self.connect_firebase():
                return {'posts': 0, 'images': 0, 'comments': 0}
        
        # Migrate data
        counts = self.firebase_db.import_from_postgres(
            posts=data['posts'],
            images=data['images'],
            comments=data['comments']
        )
        
        print(f"✓ Migration complete: {counts['posts']} posts, "
              f"{counts['images']} images, {counts['comments']} comments")
        
        return counts
    
    def migrate_firebase_to_sheets(self, spreadsheet_name: str,
                                    include_analysis: bool = True) -> str:
        """
        Export Firebase data to Google Sheets
        
        Args:
            spreadsheet_name: Name for the Google Spreadsheet
            include_analysis: Whether to include ML analysis results
            
        Returns:
            URL of the created spreadsheet
        """
        print("Starting Firebase to Google Sheets export...")
        
        # Connect to Firebase
        if not self.firebase_db:
            if not self.connect_firebase():
                raise Exception("Could not connect to Firebase")
        
        # Connect to Sheets
        if not self.sheets_exporter:
            if not self.connect_sheets():
                raise Exception("Could not connect to Google Sheets")
        
        # Get all data from Firebase
        posts = self.firebase_db.get_all_posts(limit=10000)
        
        if not posts:
            raise Exception("No data found in Firebase")
        
        # Get analysis results if requested
        analysis_data = None
        if include_analysis:
            analysis_data = self.firebase_db.get_analysis_results()
        
        # Export to Sheets
        url = self.sheets_exporter.export_posts(posts, spreadsheet_name, analysis_data)
        
        print(f"✓ Export complete: {len(posts)} posts exported to {url}")
        
        return url
    
    def full_pipeline(self, spreadsheet_name: str = "Facebook_Scraper_Export",
                      run_analysis: bool = True) -> Dict[str, Any]:
        """
        Run full migration and analysis pipeline:
        PostgreSQL -> Firebase -> ML Analysis -> Google Sheets
        
        Args:
            spreadsheet_name: Name for the Google Spreadsheet
            run_analysis: Whether to run ML analysis
            
        Returns:
            Summary of the pipeline execution
        """
        results = {
            'postgres_to_firebase': None,
            'analysis': None,
            'sheets_url': None,
            'errors': []
        }
        
        try:
            # Step 1: Migrate PostgreSQL to Firebase
            print("\n=== Step 1: Migrating PostgreSQL to Firebase ===")
            counts = self.migrate_postgres_to_firebase()
            results['postgres_to_firebase'] = counts
        except Exception as e:
            results['errors'].append(f"Migration failed: {e}")
            print(f"✗ Migration error: {e}")
        
        # Step 2: Run ML Analysis
        if run_analysis and self.firebase_db:
            try:
                print("\n=== Step 2: Running ML Analysis ===")
                from ml.analyzer import DataAnalyzer
                
                analyzer = DataAnalyzer()
                posts = self.firebase_db.get_all_posts()
                
                if posts:
                    # Run all analyses
                    analysis_results = analyzer.analyze_all(posts)
                    
                    # Save to Firebase
                    for post_id, analysis in analysis_results.items():
                        for analysis_type, result in analysis.items():
                            if analysis_type != 'analyzed_at':
                                self.firebase_db.save_analysis_result(
                                    post_id, analysis_type, result
                                )
                    
                    results['analysis'] = analyzer.get_summary_stats(posts)
                    print(f"✓ Analysis complete for {len(posts)} posts")
            except Exception as e:
                results['errors'].append(f"Analysis failed: {e}")
                print(f"✗ Analysis error: {e}")
        
        # Step 3: Export to Google Sheets
        try:
            print("\n=== Step 3: Exporting to Google Sheets ===")
            url = self.migrate_firebase_to_sheets(spreadsheet_name, include_analysis=True)
            results['sheets_url'] = url
        except Exception as e:
            results['errors'].append(f"Sheets export failed: {e}")
            print(f"✗ Sheets export error: {e}")
        
        print("\n=== Pipeline Complete ===")
        return results
    
    # ==================== JSON Export/Import ====================
    
    def export_to_json(self, output_path: str, source: str = 'postgres') -> bool:
        """
        Export data to JSON file
        
        Args:
            output_path: Path for the output JSON file
            source: Data source ('postgres' or 'firebase')
            
        Returns:
            True if successful
        """
        try:
            if source == 'postgres':
                data = self.get_postgres_data()
            elif source == 'firebase':
                if not self.firebase_db:
                    self.connect_firebase()
                data = self.firebase_db.export_to_dict() if self.firebase_db else {}
            else:
                raise ValueError(f"Unknown source: {source}")
            
            # Add metadata
            export_data = {
                'exported_at': datetime.utcnow().isoformat(),
                'source': source,
                'data': data
            }
            
            # Write to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✓ Data exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return False
    
    def import_from_json(self, input_path: str, target: str = 'firebase') -> Dict[str, int]:
        """
        Import data from JSON file
        
        Args:
            input_path: Path to the JSON file
            target: Target storage ('firebase')
            
        Returns:
            Dictionary with counts of imported items
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
            
            data = export_data.get('data', {})
            
            if target == 'firebase':
                if not self.firebase_db:
                    self.connect_firebase()
                
                if self.firebase_db:
                    return self.firebase_db.import_from_postgres(
                        posts=data.get('posts', []),
                        images=data.get('images', []),
                        comments=data.get('comments', [])
                    )
            
            return {'posts': 0, 'images': 0, 'comments': 0}
            
        except Exception as e:
            print(f"✗ Import failed: {e}")
            return {'posts': 0, 'images': 0, 'comments': 0}
    
    def close(self):
        """Close all connections"""
        if self.pg_session:
            self.pg_session.close()
            print("✓ PostgreSQL session closed")


# CLI interface
def main():
    """Command-line interface for data export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Export Utility')
    parser.add_argument('--action', choices=['migrate', 'export-json', 'export-sheets', 'full'],
                        default='full', help='Action to perform')
    parser.add_argument('--source', choices=['postgres', 'firebase'], default='postgres',
                        help='Data source')
    parser.add_argument('--spreadsheet', default='Facebook_Scraper_Export',
                        help='Google Spreadsheet name')
    parser.add_argument('--output', default='exports/data_export.json',
                        help='Output file path for JSON export')
    parser.add_argument('--no-analysis', action='store_true',
                        help='Skip ML analysis')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    try:
        if args.action == 'migrate':
            exporter.migrate_postgres_to_firebase()
        elif args.action == 'export-json':
            exporter.export_to_json(args.output, args.source)
        elif args.action == 'export-sheets':
            exporter.migrate_firebase_to_sheets(args.spreadsheet)
        elif args.action == 'full':
            exporter.full_pipeline(args.spreadsheet, not args.no_analysis)
    finally:
        exporter.close()


if __name__ == '__main__':
    main()
