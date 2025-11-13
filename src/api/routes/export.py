"""
Data export API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime
import csv
import json
import io
from typing import Optional

from src.utils.database import get_db
from src.utils.models import Tweet, TwitterUser

router = APIRouter()


@router.get("/tweets/csv")
async def export_tweets_csv(
    username: Optional[str] = None,
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db)
):
    """Export tweets to CSV format."""

    query = db.query(Tweet).join(TwitterUser)

    if username:
        query = query.filter(TwitterUser.username == username)

    tweets = query.limit(limit).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets found")

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'tweet_id', 'username', 'text', 'likes_count', 'retweets_count',
        'replies_count', 'engagement_rate', 'sentiment', 'posted_at', 'scraped_at'
    ])

    # Write data
    for tweet in tweets:
        writer.writerow([
            tweet.tweet_id,
            tweet.user.username,
            tweet.text,
            tweet.likes_count,
            tweet.retweets_count,
            tweet.replies_count,
            tweet.engagement_rate,
            tweet.sentiment,
            tweet.posted_at.isoformat() if tweet.posted_at else '',
            tweet.scraped_at.isoformat()
        ])

    output.seek(0)
    filename = f"tweets_{username or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/tweets/json")
async def export_tweets_json(
    username: Optional[str] = None,
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db)
):
    """Export tweets to JSON format."""

    query = db.query(Tweet).join(TwitterUser)

    if username:
        query = query.filter(TwitterUser.username == username)

    tweets = query.limit(limit).all()

    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets found")

    # Build JSON data
    data = []
    for tweet in tweets:
        data.append({
            'tweet_id': tweet.tweet_id,
            'username': tweet.user.username,
            'text': tweet.text,
            'likes_count': tweet.likes_count,
            'retweets_count': tweet.retweets_count,
            'replies_count': tweet.replies_count,
            'quotes_count': tweet.quotes_count,
            'engagement_rate': tweet.engagement_rate,
            'sentiment': tweet.sentiment,
            'sentiment_score': tweet.sentiment_score,
            'hashtags': tweet.hashtags,
            'mentions': tweet.mentions,
            'urls': tweet.urls,
            'has_media': tweet.has_media,
            'media_urls': tweet.media_urls,
            'posted_at': tweet.posted_at.isoformat() if tweet.posted_at else None,
            'scraped_at': tweet.scraped_at.isoformat()
        })

    filename = f"tweets_{username or 'all'}_{datetime.now().strftime('%Y%m%d')}.json"

    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/users/csv")
async def export_users_csv(
    tracked_only: bool = False,
    db: Session = Depends(get_db)
):
    """Export user profiles to CSV format."""

    query = db.query(TwitterUser)

    if tracked_only:
        query = query.filter_by(is_tracked=True)

    users = query.all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'username', 'display_name', 'bio', 'followers_count',
        'following_count', 'tweets_count', 'is_verified', 'is_tracked'
    ])

    # Write data
    for user in users:
        writer.writerow([
            user.username,
            user.display_name or '',
            user.bio or '',
            user.followers_count,
            user.following_count,
            user.tweets_count,
            user.is_verified,
            user.is_tracked
        ])

    output.seek(0)
    filename = f"users_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/users/json")
async def export_users_json(
    tracked_only: bool = False,
    db: Session = Depends(get_db)
):
    """Export user profiles to JSON format."""

    query = db.query(TwitterUser)

    if tracked_only:
        query = query.filter_by(is_tracked=True)

    users = query.all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    data = []
    for user in users:
        data.append({
            'username': user.username,
            'display_name': user.display_name,
            'bio': user.bio,
            'location': user.location,
            'website': user.website,
            'followers_count': user.followers_count,
            'following_count': user.following_count,
            'tweets_count': user.tweets_count,
            'is_verified': user.is_verified,
            'is_tracked': user.is_tracked,
            'joined_date': user.joined_date.isoformat() if user.joined_date else None,
            'last_scraped': user.last_scraped.isoformat() if user.last_scraped else None
        })

    filename = f"users_{datetime.now().strftime('%Y%m%d')}.json"

    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
