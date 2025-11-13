"""
Celery tasks for background scraping jobs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from celery import Task
from loguru import logger
import uuid

from .celery_app import celery_app
from src.nitter_manager import NitterInstanceManager
from src.scrapers import ProfileScraper, TimelineScraper, SearchScraper, ThreadScraper
from src.data_processing import (
    TextCleaner, DataExtractor, SentimentAnalyzer, EngagementCalculator
)
from src.utils.database import get_db_context
from src.utils.models import TwitterUser, Tweet, SearchQuery, ScrapingJob
from src.utils.config import settings


# Initialize Nitter instance manager
instance_manager = NitterInstanceManager(
    health_check_interval=settings.health_check_interval,
    request_timeout=settings.request_timeout
)


class AsyncTask(Task):
    """Base task class that runs async functions."""

    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))


@celery_app.task(bind=True, base=AsyncTask, max_retries=3)
async def scrape_user_profile(self, username: str) -> Dict:
    """
    Scrape a user's profile.

    Args:
        username: Twitter username

    Returns:
        Dictionary with profile data
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Starting profile scrape job {job_id} for {username}")

    # Create scraping job record
    with get_db_context() as db:
        job = ScrapingJob(
            job_id=job_id,
            job_type='profile',
            target=username,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

    try:
        # Ensure instance manager is started
        if not instance_manager._health_check_task:
            await instance_manager.start()

        # Scrape profile
        async with ProfileScraper(instance_manager) as scraper:
            profile_data = await scraper.scrape_profile(username)

        if not profile_data:
            raise Exception(f"Failed to scrape profile: {username}")

        # Save to database
        with get_db_context() as db:
            user = db.query(TwitterUser).filter_by(username=username).first()

            if user:
                # Update existing user
                for key, value in profile_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                user.updated_at = datetime.utcnow()
                user.last_scraped = datetime.utcnow()
            else:
                # Create new user
                user = TwitterUser(**profile_data)
                user.last_scraped = datetime.utcnow()
                db.add(user)

            # Update job status
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration = (job.completed_at - job.started_at).total_seconds()
            job.items_scraped = 1
            job.nitter_instance = instance_manager.current_instance

            db.commit()

        logger.info(f"Successfully completed profile scrape job {job_id}")
        return profile_data

    except Exception as e:
        logger.error(f"Error in profile scrape job {job_id}: {e}")

        with get_db_context() as db:
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, base=AsyncTask, max_retries=3)
async def scrape_user_timeline(self, username: str, max_tweets: int = 100) -> List[Dict]:
    """
    Scrape a user's timeline.

    Args:
        username: Twitter username
        max_tweets: Maximum tweets to scrape

    Returns:
        List of tweet dictionaries
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Starting timeline scrape job {job_id} for {username}")

    with get_db_context() as db:
        job = ScrapingJob(
            job_id=job_id,
            job_type='timeline',
            target=username,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

    try:
        if not instance_manager._health_check_task:
            await instance_manager.start()

        # Scrape timeline
        async with TimelineScraper(instance_manager) as scraper:
            tweets = await scraper.scrape_timeline(username, max_tweets)

        # Process and save tweets
        saved_count = 0
        with get_db_context() as db:
            # Get or create user
            user = db.query(TwitterUser).filter_by(username=username).first()
            if not user:
                user = TwitterUser(username=username)
                db.add(user)
                db.flush()

            for tweet_data in tweets:
                # Check if tweet already exists
                existing_tweet = db.query(Tweet).filter_by(
                    tweet_id=tweet_data['tweet_id']
                ).first()

                if existing_tweet:
                    # Update existing tweet
                    for key, value in tweet_data.items():
                        if hasattr(existing_tweet, key) and key != 'scraped_at':
                            setattr(existing_tweet, key, value)
                else:
                    # Process tweet data
                    processed_data = await process_tweet_data(tweet_data, user.followers_count)

                    # Create new tweet
                    tweet = Tweet(
                        user_id=user.id,
                        nitter_instance=instance_manager.current_instance,
                        **processed_data
                    )
                    db.add(tweet)
                    saved_count += 1

            user.last_scraped = datetime.utcnow()

            # Update job
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration = (job.completed_at - job.started_at).total_seconds()
            job.items_scraped = saved_count
            job.nitter_instance = instance_manager.current_instance

            db.commit()

        logger.info(f"Successfully completed timeline scrape job {job_id}: {saved_count} new tweets")
        return tweets

    except Exception as e:
        logger.error(f"Error in timeline scrape job {job_id}: {e}")

        with get_db_context() as db:
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, base=AsyncTask, max_retries=3)
async def scrape_search_results(self, query: str, search_type: str = 'keyword', max_tweets: int = 100) -> List[Dict]:
    """
    Scrape search results.

    Args:
        query: Search query
        search_type: Type of search
        max_tweets: Maximum tweets to scrape

    Returns:
        List of tweet dictionaries
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Starting search scrape job {job_id} for query: {query}")

    with get_db_context() as db:
        job = ScrapingJob(
            job_id=job_id,
            job_type='search',
            target=query,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

    try:
        if not instance_manager._health_check_task:
            await instance_manager.start()

        # Scrape search results
        async with SearchScraper(instance_manager) as scraper:
            tweets = await scraper.scrape_search(query, max_tweets, search_type)

        # Save tweets
        saved_count = 0
        with get_db_context() as db:
            for tweet_data in tweets:
                # Get or create user
                user = db.query(TwitterUser).filter_by(username=tweet_data['username']).first()
                if not user:
                    user = TwitterUser(username=tweet_data['username'])
                    db.add(user)
                    db.flush()

                # Check if tweet exists
                existing_tweet = db.query(Tweet).filter_by(tweet_id=tweet_data['tweet_id']).first()

                if not existing_tweet:
                    processed_data = await process_tweet_data(tweet_data, user.followers_count)

                    tweet = Tweet(
                        user_id=user.id,
                        nitter_instance=instance_manager.current_instance,
                        **processed_data
                    )
                    db.add(tweet)
                    saved_count += 1

            # Update search query tracking
            search_query = db.query(SearchQuery).filter_by(query=query).first()
            if search_query:
                search_query.last_executed = datetime.utcnow()
                search_query.last_result_count = len(tweets)
                search_query.total_results += saved_count

            # Update job
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration = (job.completed_at - job.started_at).total_seconds()
            job.items_scraped = saved_count
            job.nitter_instance = instance_manager.current_instance

            db.commit()

        logger.info(f"Successfully completed search scrape job {job_id}: {saved_count} new tweets")
        return tweets

    except Exception as e:
        logger.error(f"Error in search scrape job {job_id}: {e}")

        with get_db_context() as db:
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, base=AsyncTask)
async def scrape_thread(self, tweet_url: str) -> List[Dict]:
    """
    Scrape a tweet thread.

    Args:
        tweet_url: Tweet URL

    Returns:
        List of tweets in thread
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Starting thread scrape job {job_id} for {tweet_url}")

    with get_db_context() as db:
        job = ScrapingJob(
            job_id=job_id,
            job_type='thread',
            target=tweet_url,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

    try:
        if not instance_manager._health_check_task:
            await instance_manager.start()

        async with ThreadScraper(instance_manager) as scraper:
            tweets = await scraper.scrape_thread(tweet_url)

        # Save tweets
        saved_count = 0
        with get_db_context() as db:
            for tweet_data in tweets:
                user = db.query(TwitterUser).filter_by(username=tweet_data['username']).first()
                if not user:
                    user = TwitterUser(username=tweet_data['username'])
                    db.add(user)
                    db.flush()

                existing_tweet = db.query(Tweet).filter_by(tweet_id=tweet_data['tweet_id']).first()

                if not existing_tweet:
                    processed_data = await process_tweet_data(tweet_data, user.followers_count)

                    tweet = Tweet(
                        user_id=user.id,
                        nitter_instance=instance_manager.current_instance,
                        **processed_data
                    )
                    db.add(tweet)
                    saved_count += 1

            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.duration = (job.completed_at - job.started_at).total_seconds()
            job.items_scraped = saved_count
            job.nitter_instance = instance_manager.current_instance

            db.commit()

        logger.info(f"Successfully completed thread scrape job {job_id}")
        return tweets

    except Exception as e:
        logger.error(f"Error in thread scrape job {job_id}: {e}")

        with get_db_context() as db:
            job = db.query(ScrapingJob).filter_by(job_id=job_id).first()
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise


# Periodic tasks

@celery_app.task
def check_tracked_users():
    """Check and scrape tracked users based on their schedule."""
    with get_db_context() as db:
        now = datetime.utcnow()

        # Find users that need to be scraped
        users = db.query(TwitterUser).filter(
            TwitterUser.is_tracked == True
        ).all()

        for user in users:
            # Check if it's time to scrape
            if user.last_scraped is None:
                should_scrape = True
            else:
                next_scrape = user.last_scraped + timedelta(seconds=user.check_interval)
                should_scrape = now >= next_scrape

            if should_scrape:
                logger.info(f"Scheduling scrape for tracked user: {user.username}")
                scrape_user_timeline.delay(user.username)


@celery_app.task
def check_tracked_searches():
    """Check and execute tracked search queries."""
    with get_db_context() as db:
        now = datetime.utcnow()

        searches = db.query(SearchQuery).filter(
            SearchQuery.is_active == True
        ).all()

        for search in searches:
            if search.last_executed is None:
                should_execute = True
            else:
                next_execution = search.last_executed + timedelta(seconds=search.check_interval)
                should_execute = now >= next_execution

            if should_execute:
                logger.info(f"Scheduling search for: {search.query}")
                scrape_search_results.delay(search.query, search.query_type)


@celery_app.task
def cleanup_old_jobs():
    """Clean up old scraping jobs."""
    with get_db_context() as db:
        # Delete jobs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        deleted = db.query(ScrapingJob).filter(
            ScrapingJob.created_at < cutoff_date
        ).delete()

        db.commit()
        logger.info(f"Cleaned up {deleted} old scraping jobs")


# Helper functions

async def process_tweet_data(tweet_data: Dict, followers_count: int = 0) -> Dict:
    """Process tweet data with cleaning, extraction, and analysis."""

    text = tweet_data.get('text', '')

    # Sentiment analysis
    sentiment_data = SentimentAnalyzer.analyze_sentiment(text)

    # Calculate engagement
    engagement_rate = EngagementCalculator.calculate_engagement_rate(
        likes=tweet_data.get('likes_count', 0),
        retweets=tweet_data.get('retweets_count', 0),
        replies=tweet_data.get('replies_count', 0),
        quotes=tweet_data.get('quotes_count', 0),
        followers=followers_count
    ) if followers_count > 0 else 0.0

    # Prepare processed data
    processed = {
        'tweet_id': tweet_data.get('tweet_id'),
        'text': text,
        'html_text': tweet_data.get('html_text', ''),
        'posted_at': tweet_data.get('posted_at'),
        'likes_count': tweet_data.get('likes_count', 0),
        'retweets_count': tweet_data.get('retweets_count', 0),
        'replies_count': tweet_data.get('replies_count', 0),
        'quotes_count': tweet_data.get('quotes_count', 0),
        'engagement_rate': engagement_rate,
        'is_retweet': tweet_data.get('is_retweet', False),
        'is_reply': tweet_data.get('is_reply', False),
        'reply_to_username': tweet_data.get('reply_to_username'),
        'has_media': tweet_data.get('has_media', False),
        'media_urls': tweet_data.get('media_urls', []),
        'hashtags': tweet_data.get('hashtags', []),
        'mentions': tweet_data.get('mentions', []),
        'urls': tweet_data.get('urls', []),
        'sentiment': sentiment_data['sentiment'],
        'sentiment_score': sentiment_data['polarity'],
    }

    return processed


def schedule_user_tracking(username: str, interval: int = 900):
    """
    Schedule periodic tracking of a user.

    Args:
        username: Twitter username
        interval: Check interval in seconds
    """
    with get_db_context() as db:
        user = db.query(TwitterUser).filter_by(username=username).first()

        if user:
            user.is_tracked = True
            user.check_interval = interval
        else:
            # Create user and enable tracking
            user = TwitterUser(
                username=username,
                is_tracked=True,
                check_interval=interval
            )
            db.add(user)

        db.commit()
        logger.info(f"Scheduled tracking for {username} every {interval} seconds")


def schedule_search_tracking(query: str, query_type: str = 'keyword', interval: int = 3600):
    """
    Schedule periodic tracking of a search query.

    Args:
        query: Search query
        query_type: Type of query
        interval: Check interval in seconds
    """
    with get_db_context() as db:
        search = db.query(SearchQuery).filter_by(query=query).first()

        if search:
            search.is_active = True
            search.check_interval = interval
        else:
            search = SearchQuery(
                query=query,
                query_type=query_type,
                is_active=True,
                check_interval=interval
            )
            db.add(search)

        db.commit()
        logger.info(f"Scheduled tracking for search '{query}' every {interval} seconds")
