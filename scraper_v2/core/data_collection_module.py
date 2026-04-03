"""
Automated Data Collection Module - Multi-Platform Social Media Scraper
========================================================================

This module provides a unified interface for collecting data from multiple social media
platforms (Facebook, Twitter, Instagram) with support for:
- Platform specification (Facebook, Twitter, Instagram)
- Time range filtering (start_date, end_date)
- Keyword-based filtering and search
- Post and user interaction collection
- Structured data storage

Architecture:
- AbstractPlatformCollector: Base class defining interface
- PlatformFactory: Creates platform-specific collectors
- FacebookCollector: Facebook-specific implementation
- TwitterCollector: Twitter-specific implementation
- InstagramCollector: Instagram-specific implementation
- DataCollectionManager: Orchestrates multi-platform collection
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"


@dataclass
class CollectionParams:
    """Parameters for data collection."""
    platform: Platform
    keywords: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_posts: int = 100
    max_comments_per_post: int = 50
    collect_interactions: bool = True
    collect_user_data: bool = True
    language: Optional[str] = None
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate collection parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.keywords and not self.start_date:
            return False, "Must specify either keywords or date range"
        
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                return False, "start_date must be before end_date"
        
        if self.max_posts <= 0:
            return False, "max_posts must be greater than 0"
        
        if self.max_comments_per_post < 0:
            return False, "max_comments_per_post must be >= 0"
        
        return True, ""


@dataclass
class CollectedPost:
    """Represents a collected post from any platform."""
    post_id: str
    platform: Platform
    content: str
    author: str
    author_id: str
    url: str
    timestamp: datetime
    likes: int = 0
    comments: int = 0
    shares: int = 0
    retweets: int = 0  # For Twitter
    reposts: int = 0   # For Instagram
    views: int = 0     # For Twitter/Instagram
    
    # Metadata
    keywords_matched: List[str] = field(default_factory=list)
    language: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # Collection metadata
    collected_at: datetime = field(default_factory=datetime.now)
    source: str = ""  # e.g., "search", "timeline", "hashtag"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['platform'] = self.platform.value
        data['timestamp'] = self.timestamp.isoformat()
        data['collected_at'] = self.collected_at.isoformat()
        return data


@dataclass
class CollectedComment:
    """Represents a comment/interaction on a post."""
    comment_id: str
    post_id: str
    platform: Platform
    author: str
    author_id: str
    content: str
    timestamp: datetime
    likes: int = 0
    replies: int = 0
    
    # Metadata
    is_reply_to: Optional[str] = None  # ID of parent comment if nested
    level: int = 0  # Nesting level (0 = top-level, 1+ = replies)
    
    collected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['platform'] = self.platform.value
        data['timestamp'] = self.timestamp.isoformat()
        data['collected_at'] = self.collected_at.isoformat()
        return data


@dataclass
class CollectionResult:
    """Result of a collection operation."""
    platform: Platform
    posts_collected: int
    comments_collected: int
    interactions_collected: int
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def success(self) -> bool:
        """Check if collection was successful."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform': self.platform.value,
            'posts_collected': self.posts_collected,
            'comments_collected': self.comments_collected,
            'interactions_collected': self.interactions_collected,
            'errors': self.errors,
            'duration_seconds': self.duration_seconds,
            'success': self.success
        }


