"""
Direct Twitter.com scraper - bypasses Nitter by scraping Twitter directly.
Requires a Twitter account for login.
"""

import asyncio
from typing import Optional, Dict, List
from loguru import logger
from datetime import datetime
import re

from .base_scraper import BaseScraper


class TwitterDirectScraper(BaseScraper):
    """Scraper that works directly on twitter.com instead of Nitter."""

    def __init__(self, instance_manager, twitter_username: str = None, twitter_password: str = None):
        """
        Initialize direct Twitter scraper.

        Args:
            instance_manager: NitterInstanceManager (kept for compatibility)
            twitter_username: Twitter account username for login
            twitter_password: Twitter account password for login
        """
        super().__init__(instance_manager)
        self.twitter_username = twitter_username
        self.twitter_password = twitter_password
        self.is_logged_in = False
        self.base_url = "https://twitter.com"

    async def login(self) -> bool:
        """
        Login to Twitter.com.

        Returns:
            True if login successful, False otherwise
        """
        if not self.twitter_username or not self.twitter_password:
            logger.warning("No Twitter credentials provided, skipping login")
            return False

        if self.is_logged_in:
            return True

        try:
            logger.info("Logging in to Twitter...")

            # Go to login page
            await self.page.goto(f"{self.base_url}/login", wait_until='networkidle')
            await self.random_delay()

            # Enter username
            username_input = await self.page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            await username_input.fill(self.twitter_username)
            await self.random_delay()

            # Click Next
            await self.page.click('button:has-text("Next")')
            await self.random_delay()

            # Enter password
            password_input = await self.page.wait_for_selector('input[name="password"]', timeout=10000)
            await password_input.fill(self.twitter_password)
            await self.random_delay()

            # Click Login
            await self.page.click('button[data-testid="LoginForm_Login_Button"]')

            # Wait for navigation to complete
            await asyncio.sleep(5)

            # Check if logged in by looking for home timeline
            current_url = self.page.url
            if 'home' in current_url or 'twitter.com' in current_url:
                self.is_logged_in = True
                logger.info("Successfully logged in to Twitter")
                return True
            else:
                logger.error("Login failed - unexpected URL: " + current_url)
                return False

        except Exception as e:
            logger.error(f"Error during Twitter login: {e}")
            return False

    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape a Twitter user's profile from twitter.com.

        Args:
            username: Twitter username (without @)

        Returns:
            Dictionary containing profile data or None if failed
        """
        username = username.lstrip('@')
        profile_url = f"{self.base_url}/{username}"

        logger.info(f"Scraping Twitter profile: {username}")

        # Login if credentials provided
        if self.twitter_username and not self.is_logged_in:
            await self.login()

        # Navigate to profile
        success = await self.navigate_to_url(profile_url)
        if not success:
            logger.error(f"Failed to navigate to profile: {username}")
            return None

        await self.random_delay()

        try:
            # Wait for profile to load
            await asyncio.sleep(3)

            profile_data = await self._extract_profile_data(username)
            logger.info(f"Successfully scraped Twitter profile: {username}")
            return profile_data

        except Exception as e:
            logger.error(f"Error extracting profile data for {username}: {e}")
            return None

    async def _extract_profile_data(self, username: str) -> Dict:
        """Extract profile data from Twitter.com page."""

        # Extract display name
        display_name = await self.extract_text('[data-testid="UserName"] span', username)

        # Extract bio
        bio = await self.extract_text('[data-testid="UserDescription"]', '')

        # Extract location
        location = await self.extract_text('[data-testid="UserLocation"] span', '')

        # Extract website
        website = await self.extract_attribute('[data-testid="UserUrl"] a', 'href', '')

        # Extract profile image
        profile_image = await self.extract_attribute('[data-testid="UserAvatar"] img', 'src', '')

        # Extract banner image
        banner_image = await self.extract_attribute('[data-testid="UserBanner"] img', 'src', '')

        # Extract stats - Twitter uses specific patterns
        followers_count = await self._extract_stat_by_text('Followers')
        following_count = await self._extract_stat_by_text('Following')

        # Try to get tweet count from profile
        tweets_count = 0
        try:
            # Posts count is usually visible in the profile
            posts_text = await self.extract_text('[href$="/posts"] span', '0')
            tweets_count = self._parse_number(posts_text)
        except:
            pass

        # Check verification
        is_verified = await self.page.query_selector('[data-testid="icon-verified"]') is not None

        return {
            'username': username,
            'display_name': display_name,
            'bio': bio,
            'location': location,
            'website': website,
            'profile_image_url': profile_image,
            'banner_image_url': banner_image,
            'followers_count': followers_count,
            'following_count': following_count,
            'tweets_count': tweets_count,
            'is_verified': is_verified,
            'is_protected': False,  # Twitter.com doesn't easily show this
            'joined_date': None,  # Would need to click "More" to get this
        }

    async def _extract_stat_by_text(self, stat_name: str) -> int:
        """Extract follower/following counts from Twitter."""
        try:
            # Twitter shows stats as "123 Following", "456 Followers"
            stat_element = await self.page.query_selector(f'a[href*="/{stat_name.lower()}"] span')
            if stat_element:
                text = await stat_element.text_content()
                return self._parse_number(text)
        except Exception as e:
            logger.debug(f"Error extracting {stat_name}: {e}")
        return 0

    def _parse_number(self, text: str) -> int:
        """Parse number from text like '1.2M', '123K', '456'."""
        text = text.strip().upper()

        if not text or not any(c.isdigit() for c in text):
            return 0

        # Remove commas
        text = text.replace(',', '')

        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000
        }

        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    num = float(text.replace(suffix, ''))
                    return int(num * multiplier)
                except ValueError:
                    return 0

        try:
            return int(float(text))
        except ValueError:
            return 0

    async def scrape_timeline(self, username: str, max_tweets: int = 100) -> List[Dict]:
        """
        Scrape tweets from a user's timeline on twitter.com.

        Args:
            username: Twitter username
            max_tweets: Maximum number of tweets to scrape

        Returns:
            List of tweet dictionaries
        """
        username = username.lstrip('@')
        profile_url = f"{self.base_url}/{username}"

        logger.info(f"Scraping Twitter timeline: {username} (max {max_tweets} tweets)")

        # Login if needed
        if self.twitter_username and not self.is_logged_in:
            await self.login()

        # Navigate to profile
        success = await self.navigate_to_url(profile_url)
        if not success:
            logger.error(f"Failed to navigate to profile: {username}")
            return []

        await self.random_delay()

        tweets = []
        try:
            # Scroll to load tweets
            for scroll in range(10):  # Scroll up to 10 times
                # Wait for tweets to load
                await asyncio.sleep(2)

                # Extract visible tweets
                tweet_articles = await self.page.query_selector_all('article[data-testid="tweet"]')

                logger.debug(f"Found {len(tweet_articles)} tweet elements on page")

                for article in tweet_articles:
                    if len(tweets) >= max_tweets:
                        break

                    try:
                        tweet_data = await self._extract_tweet_data(article, username)
                        if tweet_data and tweet_data['tweet_id'] not in [t.get('tweet_id') for t in tweets]:
                            tweets.append(tweet_data)
                    except Exception as e:
                        logger.debug(f"Error extracting tweet: {e}")
                        continue

                if len(tweets) >= max_tweets:
                    break

                # Scroll down
                await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)

            logger.info(f"Successfully scraped {len(tweets)} tweets from {username}")
            return tweets

        except Exception as e:
            logger.error(f"Error scraping timeline for {username}: {e}")
            return tweets

    async def _extract_tweet_data(self, article, username: str) -> Optional[Dict]:
        """Extract data from a single tweet article element."""
        try:
            # Extract tweet ID from link
            tweet_link = await article.query_selector('a[href*="/status/"]')
            if not tweet_link:
                return None

            href = await tweet_link.get_attribute('href')
            tweet_id_match = re.search(r'/status/(\d+)', href)
            if not tweet_id_match:
                return None

            tweet_id = tweet_id_match.group(1)

            # Extract text
            text_element = await article.query_selector('[data-testid="tweetText"]')
            text = await text_element.text_content() if text_element else ''

            # Extract engagement metrics
            likes_element = await article.query_selector('[data-testid="like"] span')
            likes_text = await likes_element.text_content() if likes_element else '0'
            likes_count = self._parse_number(likes_text)

            retweets_element = await article.query_selector('[data-testid="retweet"] span')
            retweets_text = await retweets_element.text_content() if retweets_element else '0'
            retweets_count = self._parse_number(retweets_text)

            replies_element = await article.query_selector('[data-testid="reply"] span')
            replies_text = await replies_element.text_content() if replies_element else '0'
            replies_count = self._parse_number(replies_text)

            # Extract timestamp
            time_element = await article.query_selector('time')
            posted_at = None
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    try:
                        posted_at = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except:
                        posted_at = datetime.utcnow()

            # Extract hashtags and mentions
            hashtags = re.findall(r'#(\w+)', text)
            mentions = re.findall(r'@(\w+)', text)

            # Extract media URLs
            media_elements = await article.query_selector_all('img[src*="pbs.twimg.com"]')
            media_urls = []
            for media in media_elements[:4]:  # Limit to 4 images
                src = await media.get_attribute('src')
                if src and 'profile' not in src:
                    media_urls.append(src)

            has_media = len(media_urls) > 0

            # Check if it's a retweet
            is_retweet = 'retweeted' in text.lower() or await article.query_selector('[data-testid="socialContext"]') is not None

            return {
                'tweet_id': tweet_id,
                'username': username,
                'text': text,
                'html_text': text,  # Twitter.com doesn't easily give HTML
                'posted_at': posted_at or datetime.utcnow(),
                'likes_count': likes_count,
                'retweets_count': retweets_count,
                'replies_count': replies_count,
                'quotes_count': 0,  # Hard to get from UI
                'is_retweet': is_retweet,
                'is_reply': False,  # Would need to check context
                'reply_to_username': None,
                'has_media': has_media,
                'media_urls': media_urls,
                'hashtags': hashtags,
                'mentions': mentions,
                'urls': [],  # Would need to extract from links
            }

        except Exception as e:
            logger.debug(f"Error extracting tweet data: {e}")
            return None
