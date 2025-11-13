"""
TwitterAPI.io scraper - uses unofficial Twitter API service.
Much cheaper than official Twitter API ($0.15 per 1K tweets vs $100+/month)
"""

import httpx
from typing import Optional, Dict, List
from loguru import logger
from datetime import datetime

from src.utils.config import settings


class TwitterAPIioScraper:
    """Scraper using TwitterAPI.io service."""

    def __init__(self, api_key: str):
        """
        Initialize TwitterAPI.io scraper.

        Args:
            api_key: TwitterAPI.io API key
        """
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape a Twitter user's profile using TwitterAPI.io.

        Args:
            username: Twitter username (without @)

        Returns:
            Dictionary containing profile data or None if failed
        """
        username = username.lstrip('@')
        logger.info(f"Scraping profile via TwitterAPI.io: {username}")

        try:
            async with httpx.AsyncClient() as client:
                # Get user info
                response = await client.get(
                    f"{self.base_url}/users/by/username/{username}",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"TwitterAPI.io error {response.status_code}: {response.text}")
                    return None

                data = response.json()

                if not data or 'data' not in data:
                    logger.error(f"Invalid response from TwitterAPI.io: {data}")
                    return None

                user = data['data']

                # Map to our format
                profile_data = {
                    'username': user.get('username', username),
                    'display_name': user.get('name', username),
                    'bio': user.get('description', ''),
                    'location': user.get('location', ''),
                    'website': user.get('url', ''),
                    'profile_image_url': user.get('profile_image_url', ''),
                    'banner_image_url': user.get('profile_banner_url', ''),
                    'followers_count': user.get('public_metrics', {}).get('followers_count', 0),
                    'following_count': user.get('public_metrics', {}).get('following_count', 0),
                    'tweets_count': user.get('public_metrics', {}).get('tweet_count', 0),
                    'is_verified': user.get('verified', False),
                    'is_protected': user.get('protected', False),
                    'joined_date': None  # Parse created_at if needed
                }

                logger.info(f"Successfully scraped profile via TwitterAPI.io: {username}")
                return profile_data

        except httpx.TimeoutException:
            logger.error(f"Timeout scraping profile via TwitterAPI.io: {username}")
            return None
        except Exception as e:
            logger.error(f"Error scraping profile via TwitterAPI.io: {e}")
            return None

    async def scrape_timeline(self, username: str, max_tweets: int = 100) -> List[Dict]:
        """
        Scrape tweets from a user's timeline using TwitterAPI.io.

        Args:
            username: Twitter username
            max_tweets: Maximum number of tweets to scrape

        Returns:
            List of tweet dictionaries
        """
        username = username.lstrip('@')
        logger.info(f"Scraping timeline via TwitterAPI.io: {username} (max {max_tweets} tweets)")

        try:
            async with httpx.AsyncClient() as client:
                # Get user ID first
                user_response = await client.get(
                    f"{self.base_url}/users/by/username/{username}",
                    headers=self.headers,
                    timeout=30.0
                )

                if user_response.status_code != 200:
                    logger.error(f"Failed to get user ID: {user_response.text}")
                    return []

                user_data = user_response.json()
                user_id = user_data.get('data', {}).get('id')

                if not user_id:
                    logger.error(f"Could not find user ID for {username}")
                    return []

                # Get user tweets
                tweets_response = await client.get(
                    f"{self.base_url}/users/{user_id}/tweets",
                    headers=self.headers,
                    params={
                        "max_results": min(max_tweets, 100),  # API limit is 100
                        "tweet.fields": "created_at,public_metrics,entities,referenced_tweets"
                    },
                    timeout=30.0
                )

                if tweets_response.status_code != 200:
                    logger.error(f"Failed to get tweets: {tweets_response.text}")
                    return []

                tweets_data = tweets_response.json()
                tweets_list = tweets_data.get('data', [])

                # Map to our format
                tweets = []
                for tweet in tweets_list:
                    # Extract hashtags and mentions
                    entities = tweet.get('entities', {})
                    hashtags = [tag['tag'] for tag in entities.get('hashtags', [])]
                    mentions = [mention['username'] for mention in entities.get('mentions', [])]
                    urls = [url['expanded_url'] for url in entities.get('urls', [])]

                    # Get metrics
                    metrics = tweet.get('public_metrics', {})

                    # Check if retweet
                    referenced = tweet.get('referenced_tweets', [])
                    is_retweet = any(ref.get('type') == 'retweeted' for ref in referenced)
                    is_reply = any(ref.get('type') == 'replied_to' for ref in referenced)

                    tweet_data = {
                        'tweet_id': tweet.get('id'),
                        'username': username,
                        'text': tweet.get('text', ''),
                        'html_text': tweet.get('text', ''),
                        'posted_at': datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00')) if tweet.get('created_at') else datetime.utcnow(),
                        'likes_count': metrics.get('like_count', 0),
                        'retweets_count': metrics.get('retweet_count', 0),
                        'replies_count': metrics.get('reply_count', 0),
                        'quotes_count': metrics.get('quote_count', 0),
                        'is_retweet': is_retweet,
                        'is_reply': is_reply,
                        'reply_to_username': None,  # Would need to parse referenced_tweets
                        'has_media': False,  # Would need to check attachments
                        'media_urls': [],
                        'hashtags': hashtags,
                        'mentions': mentions,
                        'urls': urls,
                    }

                    tweets.append(tweet_data)

                logger.info(f"Successfully scraped {len(tweets)} tweets via TwitterAPI.io")
                return tweets

        except httpx.TimeoutException:
            logger.error(f"Timeout scraping timeline via TwitterAPI.io: {username}")
            return []
        except Exception as e:
            logger.error(f"Error scraping timeline via TwitterAPI.io: {e}")
            return []

    async def search_tweets(self, query: str, max_tweets: int = 100) -> List[Dict]:
        """
        Search for tweets using TwitterAPI.io.

        Args:
            query: Search query
            max_tweets: Maximum number of tweets to return

        Returns:
            List of tweet dictionaries
        """
        logger.info(f"Searching tweets via TwitterAPI.io: {query}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tweets/search/recent",
                    headers=self.headers,
                    params={
                        "query": query,
                        "max_results": min(max_tweets, 100),
                        "tweet.fields": "created_at,public_metrics,entities,author_id"
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"Search failed: {response.text}")
                    return []

                data = response.json()
                tweets_list = data.get('data', [])

                # Map to our format (similar to scrape_timeline)
                tweets = []
                for tweet in tweets_list:
                    entities = tweet.get('entities', {})
                    hashtags = [tag['tag'] for tag in entities.get('hashtags', [])]
                    mentions = [mention['username'] for mention in entities.get('mentions', [])]

                    metrics = tweet.get('public_metrics', {})

                    tweet_data = {
                        'tweet_id': tweet.get('id'),
                        'username': None,  # Would need to fetch user data
                        'text': tweet.get('text', ''),
                        'html_text': tweet.get('text', ''),
                        'posted_at': datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00')) if tweet.get('created_at') else datetime.utcnow(),
                        'likes_count': metrics.get('like_count', 0),
                        'retweets_count': metrics.get('retweet_count', 0),
                        'replies_count': metrics.get('reply_count', 0),
                        'quotes_count': metrics.get('quote_count', 0),
                        'is_retweet': False,
                        'is_reply': False,
                        'reply_to_username': None,
                        'has_media': False,
                        'media_urls': [],
                        'hashtags': hashtags,
                        'mentions': mentions,
                        'urls': [],
                    }

                    tweets.append(tweet_data)

                logger.info(f"Successfully found {len(tweets)} tweets via TwitterAPI.io")
                return tweets

        except Exception as e:
            logger.error(f"Error searching via TwitterAPI.io: {e}")
            return []
