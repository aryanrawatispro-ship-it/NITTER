"""
Dashboard data API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from src.utils.database import get_db
from src.utils.models import Tweet, TwitterUser, ScrapingJob
from src.nitter_manager import NitterInstanceManager
from src.utils.config import settings

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall dashboard statistics."""

    # User stats
    total_users = db.query(func.count(TwitterUser.id)).scalar()
    tracked_users = db.query(func.count(TwitterUser.id)).filter_by(is_tracked=True).scalar()

    # Tweet stats
    total_tweets = db.query(func.count(Tweet.id)).scalar()
    tweets_today = db.query(func.count(Tweet.id)).filter(
        Tweet.scraped_at >= datetime.utcnow() - timedelta(days=1)
    ).scalar()

    # Job stats
    total_jobs = db.query(func.count(ScrapingJob.id)).scalar()
    completed_jobs = db.query(func.count(ScrapingJob.id)).filter_by(status='completed').scalar()
    failed_jobs = db.query(func.count(ScrapingJob.id)).filter_by(status='failed').scalar()
    running_jobs = db.query(func.count(ScrapingJob.id)).filter_by(status='running').scalar()

    # Sentiment distribution
    positive_tweets = db.query(func.count(Tweet.id)).filter_by(sentiment='positive').scalar()
    negative_tweets = db.query(func.count(Tweet.id)).filter_by(sentiment='negative').scalar()
    neutral_tweets = db.query(func.count(Tweet.id)).filter_by(sentiment='neutral').scalar()

    return {
        "users": {
            "total": total_users,
            "tracked": tracked_users
        },
        "tweets": {
            "total": total_tweets,
            "today": tweets_today
        },
        "jobs": {
            "total": total_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "running": running_jobs,
            "success_rate": round((completed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0
        },
        "sentiment": {
            "positive": positive_tweets,
            "negative": negative_tweets,
            "neutral": neutral_tweets
        }
    }


@router.get("/trending/users")
async def get_trending_users(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get users with highest average engagement."""

    # Calculate average engagement per user
    from sqlalchemy import Float
    from sqlalchemy import cast

    users = db.query(
        TwitterUser,
        func.avg(Tweet.engagement_rate).label('avg_engagement')
    ).join(Tweet).group_by(TwitterUser.id).order_by(
        desc('avg_engagement')
    ).limit(limit).all()

    result = []
    for user, avg_engagement in users:
        result.append({
            "username": user.username,
            "display_name": user.display_name,
            "followers_count": user.followers_count,
            "avg_engagement_rate": round(avg_engagement, 2) if avg_engagement else 0
        })

    return result


@router.get("/trending/tweets")
async def get_trending_tweets(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get trending tweets (highest engagement in recent hours)."""

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    tweets = db.query(Tweet).filter(
        Tweet.scraped_at >= cutoff_time
    ).order_by(desc(Tweet.engagement_rate)).limit(limit).all()

    result = []
    for tweet in tweets:
        result.append({
            "tweet_id": tweet.tweet_id,
            "username": tweet.user.username,
            "text": tweet.text,
            "likes": tweet.likes_count,
            "retweets": tweet.retweets_count,
            "engagement_rate": tweet.engagement_rate,
            "posted_at": tweet.posted_at.isoformat() if tweet.posted_at else None
        })

    return result


@router.get("/trending/hashtags")
async def get_trending_hashtags(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get trending hashtags."""

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Get all tweets from the time period
    tweets = db.query(Tweet).filter(
        Tweet.scraped_at >= cutoff_time,
        Tweet.hashtags.isnot(None)
    ).all()

    # Count hashtags
    hashtag_counts = {}
    for tweet in tweets:
        for hashtag in tweet.hashtags or []:
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1

    # Sort and get top hashtags
    sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    result = []
    for hashtag, count in sorted_hashtags:
        result.append({
            "hashtag": hashtag,
            "count": count
        })

    return result


@router.get("/timeline")
async def get_timeline_data(
    days: int = Query(7, ge=1, le=30),
    username: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tweet timeline data for charts."""

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(
        func.date(Tweet.posted_at).label('date'),
        func.count(Tweet.id).label('count')
    ).filter(Tweet.posted_at >= cutoff_date)

    if username:
        query = query.join(TwitterUser).filter(TwitterUser.username == username)

    timeline = query.group_by(func.date(Tweet.posted_at)).order_by('date').all()

    result = []
    for date, count in timeline:
        result.append({
            "date": date.isoformat() if date else None,
            "count": count
        })

    return result


@router.get("/instance/health")
async def get_instance_health():
    """Get Nitter instance health status."""

    # Create temporary instance manager to check health
    manager = NitterInstanceManager(
        health_check_interval=settings.health_check_interval,
        request_timeout=settings.request_timeout
    )

    # Get stats without starting the health check loop
    stats = manager.get_stats()

    return {
        "total_instances": stats['total_instances'],
        "healthy_instances": stats['healthy_instances'],
        "unhealthy_instances": stats['unhealthy_instances'],
        "health_percentage": stats['health_percentage'],
        "avg_response_time": round(stats['avg_response_time'], 2) if stats['avg_response_time'] else None,
        "healthy_urls": stats['healthy_urls'],
        "unhealthy_urls": stats['unhealthy_urls']
    }
