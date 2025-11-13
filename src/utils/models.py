"""
SQLAlchemy database models for storing scraped Twitter data.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    BigInteger, ForeignKey, Index, Float, JSON
)
from sqlalchemy.orm import relationship

from .database import Base


class TwitterUser(Base):
    """Model for Twitter user profiles."""

    __tablename__ = "twitter_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    bio = Column(Text)
    location = Column(String(255))
    website = Column(String(512))

    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    tweets_count = Column(Integer, default=0)

    profile_image_url = Column(String(512))
    banner_image_url = Column(String(512))

    is_verified = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)

    joined_date = Column(DateTime, nullable=True)

    # Tracking configuration
    is_tracked = Column(Boolean, default=False)
    check_interval = Column(Integer, default=900)  # seconds
    last_scraped = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tweets = relationship("Tweet", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TwitterUser(username='{self.username}', followers={self.followers_count})>"


class Tweet(Base):
    """Model for individual tweets."""

    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String(255), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("twitter_users.id"), nullable=False)

    text = Column(Text, nullable=False)
    html_text = Column(Text)
    tweet_url = Column(String(512))  # Direct link to tweet

    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    quotes_count = Column(Integer, default=0)

    # Engagement metrics
    engagement_rate = Column(Float, default=0.0)

    # Tweet metadata
    posted_at = Column(DateTime, nullable=False, index=True)
    language = Column(String(10))
    source = Column(String(255))  # Tweet source (e.g., "Twitter for iPhone")

    # Tweet type
    is_retweet = Column(Boolean, default=False)
    is_reply = Column(Boolean, default=False)
    is_quote = Column(Boolean, default=False)

    # Parent tweet info (for replies/quotes)
    reply_to_tweet_id = Column(String(255), nullable=True)
    reply_to_username = Column(String(255), nullable=True)

    # Media
    has_media = Column(Boolean, default=False)
    media_urls = Column(JSON)  # List of media URLs

    # Extracted data
    hashtags = Column(JSON)  # List of hashtags
    mentions = Column(JSON)  # List of mentions
    urls = Column(JSON)  # List of URLs

    # Sentiment analysis
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)

    # Community (if tweet is from a community)
    community_id = Column(String(255), nullable=True, index=True)

    # Scraping metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    nitter_instance = Column(String(255))  # Which instance was used

    # Relationships
    user = relationship("TwitterUser", back_populates="tweets")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_posted', 'user_id', 'posted_at'),
        Index('idx_posted_engagement', 'posted_at', 'engagement_rate'),
    )

    def __repr__(self):
        return f"<Tweet(tweet_id='{self.tweet_id}', user_id={self.user_id})>"


class SearchQuery(Base):
    """Model for storing search queries and their results."""

    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, index=True)
    query_type = Column(String(50), default="keyword")  # keyword, hashtag, user

    # Tracking
    is_active = Column(Boolean, default=True)
    check_interval = Column(Integer, default=3600)  # seconds
    last_executed = Column(DateTime, nullable=True)

    # Stats
    total_results = Column(Integer, default=0)
    last_result_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SearchQuery(query='{self.query}', type='{self.query_type}')>"


class ScrapingJob(Base):
    """Model for tracking scraping jobs and their status."""

    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)

    job_type = Column(String(50), nullable=False)  # profile, timeline, search, thread
    target = Column(String(500), nullable=False)  # username, url, query

    status = Column(String(50), default="pending")  # pending, running, completed, failed

    # Results
    items_scraped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # seconds

    # Instance used
    nitter_instance = Column(String(255))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ScrapingJob(job_id='{self.job_id}', type='{self.job_type}', status='{self.status}')>"


class Webhook(Base):
    """Model for webhook configurations."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(512), nullable=False)

    # Trigger configuration
    event_type = Column(String(50), nullable=False)  # new_tweet, user_update, etc.
    username = Column(String(255), nullable=True, index=True)  # Specific user to track

    # Authentication
    secret_key = Column(String(255), nullable=True)
    headers = Column(JSON, nullable=True)  # Custom headers

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Webhook(url='{self.url}', event='{self.event_type}')>"


class TwitterCommunity(Base):
    """Model for Twitter communities."""

    __tablename__ = "twitter_communities"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(String(255), unique=True, nullable=False, index=True)

    name = Column(String(500), nullable=False)
    description = Column(Text)

    # Stats
    member_count = Column(Integer, default=0)
    admin_count = Column(Integer, default=0)
    moderator_count = Column(Integer, default=0)

    # Community metadata
    created_at_twitter = Column(DateTime, nullable=True)
    rules = Column(JSON)  # List of community rules
    url = Column(String(512))

    # Tracking configuration
    is_tracked = Column(Boolean, default=False)
    check_interval = Column(Integer, default=3600)  # seconds (default: 1 hour)
    last_scraped = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TwitterCommunity(community_id='{self.community_id}', name='{self.name}')>"
