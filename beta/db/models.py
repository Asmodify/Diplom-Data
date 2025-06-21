from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FacebookPost(Base):
    __tablename__ = 'facebook_posts'

    id = Column(Integer, primary_key=True)
    page_name = Column(Text)
    post_id = Column(Text, unique=True)
    post_url = Column(Text)
    post_text = Column(Text)
    post_time = Column(DateTime)
    author = Column(Text, nullable=True)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    extracted_at = Column(DateTime)
    
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")

class PostImage(Base):
    __tablename__ = 'post_images'

    id = Column(Integer, primary_key=True)
    post_id = Column(Text, ForeignKey('facebook_posts.post_id', ondelete='CASCADE'))
    original_url = Column(Text)
    local_path = Column(Text)
    filename = Column(Text)
    downloaded_at = Column(DateTime)
    
    post = relationship("FacebookPost", back_populates="images")

class PostComment(Base):
    __tablename__ = 'post_comments'

    id = Column(Integer, primary_key=True)
    post_id = Column(Text, ForeignKey('facebook_posts.post_id', ondelete='CASCADE'))
    author = Column(Text)
    text = Column(Text)
    comment_time = Column(DateTime)
    likes = Column(Integer, default=0)
    extracted_at = Column(DateTime)
    
    post = relationship("FacebookPost", back_populates="comments")
