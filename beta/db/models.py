from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FacebookPost(Base):
    __tablename__ = 'facebook_posts'

    id = Column(Integer, primary_key=True)
    page_name = Column(Text, nullable=False)
    post_id = Column(Text, unique=True, nullable=False)
    post_url = Column(Text)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_facebook_posts_page_name', 'page_name'),
        Index('idx_facebook_posts_timestamp', 'timestamp'),
        Index('idx_facebook_posts_scraped_at', 'scraped_at')
    )

class PostImage(Base):
    __tablename__ = 'post_images'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('facebook_posts.id', ondelete='CASCADE'), nullable=False)
    image_url = Column(Text, nullable=False)
    local_path = Column(Text)  # Path where image is stored locally
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to post
    post = relationship("FacebookPost", back_populates="images")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_images_post_id', 'post_id'),
    )

class PostComment(Base):
    __tablename__ = 'post_comments'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('facebook_posts.id', ondelete='CASCADE'), nullable=False)
    comment_id = Column(Text, unique=True)
    author_name = Column(Text)
    author_url = Column(Text)
    content = Column(Text)
    timestamp = Column(DateTime)
    likes = Column(Integer, default=0)
    reply_to_id = Column(Integer, ForeignKey('post_comments.id', ondelete='SET NULL'))
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("FacebookPost", back_populates="comments")
    replies = relationship("PostComment", backref='parent', remote_side=[id], cascade="all, delete-orphan", single_parent=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_post_comments_post_id', 'post_id'),
        Index('idx_post_comments_timestamp', 'timestamp'),
        Index('idx_post_comments_reply_to_id', 'reply_to_id'),
    )
