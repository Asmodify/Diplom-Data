"""
Database Models v2.0 - SQLAlchemy models for post storage.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Boolean, Table, JSON, create_engine
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.mutable import MutableList

Base = declarative_base()


class PageModel(Base):
    """Represents a Facebook page."""
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("PostModel", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Page(name='{self.name}', url='{self.url}')>"


class PostModel(Base):
    """Represents a Facebook post."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(100), unique=True, index=True, nullable=False)
    page_id = Column(Integer, ForeignKey('pages.id'), nullable=True)
    page_name = Column(String(255))
    
    content = Column(Text)
    post_url = Column(String(500))
    timestamp = Column(String(100))
    
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    media_urls = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # renamed from metadata (reserved)
    
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("PageModel", back_populates="posts")
    comments = relationship("CommentModel", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(id='{self.post_id}', page='{self.page_name}')>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'page_name': self.page_name,
            'content': self.content,
            'post_url': self.post_url,
            'timestamp': self.timestamp,
            'likes': self.likes,
            'comments': self.comments_count,
            'shares': self.shares,
            'media_urls': self.media_urls or [],
            'extra_data': self.extra_data or {},
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }


class CommentModel(Base):
    """Represents a comment on a post."""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(100), index=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    
    author = Column(String(255))
    content = Column(Text)
    timestamp = Column(String(100))
    likes = Column(Integer, default=0)
    
    parent_comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("PostModel", back_populates="comments")
    replies = relationship("CommentModel", 
                          backref="parent",
                          remote_side=[id],
                          cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Comment(author='{self.author}', post_id={self.post_id})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'author': self.author,
            'content': self.content,
            'timestamp': self.timestamp,
            'likes': self.likes,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }


class ScrapeLogModel(Base):
    """Logs scraping sessions for tracking."""
    __tablename__ = 'scrape_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    posts_scraped = Column(Integer, default=0)
    comments_scraped = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    status = Column(String(50), default='running')  # running, completed, failed
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<ScrapeLog(page='{self.page_url}', status='{self.status}')>"


# Convenience function to create all tables
def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
