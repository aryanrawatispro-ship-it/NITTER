"""
Community scraping API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from loguru import logger
from sqlalchemy.orm import Session
from src.utils.database import get_db
from src.utils.models import TwitterCommunity, Tweet
from src.scheduler.tasks import scrape_community_tweets
from fastapi import Depends

router = APIRouter()


@router.post("/{community_id}/scrape")
async def scrape_community(
    community_id: str,
    max_tweets: Optional[int] = Query(None, description="Maximum tweets to scrape (None = ALL tweets)")
):
    """
    Scrape tweets from a Twitter community.

    - **community_id**: Twitter community ID (from URL: twitter.com/i/communities/COMMUNITY_ID)
    - **max_tweets**: Maximum number of tweets to scrape (default: None = scrape ALL tweets)
    """
    try:
        logger.info(f"Starting community scrape: {community_id}, max_tweets: {max_tweets}")

        # Trigger scraping task
        result = await scrape_community_tweets.apply_async(
            args=[community_id, max_tweets]
        ).get(timeout=300)  # 5 minute timeout

        return {
            "status": "success",
            "community_id": community_id,
            "tweets_scraped": len(result) if result else 0,
            "message": f"Successfully scraped {len(result) if result else 0} tweets from community"
        }
    except Exception as e:
        logger.error(f"Error scraping community {community_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{community_id}/track")
async def track_community(
    community_id: str,
    check_interval: int = Query(3600, description="Check interval in seconds (default: 1 hour)"),
    db: Session = Depends(get_db)
):
    """
    Track a community for automatic scraping.

    - **community_id**: Twitter community ID
    - **check_interval**: How often to scrape (in seconds, default: 3600 = 1 hour)
    """
    try:
        # Get or create community
        community = db.query(TwitterCommunity).filter(
            TwitterCommunity.community_id == community_id
        ).first()

        if not community:
            # Create new community
            community = TwitterCommunity(
                community_id=community_id,
                name=f"Community {community_id}",
                is_tracked=True,
                check_interval=check_interval
            )
            db.add(community)
        else:
            # Update existing
            community.is_tracked = True
            community.check_interval = check_interval

        db.commit()

        return {
            "status": "success",
            "community_id": community_id,
            "check_interval": check_interval,
            "message": f"Community is now being tracked every {check_interval} seconds"
        }
    except Exception as e:
        logger.error(f"Error tracking community {community_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{community_id}/untrack")
async def untrack_community(
    community_id: str,
    db: Session = Depends(get_db)
):
    """
    Stop tracking a community.

    - **community_id**: Twitter community ID
    """
    try:
        community = db.query(TwitterCommunity).filter(
            TwitterCommunity.community_id == community_id
        ).first()

        if not community:
            raise HTTPException(status_code=404, detail="Community not found")

        community.is_tracked = False
        db.commit()

        return {
            "status": "success",
            "community_id": community_id,
            "message": "Community tracking stopped"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error untracking community {community_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{community_id}/tweets")
async def get_community_tweets(
    community_id: str,
    limit: int = Query(100, description="Maximum number of tweets to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get scraped tweets from a community.

    - **community_id**: Twitter community ID
    - **limit**: Maximum tweets to return (default: 100)
    - **offset**: Offset for pagination (default: 0)
    """
    try:
        tweets = db.query(Tweet).filter(
            Tweet.community_id == community_id
        ).order_by(
            Tweet.created_at.desc()
        ).limit(limit).offset(offset).all()

        return {
            "status": "success",
            "community_id": community_id,
            "count": len(tweets),
            "tweets": [
                {
                    "tweet_id": tweet.tweet_id,
                    "username": tweet.user.username if tweet.user else None,
                    "text": tweet.text,
                    "tweet_url": tweet.tweet_url,
                    "likes_count": tweet.likes_count,
                    "retweets_count": tweet.retweets_count,
                    "replies_count": tweet.replies_count,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None
                }
                for tweet in tweets
            ]
        }
    except Exception as e:
        logger.error(f"Error getting tweets for community {community_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tracked_communities(db: Session = Depends(get_db)):
    """
    List all tracked communities.
    """
    try:
        communities = db.query(TwitterCommunity).filter(
            TwitterCommunity.is_tracked == True
        ).all()

        return {
            "status": "success",
            "count": len(communities),
            "communities": [
                {
                    "community_id": c.community_id,
                    "name": c.name,
                    "member_count": c.member_count,
                    "check_interval": c.check_interval,
                    "last_scraped": c.last_scraped.isoformat() if c.last_scraped else None
                }
                for c in communities
            ]
        }
    except Exception as e:
        logger.error(f"Error listing communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{community_id}")
async def get_community_info(
    community_id: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a community.

    - **community_id**: Twitter community ID
    """
    try:
        community = db.query(TwitterCommunity).filter(
            TwitterCommunity.community_id == community_id
        ).first()

        if not community:
            raise HTTPException(status_code=404, detail="Community not found")

        # Count tweets
        tweet_count = db.query(Tweet).filter(
            Tweet.community_id == community_id
        ).count()

        return {
            "status": "success",
            "community": {
                "community_id": community.community_id,
                "name": community.name,
                "description": community.description,
                "member_count": community.member_count,
                "is_tracked": community.is_tracked,
                "check_interval": community.check_interval,
                "last_scraped": community.last_scraped.isoformat() if community.last_scraped else None,
                "tweets_scraped": tweet_count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting community info for {community_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
