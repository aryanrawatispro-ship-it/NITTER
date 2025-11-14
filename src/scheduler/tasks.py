"""
Celery tasks for background scraping jobs - TwitterAPI.io Only.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from celery import Task
from loguru import logger
import uuid

from .celery_app import celery_app
from src.scrapers.twitterapiio_scraper import TwitterAPIioScraper
from src.data_processing import (
    TextCleaner, DataExtractor, SentimentAnalyzer, EngagementCalculator
)
from src.utils.database import get_db_context
from src.utils.models import TwitterUser, Tweet, ScrapingJob, TwitterCommunity
from src.utils.config import settings


class AsyncTask(Task):
    """Base task class that runs async functions."""

    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))


async def process_tweet_data(tweet_data: Dict, user_followers: int) -> Dict:
    """Process tweet data with cleaning, extraction, and analysis."""
    # Clean text
    cleaner = TextCleaner()
    cleaned_text = cleaner.clean_text(tweet_data.get('text', ''))

    # Extract data
    extractor = DataExtractor()
    hashtags = extractor.extract_hashtags(tweet_data.get('text', ''))
    mentions = extractor.extract_mentions(tweet_data.get('text', ''))
    urls = extractor.extract_urls(tweet_data.get('text', ''))

    # Analyze sentiment
    analyzer = SentimentAnalyzer()
    sentiment, sentiment_score = analyzer.analyze(cleaned_text)

    # Calculate engagement
    calculator = EngagementCalculator()
    engagement_rate = calculator.calculate_engagement_rate(
        tweet_data.get('likes_count', 0),
        tweet_data.get('retweets_count', 0),
        tweet_data.get('replies_count', 0),
        user_followers
    )

    return {
        'tweet_id': tweet_data.get('tweet_id'),
        'text': tweet_data.get('text'),
        'html_text': tweet_data.get('html_text'),
        'tweet_url': tweet_data.get('tweet_url'),
        'likes_count': tweet_data.get('likes_count', 0),
        'retweets_count': tweet_data.get('retweets_count', 0),
        'replies_count': tweet_data.get('replies_count', 0),
        'quotes_count': tweet_data.get('quotes_count', 0),
        'community_id': tweet_data.get('community_id'),
        'hashtags': hashtags,
        'mentions': mentions,
        'urls': urls,
        'has_media': tweet_data.get('has_media', False),
        'media_urls': tweet_data.get('media_urls', []),
        'sentiment': sentiment,
        'sentiment_score': sentiment_score,
        'engagement_rate': engagement_rate,
        'posted_at': tweet_data.get('posted_at'),
        'created_at': tweet_data.get('created_at', datetime.utcnow())
    }


@celery_app.task(bind=True, base=AsyncTask, max_retries=3)
async def scrape_community_tweets(self, community_id: str, max_tweets: int = None) -> List[Dict]:
    """
    Scrape tweets from a Twitter community using TwitterAPI.io.

    Args:
        community_id: Twitter community ID
        max_tweets: Maximum tweets to scrape (None = ALL tweets)

    Returns:
        List of tweet dictionaries
    """
    job_id = str(uuid.uuid4())

    if max_tweets is None:
        logger.info(f"Starting community scrape job {job_id} for community {community_id} (ALL tweets)")
    else:
        logger.info(f"Starting community scrape job {job_id} for community {community_id} (max {max_tweets})")

    with get_db_context() as db:
        job = ScrapingJob(
            job_id=job_id,
            job_type='community',
            target=community_id,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

    try:
        # Check if TwitterAPI.io is configured
        if not settings.twitterapiio_api_key:
            raise Exception("TwitterAPI.io API key not configured. Please set TWITTERAPIIO_API_KEY in .env file")

        tweets = []
        community_data = None

        # Use TwitterAPI.io
        logger.info(f"Using TwitterAPI.io for community {community_id}")
        scraper = TwitterAPIioScraper(settings.twitterapiio_api_key)
        tweets = await scraper.scrape_community_tweets(community_id, max_tweets)

        if tweets:
            logger.info(f"Successfully scraped {len(tweets)} tweets via TwitterAPI.io")
            # Also get community details
            community_data = await scraper.get_community(community_id)
        else:
            logger.warning(f"No tweets found for community {community_id}")

        # Save community details if we got them
        if community_data:
            with get_db_context() as db:
                community = db.query(TwitterCommunity).filter_by(community_id=community_id).first()

                if community:
                    # Update existing community
                    for key, value in community_data.items():
                        if hasattr(community, key) and key != 'community_id':
                            setattr(community, key, value)
                    community.updated_at = datetime.utcnow()
                    community.last_scraped = datetime.utcnow()
                else:
                    # Create new community
                    community = TwitterCommunity(**community_data)
                    community.last_scraped = datetime.utcnow()
                    db.add(community)

                db.commit()

        # Save tweets
        saved_count = 0
        with get_db_context() as db:
            for tweet_data in tweets:
                # Get or create user
                user = db.query(TwitterUser).filter_by(username=tweet_data.get('username')).first()
                if not user and tweet_data.get('username'):
                    user = TwitterUser(username=tweet_data['username'])
                    db.add(user)
                    db.flush()

                # Check if tweet exists
                existing_tweet = db.query(Tweet).filter_by(tweet_id=tweet_data['tweet_id']).first()

                if not existing_tweet:
                    processed_data = await process_tweet_data(tweet_data, user.followers_count if user else 0)

                    tweet = Tweet(
                        user_id=user.id if user else None,
                        **processed_data
                    )
                    db.add(tweet)
                    saved_count += 1

            # Update community last_scraped
            community = db.query(TwitterCommunity).filter_by(community_id=community_id).first()
            if community:
                community.last_scraped = datetime.utcnow()

            # Update job
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration = (job.completed_at - job.started_at).total_seconds()
            job.items_scraped = saved_count

            db.commit()

        logger.info(f"Successfully completed community scrape job {job_id}: {saved_count} new tweets")
        return tweets

    except Exception as e:
        logger.error(f"Error in community scrape job {job_id}: {e}")

        with get_db_context() as db:
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()

        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="check_tracked_communities")
def check_tracked_communities():
    """Periodic task to scrape tracked communities."""
    logger.info("Checking tracked communities...")

    with get_db_context() as db:
        communities = db.query(TwitterCommunity).filter_by(is_tracked=True).all()

        for community in communities:
            # Check if it's time to scrape based on check_interval
            if community.last_scraped:
                time_since_last = datetime.utcnow() - community.last_scraped
                if time_since_last.total_seconds() < community.check_interval:
                    continue

            logger.info(f"Triggering scrape for tracked community: {community.community_id}")
            scrape_community_tweets.delay(community.community_id)

    logger.info("Finished checking tracked communities")
