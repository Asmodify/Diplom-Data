"""
Firebase Firestore Database Module
Provides cloud-based storage for Facebook scraper data
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import os


class FirebaseDB:
    """Firebase Firestore database handler for Facebook scraper data"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase connection
        
        Args:
            credentials_path: Path to Firebase service account JSON file
                            If None, looks for FIREBASE_CREDENTIALS env var or 
                            'firebase_credentials.json' in project root
        """
        self.db = None
        self._initialize_firebase(credentials_path)
    
    def _initialize_firebase(self, credentials_path: Optional[str] = None):
        """Initialize Firebase Admin SDK"""
        # Check if already initialized
        if firebase_admin._apps:
            self.db = firestore.client()
            return
        
        # Find credentials file
        if credentials_path is None:
            credentials_path = os.getenv('FIREBASE_CREDENTIALS')
        
        if credentials_path is None:
            # Look in common locations
            possible_paths = [
                Path(__file__).parent.parent / 'firebase_credentials.json',
                Path(__file__).parent.parent / 'serviceAccountKey.json',
                Path.home() / '.firebase' / 'credentials.json'
            ]
            for path in possible_paths:
                if path.exists():
                    credentials_path = str(path)
                    break
        
        if credentials_path is None or not Path(credentials_path).exists():
            raise FileNotFoundError(
                "Firebase credentials not found. Please provide credentials_path, "
                "set FIREBASE_CREDENTIALS environment variable, or place "
                "'firebase_credentials.json' in the project root."
            )
        
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        print("✓ Firebase Firestore initialized successfully")
    
    # ==================== POST OPERATIONS ====================
    
    def save_post(self, post_data: Dict[str, Any]) -> str:
        """
        Save a Facebook post to Firestore
        
        Args:
            post_data: Dictionary containing post information
            
        Returns:
            Document ID of the saved post
        """
        # Ensure required fields
        if 'post_id' not in post_data:
            raise ValueError("post_id is required")
        
        # Add metadata
        post_data['scraped_at'] = datetime.utcnow()
        post_data['updated_at'] = datetime.utcnow()
        
        # Use post_id as document ID for easy lookups
        doc_ref = self.db.collection('facebook_posts').document(post_data['post_id'])
        doc_ref.set(post_data, merge=True)
        
        return post_data['post_id']
    
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a single post by ID"""
        doc = self.db.collection('facebook_posts').document(post_id).get()
        if doc.exists:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    def get_posts_by_page(self, page_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all posts from a specific Facebook page"""
        query = (self.db.collection('facebook_posts')
                 .where('page_name', '==', page_name)
                 .order_by('timestamp', direction=firestore.Query.DESCENDING)
                 .limit(limit))
        
        return [{'id': doc.id, **doc.to_dict()} for doc in query.stream()]
    
    def get_all_posts(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all posts with optional limit"""
        query = (self.db.collection('facebook_posts')
                 .order_by('scraped_at', direction=firestore.Query.DESCENDING)
                 .limit(limit))
        
        return [{'id': doc.id, **doc.to_dict()} for doc in query.stream()]
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a post and its related data"""
        try:
            # Delete images subcollection
            images_ref = self.db.collection('facebook_posts').document(post_id).collection('images')
            for img in images_ref.stream():
                img.reference.delete()
            
            # Delete comments subcollection
            comments_ref = self.db.collection('facebook_posts').document(post_id).collection('comments')
            for comment in comments_ref.stream():
                comment.reference.delete()
            
            # Delete the post
            self.db.collection('facebook_posts').document(post_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False
    
    # ==================== IMAGE OPERATIONS ====================
    
    def save_image(self, post_id: str, image_data: Dict[str, Any]) -> str:
        """Save an image as subcollection of a post"""
        image_data['downloaded_at'] = datetime.utcnow()
        
        doc_ref = (self.db.collection('facebook_posts')
                   .document(post_id)
                   .collection('images')
                   .add(image_data))
        
        return doc_ref[1].id
    
    def get_images_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        """Get all images for a specific post"""
        images_ref = (self.db.collection('facebook_posts')
                      .document(post_id)
                      .collection('images'))
        
        return [{'id': doc.id, **doc.to_dict()} for doc in images_ref.stream()]
    
    # ==================== COMMENT OPERATIONS ====================
    
    def save_comment(self, post_id: str, comment_data: Dict[str, Any]) -> str:
        """Save a comment as subcollection of a post"""
        comment_data['scraped_at'] = datetime.utcnow()
        
        # Use comment_id as document ID if available
        if 'comment_id' in comment_data:
            doc_ref = (self.db.collection('facebook_posts')
                       .document(post_id)
                       .collection('comments')
                       .document(comment_data['comment_id']))
            doc_ref.set(comment_data, merge=True)
            return comment_data['comment_id']
        else:
            doc_ref = (self.db.collection('facebook_posts')
                       .document(post_id)
                       .collection('comments')
                       .add(comment_data))
            return doc_ref[1].id
    
    def get_comments_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a specific post"""
        comments_ref = (self.db.collection('facebook_posts')
                        .document(post_id)
                        .collection('comments')
                        .order_by('timestamp', direction=firestore.Query.DESCENDING))
        
        return [{'id': doc.id, **doc.to_dict()} for doc in comments_ref.stream()]
    
    # ==================== ANALYTICS DATA ====================
    
    def save_analysis_result(self, post_id: str, analysis_type: str, 
                              result: Dict[str, Any]) -> str:
        """Save ML analysis results for a post"""
        analysis_data = {
            'post_id': post_id,
            'analysis_type': analysis_type,
            'result': result,
            'analyzed_at': datetime.utcnow()
        }
        
        doc_ref = (self.db.collection('analysis_results')
                   .document(f"{post_id}_{analysis_type}"))
        doc_ref.set(analysis_data, merge=True)
        
        return doc_ref.id
    
    def get_analysis_results(self, post_id: str = None, 
                             analysis_type: str = None) -> List[Dict[str, Any]]:
        """Get analysis results with optional filters"""
        query = self.db.collection('analysis_results')
        
        if post_id:
            query = query.where('post_id', '==', post_id)
        if analysis_type:
            query = query.where('analysis_type', '==', analysis_type)
        
        return [{'id': doc.id, **doc.to_dict()} for doc in query.stream()]
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_save_posts(self, posts: List[Dict[str, Any]]) -> int:
        """Save multiple posts in a batch"""
        batch = self.db.batch()
        count = 0
        
        for post in posts:
            if 'post_id' not in post:
                continue
            
            post['scraped_at'] = datetime.utcnow()
            post['updated_at'] = datetime.utcnow()
            
            doc_ref = self.db.collection('facebook_posts').document(post['post_id'])
            batch.set(doc_ref, post, merge=True)
            count += 1
            
            # Firestore batch limit is 500
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        return count
    
    # ==================== MIGRATION HELPERS ====================
    
    def import_from_postgres(self, posts: List[Dict[str, Any]], 
                              images: List[Dict[str, Any]] = None,
                              comments: List[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Import data from PostgreSQL format to Firestore
        
        Args:
            posts: List of post dictionaries from PostgreSQL
            images: List of image dictionaries (with post_id reference)
            comments: List of comment dictionaries (with post_id reference)
            
        Returns:
            Dictionary with counts of imported items
        """
        counts = {'posts': 0, 'images': 0, 'comments': 0}
        
        # Import posts
        for post in posts:
            # Convert datetime objects to Firestore timestamps
            if 'timestamp' in post and post['timestamp']:
                if hasattr(post['timestamp'], 'isoformat'):
                    post['timestamp'] = post['timestamp']
            
            self.save_post(post)
            counts['posts'] += 1
        
        # Import images
        if images:
            for image in images:
                post_id = str(image.get('post_id', ''))
                if post_id:
                    self.save_image(post_id, image)
                    counts['images'] += 1
        
        # Import comments
        if comments:
            for comment in comments:
                post_id = str(comment.get('post_id', ''))
                if post_id:
                    self.save_comment(post_id, comment)
                    counts['comments'] += 1
        
        return counts
    
    def export_to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all data to a dictionary format"""
        data = {
            'posts': self.get_all_posts(limit=10000),
            'analysis_results': self.get_analysis_results()
        }
        
        # Get images and comments for each post
        for post in data['posts']:
            post['images'] = self.get_images_for_post(post['id'])
            post['comments'] = self.get_comments_for_post(post['id'])
        
        return data


# Convenience function for quick initialization
def get_firebase_db(credentials_path: Optional[str] = None) -> FirebaseDB:
    """Get a FirebaseDB instance"""
    return FirebaseDB(credentials_path)
