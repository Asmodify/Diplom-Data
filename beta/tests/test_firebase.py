"""
Test script for Firebase Firestore connection
Run this after setting up your Firebase credentials
"""
import sys
import os
sys.path.insert(0, '.')

# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def test_firebase_connection():
    """Test Firebase connection and basic operations"""
    print("=" * 50)
    print("FIREBASE FIRESTORE CONNECTION TEST")
    print("=" * 50)
    
    # Check for credentials file
    creds_path = os.getenv('FIREBASE_CREDENTIALS')
    print(f"\n1. Checking credentials...")
    print(f"   FIREBASE_CREDENTIALS env var: {creds_path or 'Not set'}")
    
    # Check common locations
    possible_paths = [
        Path(__file__).parent / 'firebase_credentials.json',
        Path(__file__).parent / 'serviceAccountKey.json',
    ]
    for path in possible_paths:
        if path.exists():
            print(f"   ✓ Found credentials at: {path}")
            creds_path = str(path)
            break
    else:
        if not creds_path or not Path(creds_path).exists():
            print("\n   ✗ ERROR: No Firebase credentials found!")
            print("\n   To fix this:")
            print("   1. Go to Firebase Console: https://console.firebase.google.com/")
            print("   2. Select your project (or create one)")
            print("   3. Go to Project Settings > Service Accounts")
            print("   4. Click 'Generate new private key'")
            print("   5. Save the file as 'firebase_credentials.json' in this folder")
            print("   6. Or set FIREBASE_CREDENTIALS in your .env file")
            return False
    
    # Test connection
    print(f"\n2. Connecting to Firebase...")
    try:
        from db.firebase_db import FirebaseDB
        db = FirebaseDB(creds_path)
        print("   ✓ Firebase connection successful!")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False
    
    # Test write operation
    print(f"\n3. Testing write operation...")
    try:
        test_post = {
            'post_id': 'test_post_001',
            'page_name': 'Test Page',
            'content': 'This is a test post to verify Firebase connection',
            'likes': 42,
            'shares': 10,
            'comment_count': 5,
            'test_entry': True
        }
        doc_id = db.save_post(test_post)
        print(f"   ✓ Successfully saved test post with ID: {doc_id}")
    except Exception as e:
        print(f"   ✗ Write failed: {e}")
        return False
    
    # Test read operation
    print(f"\n4. Testing read operation...")
    try:
        retrieved = db.get_post('test_post_001')
        if retrieved:
            print(f"   ✓ Successfully retrieved post:")
            print(f"      - Page: {retrieved.get('page_name')}")
            print(f"      - Content: {retrieved.get('content')[:50]}...")
            print(f"      - Likes: {retrieved.get('likes')}")
        else:
            print("   ⚠ Post not found (but no error)")
    except Exception as e:
        print(f"   ✗ Read failed: {e}")
        return False
    
    # Test query operation
    print(f"\n5. Testing query operation...")
    try:
        posts = db.get_posts_by_page('Test Page', limit=10)
        print(f"   ✓ Query returned {len(posts)} posts from 'Test Page'")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
        return False
    
    # Test analysis storage
    print(f"\n6. Testing analysis storage...")
    try:
        analysis_data = {
            'sentiment': 'positive',
            'polarity': 0.75,
            'topic': 'test'
        }
        db.save_analysis_result('test_post_001', 'sentiment', analysis_data)
        print("   ✓ Successfully saved analysis result")
    except Exception as e:
        print(f"   ✗ Analysis storage failed: {e}")
        return False
    
    # Cleanup test data (optional)
    print(f"\n7. Cleaning up test data...")
    try:
        db.delete_post('test_post_001')
        print("   ✓ Test post deleted")
    except Exception as e:
        print(f"   ⚠ Cleanup failed (not critical): {e}")
    
    print("\n" + "=" * 50)
    print("✓ ALL FIREBASE TESTS PASSED!")
    print("=" * 50)
    print("\nYour Firebase Firestore is ready to use.")
    print("You can now run the API server or migrate existing data.")
    
    return True


if __name__ == '__main__':
    success = test_firebase_connection()
    sys.exit(0 if success else 1)