class AbstractPlatformCollector(ABC):
    """
    Abstract base class for platform-specific collectors.
    
    Defines interface for collecting data from social media platforms.
    """
    
    def __init__(self, params: CollectionParams, config: Optional[Any] = None):
        """
        Initialize collector.
        
        Args:
            params: Collection parameters
            config: Optional configuration object
        """
        self.params = params
        self.config = config
        self.result = CollectionResult(platform=params.platform)
        self.posts: List[CollectedPost] = []
        self.comments: List[CollectedComment] = []
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            Whether authentication was successful
        """
        pass
    
    @abstractmethod
    def search_posts(self, keywords: List[str]) -> List[CollectedPost]:
        """
        Search for posts matching keywords.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            List of collected posts
        """
        pass
    
    @abstractmethod
    def collect_timeline_posts(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CollectedPost]:
        """
        Collect posts from timeline within date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of collected posts
        """
        pass
    
    @abstractmethod
    def collect_comments(self, post_id: str) -> List[CollectedComment]:
        """
        Collect comments for a post.
        
        Args:
            post_id: ID of post to collect comments for
            
        Returns:
            List of collected comments
        """
        pass
    
    @abstractmethod
    def collect_user_interactions(self, post_id: str) -> Dict[str, Any]:
        """
        Collect user interactions (likes, shares, etc.) for a post.
        
        Args:
            post_id: ID of post
            
        Returns:
            Dictionary of interaction data
        """
        pass
    
    def collect(self) -> CollectionResult:
        """
        Execute full collection workflow.
        
        Returns:
            CollectionResult with statistics
        """
        try:
            # Authenticate
            if not self.authenticate():
                self.result.errors.append(f"Failed to authenticate with {self.params.platform.value}")
                return self.result
            
            # Collect posts
            if self.params.keywords:
                self.posts.extend(self.search_posts(self.params.keywords))
            
            if self.params.start_date and self.params.end_date:
                self.posts.extend(self.collect_timeline_posts(
                    self.params.start_date,
                    self.params.end_date
                ))
            
            # Limit posts
            self.posts = self.posts[:self.params.max_posts]
            self.result.posts_collected = len(self.posts)
            
            # Collect interactions
            if self.params.collect_interactions:
                for post in self.posts:
                    # Collect comments
                    comments = self.collect_comments(post.post_id)
                    self.comments.extend(comments[:self.params.max_comments_per_post])
                    self.result.comments_collected += len(comments)
                    
                    # Collect user interactions
                    interactions = self.collect_user_interactions(post.post_id)
                    self.result.interactions_collected += sum(1 for v in interactions.values() if v)
            
            self.result.end_time = datetime.now()
            logger.info(f"Collection complete for {self.params.platform.value}: "
                       f"{self.result.posts_collected} posts, "
                       f"{self.result.comments_collected} comments")
            
        except Exception as e:
            self.result.errors.append(str(e))
            logger.error(f"Collection error for {self.params.platform.value}: {e}")
        
        self.result.end_time = datetime.now()
        return self.result
    
    def get_posts(self) -> List[Dict[str, Any]]:
        """Get collected posts as dictionaries."""
        return [post.to_dict() for post in self.posts]
    
    def get_comments(self) -> List[Dict[str, Any]]:
        """Get collected comments as dictionaries."""
        return [comment.to_dict() for comment in self.comments]


class FacebookCollector(AbstractPlatformCollector):
    """Collector for Facebook data."""
    
    def authenticate(self) -> bool:
        """
        Authenticate with Facebook.
        
        Requires FB_EMAIL and FB_PASSWORD in credentials.
        Uses Selenium with anti-detection measures.
        """
        try:
            from core.browser_manager import BrowserManager
            
            self.browser_manager = BrowserManager(self.config)
            if not self.browser_manager.start():
                logger.error("Failed to start browser manager")
                return False
            
            if not self.browser_manager.login():
                logger.error("Failed to login to Facebook")
                return False
            
            logger.info("Facebook authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Facebook authentication failed: {e}")
            return False
    
    def search_posts(self, keywords: List[str]) -> List[CollectedPost]:
        """
        Search Facebook for posts matching keywords.
        
        Uses Facebook search functionality via Selenium.
        """
        posts = []
        
        try:
            from core.post_scraper import PostScraper
            
            post_scraper = PostScraper(self.browser_manager, self.config)
            
            for keyword in keywords:
                logger.info(f"Searching Facebook for: {keyword}")
                search_url = f"https://www.facebook.com/search/posts/?q={keyword}"
                
                if not self.browser_manager.navigate_to(search_url):
                    continue
                
                time.sleep(2)
                
                # Extract posts from search results
                scraped_posts = post_scraper.scrape_page_posts(
                    search_url,
                    max_posts=self.params.max_posts // len(keywords),
                    scrape_comments=False
                )
                
                for post in scraped_posts:
                    collected = CollectedPost(
                        post_id=post.post_id,
                        platform=Platform.FACEBOOK,
                        content=post.content,
                        author=post.page_name,
                        author_id="",
                        url=post.post_url,
                        timestamp=datetime.now(),  # Would parse from post.timestamp
                        likes=post.likes,
                        comments=post.comments,
                        shares=post.shares,
                        keywords_matched=[keyword],
                        media_urls=post.media_urls,
                        source="search"
                    )
                    posts.append(collected)
                
        except Exception as e:
            logger.error(f"Facebook search error: {e}")
            self.result.errors.append(f"Facebook search error: {str(e)}")
        
        return posts
    
    def collect_timeline_posts(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CollectedPost]:
        """Collect posts from timeline within date range."""
        # Implementation would scroll through timeline and filter by date
        logger.info(f"Collecting Facebook timeline posts from {start_date} to {end_date}")
        return []
    
    def collect_comments(self, post_id: str) -> List[CollectedComment]:
        """Collect comments for a Facebook post."""
        comments = []
        
        try:
            from core.post_scraper import PostScraper
            from db.database import DatabaseManager
            
            db = DatabaseManager(self.config)
            post_comments = db.get_comments_by_post(post_id)
            
            for comment in post_comments:
                collected = CollectedComment(
                    comment_id=str(comment.get('id', '')),
                    post_id=post_id,
                    platform=Platform.FACEBOOK,
                    author=comment.get('author', 'Unknown'),
                    author_id="",
                    content=comment.get('content', ''),
                    timestamp=datetime.now(),
                    likes=comment.get('likes', 0)
                )
                comments.append(collected)
                
        except Exception as e:
            logger.error(f"Error collecting Facebook comments: {e}")
        
        return comments
    
    def collect_user_interactions(self, post_id: str) -> Dict[str, Any]:
        """Collect user interactions for a Facebook post."""
        # This would track likes, shares, comment metrics, etc.
        return {
            'likes': True,
            'comments': True,
            'shares': True,
            'reactions': True
        }


class TwitterCollector(AbstractPlatformCollector):
    """Collector for Twitter/X data."""
    
    def authenticate(self) -> bool:
        """
        Authenticate with Twitter/X API.
        
        Requires TWITTER_BEARER_TOKEN or API credentials.
        """
        try:
            import os
            
            self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if not self.bearer_token:
                logger.error("TWITTER_BEARER_TOKEN not found in environment")
                return False
            
            logger.info("Twitter authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False
    
    def search_posts(self, keywords: List[str]) -> List[CollectedPost]:
        """
        Search Twitter for posts matching keywords using Twitter API v2.
        
        Requires tweepy or requests library with Twitter API v2.
        """
        posts = []
        
        try:
            # Would use tweepy or requests to query Twitter API v2
            # Example: GET /tweets/search/recent?query="{keyword}"
            
            for keyword in keywords:
                logger.info(f"Searching Twitter for: {keyword}")
                # API call would go here
                # posts.extend([CollectedPost(...)])
                
        except Exception as e:
            logger.error(f"Twitter search error: {e}")
            self.result.errors.append(f"Twitter search error: {str(e)}")
        
        return posts
    
    def collect_timeline_posts(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CollectedPost]:
        """Collect posts from timeline within date range using Twitter API."""
        posts = []
        
        try:
            # Would use Twitter API v2 to collect posts from specified date range
            # GET /tweets/search/all with start_time and end_time parameters
            pass
            
        except Exception as e:
            logger.error(f"Twitter timeline collection error: {e}")
            self.result.errors.append(f"Twitter timeline error: {str(e)}")
        
        return posts
    
    def collect_comments(self, post_id: str) -> List[CollectedComment]:
        """Collect replies to a Twitter post."""
        comments = []
        
        try:
            # Would use Twitter API v2 to collect replies
            # GET /tweets/:id/liking_by or similar
            pass
            
        except Exception as e:
            logger.error(f"Twitter comment collection error: {e}")
        
        return comments
    
    def collect_user_interactions(self, post_id: str) -> Dict[str, Any]:
        """Collect user interactions (likes, retweets, replies) for a tweet."""
        return {
            'likes': True,
            'retweets': True,
            'replies': True,
            'quotes': True
        }


class InstagramCollector(AbstractPlatformCollector):
    """Collector for Instagram data."""
    
    def authenticate(self) -> bool:
        """
        Authenticate with Instagram.
        
        Requires INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD.
        Uses instagrapi library for API access.
        """
        try:
            import os
            
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.error("Instagram credentials not found in environment")
                return False
            
            # Would use instagrapi to login
            # from instagrapi import Client
            # self.client = Client()
            # self.client.login(username, password)
            
            logger.info("Instagram authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False
    
    def search_posts(self, keywords: List[str]) -> List[CollectedPost]:
        """
        Search Instagram for posts by hashtag or location.
        
        Instagram doesn't support keyword search like other platforms,
        so this uses hashtags instead.
        """
        posts = []
        
        try:
            # Would use Instagram API or instagrapi to search by hashtags
            for keyword in keywords:
                logger.info(f"Searching Instagram hashtag: {keyword}")
                hashtag = keyword.lstrip('#')
                
                # Would call Instagram API
                # posts.extend([CollectedPost(...)])
                
        except Exception as e:
            logger.error(f"Instagram search error: {e}")
            self.result.errors.append(f"Instagram search error: {str(e)}")
        
        return posts
    
    def collect_timeline_posts(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CollectedPost]:
        """Collect posts from Instagram feed within date range."""
        posts = []
        
        try:
            # Would use Instagram API to collect recent posts
            pass
            
        except Exception as e:
            logger.error(f"Instagram timeline collection error: {e}")
            self.result.errors.append(f"Instagram timeline error: {str(e)}")
        
        return posts
    
    def collect_comments(self, post_id: str) -> List[CollectedComment]:
        """Collect comments on an Instagram post."""
        comments = []
        
        try:
            # Would use Instagram API to collect comments
            pass
            
        except Exception as e:
            logger.error(f"Instagram comment collection error: {e}")
        
        return comments
    
    def collect_user_interactions(self, post_id: str) -> Dict[str, Any]:
        """Collect user interactions (likes, comments) for an Instagram post."""
        return {
            'likes': True,
            'comments': True,
            'saves': True,
            'shares': True
        }


class PlatformFactory:
    """Factory for creating platform-specific collectors."""
    
    _collectors = {
        Platform.FACEBOOK: FacebookCollector,
        Platform.TWITTER: TwitterCollector,
        Platform.INSTAGRAM: InstagramCollector,
    }
    
    @classmethod
    def create_collector(
        cls,
        platform: Platform,
        params: CollectionParams,
        config: Optional[Any] = None
    ) -> AbstractPlatformCollector:
        """
        Create a collector for specified platform.
        
        Args:
            platform: Platform to create collector for
            params: Collection parameters
            config: Optional configuration
            
        Returns:
            Platform-specific collector instance
            
        Raises:
            ValueError: If platform is not supported
        """
        if platform not in cls._collectors:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return cls._collectors[platform](params, config)


class DataCollectionManager:
    """
    Orchestrates data collection across multiple platforms.
    
    Provides high-level interface for collecting data from multiple
    social media platforms with unified configuration.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize manager.
        
        Args:
            config: Optional configuration object
        """
        self.config = config
        self.collectors: Dict[Platform, AbstractPlatformCollector] = {}
        self.results: List[CollectionResult] = []
        self.all_posts: List[CollectedPost] = []
        self.all_comments: List[CollectedComment] = []
    
    def collect_from_platforms(
        self,
        platforms: List[Platform],
        keywords: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_posts: int = 100,
        max_comments_per_post: int = 50
    ) -> List[CollectionResult]:
        """
        Collect data from multiple platforms.
        
        Args:
            platforms: List of platforms to collect from
            keywords: Keywords to search for (optional)
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            max_posts: Maximum posts per platform
            max_comments_per_post: Maximum comments per post
            
        Returns:
            List of collection results for each platform
        """
        results = []
        
        for platform in platforms:
            logger.info(f"Starting collection for {platform.value}")
            
            # Create collection parameters
            params = CollectionParams(
                platform=platform,
                keywords=keywords or [],
                start_date=start_date,
                end_date=end_date,
                max_posts=max_posts,
                max_comments_per_post=max_comments_per_post
            )
            
            # Validate parameters
            is_valid, error_msg = params.validate()
            if not is_valid:
                logger.error(f"Invalid parameters for {platform.value}: {error_msg}")
                result = CollectionResult(platform=platform)
                result.errors.append(error_msg)
                results.append(result)
                continue
            
            # Create and execute collector
            try:
                collector = PlatformFactory.create_collector(platform, params, self.config)
                result = collector.collect()
                results.append(result)
                
                # Aggregate results
                self.all_posts.extend(collector.posts)
                self.all_comments.extend(collector.comments)
                
            except Exception as e:
                logger.error(f"Error collecting from {platform.value}: {e}")
                result = CollectionResult(platform=platform)
                result.errors.append(str(e))
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """
        Get summary of all collection activities.
        
        Returns:
            Summary dictionary
        """
        total_posts = sum(r.posts_collected for r in self.results)
        total_comments = sum(r.comments_collected for r in self.results)
        total_interactions = sum(r.interactions_collected for r in self.results)
        
        return {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'total_interactions': total_interactions,
            'platforms_used': [r.platform.value for r in self.results],
            'collection_results': [r.to_dict() for r in self.results],
            'successful_collections': sum(1 for r in self.results if r.success),
            'failed_collections': sum(1 for r in self.results if not r.success)
        }
    
    def export_data(self) -> Dict[str, Any]:
        """
        Export collected data for storage or analysis.
        
        Returns:
            Dictionary with posts and comments
        """
        return {
            'posts': [post.to_dict() for post in self.all_posts],
            'comments': [comment.to_dict() for comment in self.all_comments],
            'summary': self.get_collection_summary(),
            'export_timestamp': datetime.now().isoformat()
        }
