"""
User management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.utils.database import get_db
from src.utils.models import TwitterUser
from src.scheduler.tasks import scrape_user_profile, scrape_user_timeline, schedule_user_tracking

router = APIRouter()


class TrackUserRequest(BaseModel):
    username: str
    check_interval: int = 900  # 15 minutes default


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    bio: Optional[str]
    followers_count: int
    following_count: int
    tweets_count: int
    is_tracked: bool
    last_scraped: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("/track", status_code=201)
async def track_user(request: TrackUserRequest, db: Session = Depends(get_db)):
    """
    Start tracking a Twitter user.

    This will scrape their profile and timeline, then schedule periodic updates.
    """
    # Schedule tracking
    schedule_user_tracking(request.username, request.check_interval)

    # Trigger immediate scrape
    scrape_user_profile.delay(request.username)
    scrape_user_timeline.delay(request.username)

    return {
        "message": f"Started tracking @{request.username}",
        "username": request.username,
        "check_interval": request.check_interval
    }


@router.delete("/track/{username}")
async def untrack_user(username: str, db: Session = Depends(get_db)):
    """Stop tracking a user."""
    user = db.query(TwitterUser).filter_by(username=username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_tracked = False
    db.commit()

    return {"message": f"Stopped tracking @{username}"}


@router.get("/tracked", response_model=List[UserResponse])
async def get_tracked_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get list of tracked users."""
    users = db.query(TwitterUser).filter_by(is_tracked=True).offset(skip).limit(limit).all()
    return users


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str, db: Session = Depends(get_db)):
    """Get user profile data."""
    user = db.query(TwitterUser).filter_by(username=username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/{username}/scrape")
async def scrape_user(username: str):
    """Manually trigger a user scrape."""
    scrape_user_profile.delay(username)
    scrape_user_timeline.delay(username)

    return {
        "message": f"Scraping @{username}",
        "username": username
    }


@router.get("/{username}/stats")
async def get_user_stats(username: str, db: Session = Depends(get_db)):
    """Get statistics for a user."""
    user = db.query(TwitterUser).filter_by(username=username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from src.utils.models import Tweet
    from sqlalchemy import func

    total_tweets = db.query(func.count(Tweet.id)).filter_by(user_id=user.id).scalar()
    avg_likes = db.query(func.avg(Tweet.likes_count)).filter_by(user_id=user.id).scalar() or 0
    avg_retweets = db.query(func.avg(Tweet.retweets_count)).filter_by(user_id=user.id).scalar() or 0
    avg_engagement = db.query(func.avg(Tweet.engagement_rate)).filter_by(user_id=user.id).scalar() or 0

    return {
        "username": username,
        "total_tweets_scraped": total_tweets,
        "avg_likes": round(avg_likes, 2),
        "avg_retweets": round(avg_retweets, 2),
        "avg_engagement_rate": round(avg_engagement, 2),
        "followers_count": user.followers_count,
        "following_count": user.following_count,
    }
