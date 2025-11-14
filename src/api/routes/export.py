"""
Community tweet export API endpoints.
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


@router.get("/community/csv")
async def export_community_csv(
    community_id: str = Query(..., description="Twitter community ID"),
    limit: int = Query(10000, le=100000, description="Maximum tweets to export"),
    db: Session = Depends(get_db)
):
    """
    Export community tweets to CSV format.

    Fields exported:
    - username
    - content (tweet text)
    - likes
    - retweets
    - comments (replies)
    - post_link (tweet URL)
    - posted_at
    """

    tweets = db.query(Tweet).join(TwitterUser).filter(
        Tweet.community_id == community_id
    ).order_by(Tweet.created_at.desc()).limit(limit).all()

    if not tweets:
        raise HTTPException(status_code=404, detail=f"No tweets found for community {community_id}")

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'username',
        'content',
        'likes',
        'retweets',
        'comments',
        'post_link',
        'posted_at'
    ])

    # Write data
    for tweet in tweets:
        writer.writerow([
            tweet.user.username if tweet.user else '',
            tweet.text,
            tweet.likes_count,
            tweet.retweets_count,
            tweet.replies_count,
            tweet.tweet_url or '',
            tweet.created_at.isoformat() if tweet.created_at else ''
        ])

    output.seek(0)
    filename = f"community_{community_id}_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/community/json")
async def export_community_json(
    community_id: str = Query(..., description="Twitter community ID"),
    limit: int = Query(10000, le=100000, description="Maximum tweets to export"),
    db: Session = Depends(get_db)
):
    """
    Export community tweets to JSON format.

    Includes all available fields for each tweet.
    """

    tweets = db.query(Tweet).join(TwitterUser).filter(
        Tweet.community_id == community_id
    ).order_by(Tweet.created_at.desc()).limit(limit).all()

    if not tweets:
        raise HTTPException(status_code=404, detail=f"No tweets found for community {community_id}")

    # Build JSON data
    data = []
    for tweet in tweets:
        data.append({
            'tweet_id': tweet.tweet_id,
            'username': tweet.user.username if tweet.user else None,
            'content': tweet.text,
            'tweet_url': tweet.tweet_url,
            'likes': tweet.likes_count,
            'retweets': tweet.retweets_count,
            'comments': tweet.replies_count,
            'quotes_count': tweet.quotes_count,
            'hashtags': tweet.hashtags,
            'mentions': tweet.mentions,
            'urls': tweet.urls,
            'has_media': tweet.has_media,
            'media_urls': tweet.media_urls,
            'posted_at': tweet.created_at.isoformat() if tweet.created_at else None,
            'scraped_at': tweet.scraped_at.isoformat() if tweet.scraped_at else None
        })

    filename = f"community_{community_id}_{datetime.now().strftime('%Y%m%d')}.json"

    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
