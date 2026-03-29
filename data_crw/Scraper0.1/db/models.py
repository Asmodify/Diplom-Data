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

class PostImage(Base):
    __tablename__ = 'post_images'
    id = Column(Integer, primary_key=True)
    post_id = Column(Text, ForeignKey('facebook_posts.post_id'))
    image_url = Column(Text)
    local_path = Column(Text)

class PostComment(Base):
    __tablename__ = 'post_comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Text, ForeignKey('facebook_posts.post_id'))
    comment_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Define relationships
FacebookPost.images = relationship("PostImage", backref="post", cascade="all, delete-orphan")
FacebookPost.comments = relationship("PostComment", backref="post", cascade="all, delete-orphan")
