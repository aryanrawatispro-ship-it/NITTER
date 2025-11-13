"""
Tweet querying API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.utils.database import get_db
from src.utils.models import Tweet, TwitterUser

router = APIRouter()


class TweetResponse(BaseModel):
    id: int
    tweet_id: str
    username: str
    text: str
    likes_count: int
    retweets_count: int
    replies_count: int
    quotes_count: int
    engagement_rate: float
    sentiment: Optional[str]
    posted_at: Optional[datetime]
    scraped_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TweetResponse])
async def get_tweets(
    username: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_likes: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get tweets with optional filters.

    Filters:
    - username: Filter by specific user
    - sentiment: Filter by sentiment (positive, negative, neutral)
    - min_likes: Minimum number of likes
    """
    query = db.query(Tweet).join(TwitterUser)

    if username:
        query = query.filter(TwitterUser.username == username)

    if sentiment:
        query = query.filter(Tweet.sentiment == sentiment)

    if min_likes is not None:
        query = query.filter(Tweet.likes_count >= min_likes)

    tweets = query.order_by(desc(Tweet.posted_at)).offset(skip).limit(limit).all()

    # Add username to response
    for tweet in tweets:
        tweet.username = tweet.user.username

    return tweets


@router.get("/{tweet_id}", response_model=TweetResponse)
async def get_tweet(tweet_id: str, db: Session = Depends(get_db)):
    """Get a specific tweet by ID."""
    tweet = db.query(Tweet).filter_by(tweet_id=tweet_id).first()

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    tweet.username = tweet.user.username
    return tweet


@router.get("/user/{username}", response_model=List[TweetResponse])
async def get_user_tweets(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all tweets from a specific user."""
    user = db.query(TwitterUser).filter_by(username=username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tweets = db.query(Tweet).filter_by(user_id=user.id).order_by(desc(Tweet.posted_at)).offset(skip).limit(limit).all()

    for tweet in tweets:
        tweet.username = username

    return tweets


@router.get("/user/{username}/top")
async def get_top_tweets(
    username: str,
    metric: str = Query("likes_count", regex="^(likes_count|retweets_count|engagement_rate)$"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top performing tweets for a user."""
    user = db.query(TwitterUser).filter_by(username=username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    order_column = getattr(Tweet, metric)
    tweets = db.query(Tweet).filter_by(user_id=user.id).order_by(desc(order_column)).limit(limit).all()

    result = []
    for tweet in tweets:
        result.append({
            "tweet_id": tweet.tweet_id,
            "text": tweet.text,
            "likes": tweet.likes_count,
            "retweets": tweet.retweets_count,
            "engagement_rate": tweet.engagement_rate,
            "posted_at": tweet.posted_at
        })

    return result


@router.get("/sentiment/{sentiment_type}")
async def get_tweets_by_sentiment(
    sentiment_type: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get tweets filtered by sentiment."""
    if sentiment_type not in ['positive', 'negative', 'neutral']:
        raise HTTPException(status_code=400, detail="Invalid sentiment type")

    tweets = db.query(Tweet).filter_by(sentiment=sentiment_type).order_by(desc(Tweet.posted_at)).limit(limit).all()

    result = []
    for tweet in tweets:
        result.append({
            "tweet_id": tweet.tweet_id,
            "username": tweet.user.username,
            "text": tweet.text,
            "sentiment_score": tweet.sentiment_score,
            "posted_at": tweet.posted_at
        })

    return result


@router.get("/hashtag/{hashtag}")
async def get_tweets_by_hashtag(
    hashtag: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get tweets containing a specific hashtag."""
    hashtag = hashtag.lstrip('#')

    # Search for hashtag in the JSON array
    tweets = db.query(Tweet).filter(
        Tweet.hashtags.contains([hashtag])
    ).order_by(desc(Tweet.posted_at)).limit(limit).all()

    result = []
    for tweet in tweets:
        result.append({
            "tweet_id": tweet.tweet_id,
            "username": tweet.user.username,
            "text": tweet.text,
            "likes": tweet.likes_count,
            "retweets": tweet.retweets_count,
            "posted_at": tweet.posted_at
        })

    return result
