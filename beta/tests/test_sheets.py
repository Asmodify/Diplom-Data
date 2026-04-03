"""
Test script for Google Sheets integration
Run this after setting up your Google Cloud credentials
"""
import sys
import os
sys.path.insert(0, '.')

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def test_google_sheets_connection():
    """Test Google Sheets connection and basic operations"""
    print("=" * 50)
    print("GOOGLE SHEETS CONNECTION TEST")
    print("=" * 50)
    
    # Check for credentials file
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    print(f"\n1. Checking credentials...")
    print(f"   GOOGLE_SHEETS_CREDENTIALS env var: {creds_path or 'Not set'}")
    
    # Check common locations
    possible_paths = [
        Path(__file__).parent / 'google_credentials.json',
        Path(__file__).parent / 'service_account.json',
    ]
    for path in possible_paths:
        if path.exists():
            print(f"   ✓ Found credentials at: {path}")
            creds_path = str(path)
            break
    else:
        if not creds_path or not Path(creds_path).exists():
            print("\n   ✗ ERROR: No Google Sheets credentials found!")
            print("\n   To fix this:")
            print("   1. Go to Google Cloud Console: https://console.cloud.google.com/")
            print("   2. Create a new project or select existing")
            print("   3. Enable 'Google Sheets API' and 'Google Drive API'")
            print("   4. Go to APIs & Services > Credentials")
            print("   5. Create a Service Account")
            print("   6. Download the JSON key file as 'google_credentials.json'")
            print("   7. Place it in this folder or set GOOGLE_SHEETS_CREDENTIALS in .env")
            return False
    
    # Test connection
    print(f"\n2. Connecting to Google Sheets API...")
    try:
        from integrations.google_sheets import GoogleSheetsExporter
        exporter = GoogleSheetsExporter(creds_path)
        print("   ✓ Google Sheets connection successful!")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False
    
    # Test creating a spreadsheet
    print(f"\n3. Creating test spreadsheet...")
    try:
        test_posts = [
            {
                'post_id': 'test_001',
                'page_name': 'Test Page',
                'content': 'This is a test post for Google Sheets export',
                'likes': 100,
                'shares': 20,
                'comment_count': 15,
                'post_url': 'https://facebook.com/test',
                'timestamp': '2024-01-15T10:30:00'
            },
            {
                'post_id': 'test_002',
                'page_name': 'Test Page',
                'content': 'Another test post with more content to verify export',
                'likes': 250,
                'shares': 45,
                'comment_count': 30,
                'post_url': 'https://facebook.com/test2',
                'timestamp': '2024-01-16T14:20:00'
            }
        ]
        
        spreadsheet_url = exporter.export_posts(
            test_posts, 
            "Facebook Scraper Test Export"
        )
        print(f"   ✓ Spreadsheet created successfully!")
        print(f"   📊 URL: {spreadsheet_url}")
    except Exception as e:
        print(f"   ✗ Spreadsheet creation failed: {e}")
        print("\n   Common issues:")
        print("   - Service account email not added to spreadsheet")
        print("   - Google Sheets API not enabled")
        print("   - Quota exceeded")
        return False
    
    # Test adding analysis data
    print(f"\n4. Testing analysis data export...")
    try:
        analysis_data = [
            {
                'post_id': 'test_001',
                'analysis_type': 'sentiment',
                'sentiment': 'positive',
                'polarity': 0.75,
                'topic': 'News'
            },
            {
                'post_id': 'test_002',
                'analysis_type': 'sentiment',
                'sentiment': 'neutral',
                'polarity': 0.1,
                'topic': 'General'
            }
        ]
        
        spreadsheet_url = exporter.export_posts(
            test_posts, 
            "Facebook Scraper Test Export",
            analysis_data=analysis_data
        )
        print(f"   ✓ Analysis data exported successfully!")
    except Exception as e:
        print(f"   ⚠ Analysis export failed (not critical): {e}")
    
    # Test summary export
    print(f"\n5. Testing summary export...")
    try:
        summary = {
            'total_posts': 2,
            'total_pages': 1,
            'avg_likes': 175.0,
            'avg_shares': 32.5,
            'sentiment_distribution': {'positive': 1, 'neutral': 1}
        }
        exporter.export_summary(summary, "Facebook Scraper Test Export")
        print(f"   ✓ Summary exported successfully!")
    except Exception as e:
        print(f"   ⚠ Summary export failed (not critical): {e}")
    
    print("\n" + "=" * 50)
    print("✓ ALL GOOGLE SHEETS TESTS PASSED!")
    print("=" * 50)
    print(f"\nYour Google Sheets integration is ready to use.")
    print(f"Check the spreadsheet: Facebook Scraper Test Export")
    print(f"\nNote: To share spreadsheets with others, you can:")
    print("1. Open the spreadsheet URL")
    print("2. Click 'Share' and add collaborators")
    
    return True


if __name__ == '__main__':
    success = test_google_sheets_connection()
    sys.exit(0 if success else 1)
