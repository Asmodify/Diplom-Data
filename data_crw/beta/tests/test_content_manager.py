#!/usr/bin/env python
"""
Unit tests for content manager and database models
"""
import unittest
import tempfile
from pathlib import Path
from datetime import datetime
import shutil
import json

from content_manager.content_manager import ContentSaver
from db.models import FacebookPost, PostImage, PostComment
from db.database import DatabaseManager

class TestContentManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.content_saver = ContentSaver(self.test_dir)
        
        # Test data
        self.test_post = {
            'post_id': 'test123',
            'post_url': 'https://facebook.com/test123',
            'content': 'Test post content',
            'timestamp': datetime.now(),
            'likes': 10,
            'shares': 5,
            'images': ['https://example.com/test.jpg'],
            'comments': [{
                'comment_id': 'comment123',
                'author': 'Test User',
                'author_url': 'https://facebook.com/testuser',
                'content': 'Test comment',
                'timestamp': datetime.now(),
                'likes': 2,
                'replies': [{
                    'comment_id': 'reply123',
                    'author': 'Reply User',
                    'content': 'Test reply',
                    'timestamp': datetime.now(),
                    'likes': 1
                }]
            }]
        }
        
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_directory_creation(self):
        """Test that required directories are created"""
        self.assertTrue(Path(self.test_dir, 'images').exists())
        self.assertTrue(Path(self.test_dir, 'screenshots').exists())
        self.assertTrue(Path(self.test_dir, 'exports').exists())
        
    def test_save_post(self):
        """Test saving a post with comments and images"""
        # Save post
        result = self.content_saver.save_post(self.test_post, 'testpage')
        self.assertTrue(result)
        
        # Verify in database
        db = DatabaseManager()
        post = db.query(FacebookPost).filter_by(post_id='test123').first()
        
        self.assertIsNotNone(post)
        self.assertEqual(post.page_name, 'testpage')
        self.assertEqual(post.content, 'Test post content')
        self.assertEqual(post.likes, 10)
        self.assertEqual(post.shares, 5)
        
        # Check comments
        self.assertEqual(len(post.comments), 1)
        comment = post.comments[0]
        self.assertEqual(comment.comment_id, 'comment123')
        self.assertEqual(comment.content, 'Test comment')
        
        # Check comment replies
        self.assertEqual(len(comment.replies), 1)
        reply = comment.replies[0]
        self.assertEqual(reply.comment_id, 'reply123')
        self.assertEqual(reply.content, 'Test reply')
        
    def test_export_posts(self):
        """Test exporting posts to JSON"""
        # First save a post
        self.content_saver.save_post(self.test_post, 'testpage')
        
        # Export posts
        export_file = self.content_saver.export_posts('testpage')
        self.assertIsNotNone(export_file)
        
        # Verify export file
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
            
        self.assertEqual(len(exported_data), 1)
        exported_post = exported_data[0]
        self.assertEqual(exported_post['post_id'], 'test123')
        self.assertEqual(exported_post['content'], 'Test post content')
        self.assertEqual(len(exported_post['comments']), 1)

if __name__ == '__main__':
    unittest.main()
