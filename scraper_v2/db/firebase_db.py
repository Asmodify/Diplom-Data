"""
Firebase Database Manager
==========================
Optional Firebase/Firestore integration for cloud sync.

Provides:
- Cloud backup of scraped data
- Real-time sync
- Cross-device access
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseManager:
    """
    Firebase/Firestore database manager.
    
    Provides cloud sync functionality for scraped data.
    """
    
    def __init__(self, config=None):
        """
        Initialize Firebase connection.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.db = None
        self.app = None
        
        self._initialize()
        
    def _initialize(self):
        """Initialize Firebase SDK."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            cred_path = self.config.database.firebase_credentials_path
            if not cred_path:
                logger.warning("Firebase credentials path not configured")
                return
                
            cred = credentials.Certificate(cred_path)
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': self.config.database.firebase_project_id
            })
            self.db = firestore.client()
            logger.info("Firebase initialized successfully")
            
        except ImportError:
            logger.warning("firebase-admin package not installed")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            
    @property
    def is_connected(self) -> bool:
        """Check if Firebase is connected."""
        return self.db is not None
        
    def sync_post(self, post_data: Dict[str, Any]) -> bool:
        """
        Sync a post to Firebase.
        
        Args:
            post_data: Post data dictionary
            
        Returns:
            bool: Whether sync was successful
        """
        if not self.is_connected:
            return False
            
        try:
            post_id = post_data.get('post_id')
            if not post_id:
                return False
                
            # Prepare data for Firestore
            doc_data = {
                **post_data,
                'synced_at': datetime.utcnow().isoformat(),
            }
            
            # Remove non-serializable fields
            for key in ['id', '_sa_instance_state']:
                doc_data.pop(key, None)
                
            self.db.collection('posts').document(post_id).set(doc_data, merge=True)
            logger.debug(f"Synced post to Firebase: {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync post to Firebase: {e}")
            return False
            
    def sync_comments(self, comments: List[Dict], post_id: str) -> int:
        """
        Sync comments to Firebase.
        
        Args:
            comments: List of comment dictionaries
            post_id: Parent post ID
            
        Returns:
            Number of comments synced
        """
        if not self.is_connected:
            return 0
            
        synced = 0
        try:
            batch = self.db.batch()
            collection = self.db.collection('posts').document(post_id).collection('comments')
            
            for comment in comments:
                text = comment.get('text', '')
                if not text:
                    continue
                    
                # Create document ID from text hash
                doc_id = str(hash(text) & 0xFFFFFFFF)
                ref = collection.document(doc_id)
                
                doc_data = {
                    **comment,
                    'post_id': post_id,
                    'synced_at': datetime.utcnow().isoformat(),
                }
                
                batch.set(ref, doc_data, merge=True)
                synced += 1
                
            batch.commit()
            logger.debug(f"Synced {synced} comments to Firebase for post {post_id}")
            
        except Exception as e:
            logger.error(f"Failed to sync comments to Firebase: {e}")
            
        return synced
        
    def get_posts(self, limit: int = 100) -> List[Dict]:
        """
        Get posts from Firebase.
        
        Args:
            limit: Maximum number of posts
            
        Returns:
            List of post dictionaries
        """
        if not self.is_connected:
            return []
            
        try:
            docs = self.db.collection('posts').limit(limit).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get posts from Firebase: {e}")
            return []
            
    def get_comments(self, post_id: str) -> List[Dict]:
        """
        Get comments for a post from Firebase.
        
        Args:
            post_id: Post ID
            
        Returns:
            List of comment dictionaries
        """
        if not self.is_connected:
            return []
            
        try:
            docs = (self.db.collection('posts')
                    .document(post_id)
                    .collection('comments')
                    .stream())
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get comments from Firebase: {e}")
            return []
            
    def close(self):
        """Close Firebase connection."""
        try:
            if self.app:
                import firebase_admin
                firebase_admin.delete_app(self.app)
                logger.info("Firebase connection closed")
        except Exception as e:
            logger.error(f"Error closing Firebase: {e}")
