"""
Database Models v2.0
=====================
SQLAlchemy ORM models for storing scraped data.

Supports:
- SQLite (default/fallback)
- PostgreSQL (production)
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, 
    ForeignKey, Boolean, Float, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Page(Base):
    """Facebook page being scraped."""
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(String(100), unique=True, nullable=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True)
    followers = Column(BigInteger, nullable=True)
    
    # Scraping state
    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    scrape_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Page(id={self.id}, name='{self.name}')>"


class Post(Base):
    """Facebook post."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(100), unique=True, nullable=False, index=True)
    page_id = Column(Integer, ForeignKey('pages.id'), nullable=True)
    
    # Content
    content = Column(Text, nullable=True)
    content_type = Column(String(50), default='text')  # text, photo, video, link
    url = Column(String(500), nullable=True)
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    reactions = Column(JSON, nullable=True)  # {"like": 10, "love": 5, ...}
    
    # Media
    image_urls = Column(JSON, nullable=True)  # List of image URLs
    video_url = Column(String(500), nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    
    # Timestamps
    post_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Analysis
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    
    # Relationships
    page = relationship("Page", back_populates="posts")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_post_date', 'post_date'),
        Index('idx_scraped_at', 'scraped_at'),
    )
    
    def __repr__(self):
        return f"<Post(id={self.id}, post_id='{self.post_id}')>"


class PostComment(Base):
    """Comment on a Facebook post."""
    __tablename__ = 'post_comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(100), ForeignKey('posts.post_id'), nullable=False, index=True)
    comment_id = Column(String(100), nullable=True)
    
    # Content
    comment_text = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    author_id = Column(String(100), nullable=True)
    
    # Engagement
    likes = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Timestamps
    comment_date = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)  # When we scraped it
    
    # Analysis
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    
    # Parent comment (for replies)
    parent_comment_id = Column(Integer, ForeignKey('post_comments.id'), nullable=True)
    replies = relationship("PostComment", backref="parent", remote_side=[id])
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    
    __table_args__ = (
        UniqueConstraint('post_id', 'comment_text', name='uq_post_comment'),
        Index('idx_comment_date', 'comment_date'),
    )
    
    def __repr__(self):
        return f"<PostComment(id={self.id}, post_id='{self.post_id}')>"


class ScrapeLog(Base):
    """Log of scraping operations."""
    __tablename__ = 'scrape_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500), nullable=True)
    
    # Operation details
    operation = Column(String(50))  # scrape, login, error
    status = Column(String(20))  # success, failed, partial
    posts_scraped = Column(Integer, default=0)
    comments_scraped = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Error info
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<ScrapeLog(id={self.id}, operation='{self.operation}')>"


class AnalysisResult(Base):
    """ML analysis results."""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference
    post_id = Column(String(100), nullable=True)
    comment_id = Column(Integer, nullable=True)
    
    # Analysis type
    analysis_type = Column(String(50))  # sentiment, topic, entity
    model_name = Column(String(100))
    
    # Results
    score = Column(Float, nullable=True)
    label = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_analysis_post', 'post_id'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, type='{self.analysis_type}')>"
