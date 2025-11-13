"""
Thread scraper for extracting full Twitter threads from Nitter.
"""

from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime
import re

from .base_scraper import BaseScraper


class ThreadScraper(BaseScraper):
    """Scraper for tweet threads."""

    async def scrape_thread(self, tweet_url: str) -> List[Dict]:
        """
        Scrape a full thread starting from a tweet URL.

        Args:
            tweet_url: Full tweet URL (Twitter or Nitter URL)

        Returns:
            List of tweet dictionaries in thread order
        """
        # Convert Twitter URL to Nitter URL if needed
        nitter_url = await self._convert_to_nitter_url(tweet_url)

        logger.info(f"Scraping thread: {nitter_url}")

        success = await self.navigate_to_url(nitter_url)
        if not success:
            logger.error(f"Failed to navigate to thread: {nitter_url}")
            return []

        # Wait for main tweet to load
        if not await self.wait_for_selector('.main-tweet', timeout=10000):
            logger.error(f"Main tweet not found: {nitter_url}")
            return []

        await self.random_delay()

        # Extract all tweets in the thread
        tweets = await self._extract_thread_tweets()

        logger.info(f"Successfully scraped thread with {len(tweets)} tweets")
        return tweets

    async def _convert_to_nitter_url(self, url: str) -> str:
        """Convert Twitter URL to Nitter URL."""

        instance_url = await self.get_instance_url()

        # If already a Nitter URL, just return it
        if 'nitter' in url:
            return url

        # Convert twitter.com or x.com URL to Nitter
        if 'twitter.com' in url or 'x.com' in url:
            # Extract username and tweet ID
            parts = url.split('/')
            if 'status' in parts:
                status_idx = parts.index('status')
                if status_idx > 0 and status_idx + 1 < len(parts):
                    username = parts[status_idx - 1]
                    tweet_id = parts[status_idx + 1].split('?')[0]
                    return f"{instance_url}/{username}/status/{tweet_id}"

        return url

    async def _extract_thread_tweets(self) -> List[Dict]:
        """Extract all tweets in the thread."""

        tweets = []

        # Extract main tweet
        main_tweet_element = await self.page.query_selector('.main-tweet')
        if main_tweet_element:
            main_tweet = await self._extract_tweet_data(main_tweet_element, is_main=True)
            if main_tweet:
                tweets.append(main_tweet)

        # Extract tweets before (parent tweets in thread)
        before_elements = await self.page.query_selector_all('.thread-line .timeline-item')
        for element in before_elements:
            try:
                tweet = await self._extract_tweet_data(element)
                if tweet:
                    tweets.insert(0, tweet)  # Add to beginning
            except Exception as e:
                logger.debug(f"Error extracting parent tweet: {e}")

        # Extract replies after
        after_elements = await self.page.query_selector_all('.replies .timeline-item')
        for element in after_elements:
            try:
                tweet = await self._extract_tweet_data(element)
                if tweet:
                    # Only add if it's from the same user (part of thread)
                    if tweets and tweet['username'] == tweets[0]['username']:
                        tweets.append(tweet)
            except Exception as e:
                logger.debug(f"Error extracting reply tweet: {e}")

        return tweets

    async def _extract_tweet_data(self, element, is_main: bool = False) -> Optional[Dict]:
        """Extract data from a single tweet element."""

        try:
            # Extract username
            username_element = await element.query_selector('.username')
            username = ''
            if username_element:
                username_text = await username_element.text_content()
                username = username_text.strip().lstrip('@')

            # Extract tweet ID
            tweet_link = await element.query_selector('.tweet-link')
            if not tweet_link:
                return None

            tweet_url = await tweet_link.get_attribute('href')
            tweet_id = tweet_url.split('/')[-1].split('#')[0] if tweet_url else None

            if not tweet_id:
                return None

            # Extract display name
            fullname_element = await element.query_selector('.fullname')
            display_name = ''
            if fullname_element:
                display_name = (await fullname_element.text_content()).strip()

            # Extract tweet text
            tweet_content = await element.query_selector('.tweet-content')
            text = ''
            html_text = ''
            if tweet_content:
                text = (await tweet_content.text_content()).strip()
                html_text = await tweet_content.inner_html()

            # Extract posted time
            time_element = await element.query_selector('.tweet-date a')
            posted_at = None
            if time_element:
                time_title = await time_element.get_attribute('title')
                if time_title:
                    try:
                        posted_at = datetime.strptime(time_title.split('·')[0].strip(), '%b %d, %Y')
                    except:
                        pass

            # Extract stats
            stats = await self._extract_tweet_stats(element)

            # Check tweet type
            is_retweet = await element.query_selector('.retweet-header') is not None
            is_reply = await element.query_selector('.replying-to') is not None

            # Extract reply-to info
            reply_to_username = None
            if is_reply:
                reply_element = await element.query_selector('.replying-to a')
                if reply_element:
                    reply_to_url = await reply_element.get_attribute('href')
                    if reply_to_url:
                        reply_to_username = reply_to_url.strip('/').split('/')[-1]

            # Extract media
            media_data = await self._extract_media(element)

            # Extract mentions, hashtags, and URLs
            mentions = self._extract_mentions(text)
            hashtags = self._extract_hashtags(text)
            urls = self._extract_urls(html_text)

            return {
                'tweet_id': tweet_id,
                'username': username,
                'display_name': display_name,
                'text': text,
                'html_text': html_text,
                'posted_at': posted_at,
                'likes_count': stats['likes'],
                'retweets_count': stats['retweets'],
                'replies_count': stats['replies'],
                'quotes_count': stats['quotes'],
                'is_retweet': is_retweet,
                'is_reply': is_reply,
                'is_main_tweet': is_main,
                'reply_to_username': reply_to_username,
                'has_media': media_data['has_media'],
                'media_urls': media_data['media_urls'],
                'mentions': mentions,
                'hashtags': hashtags,
                'urls': urls,
            }

        except Exception as e:
            logger.debug(f"Error extracting tweet data: {e}")
            return None

    async def _extract_tweet_stats(self, element) -> Dict[str, int]:
        """Extract tweet engagement stats."""

        stats = {
            'likes': 0,
            'retweets': 0,
            'replies': 0,
            'quotes': 0
        }

        try:
            comments = await element.query_selector('.icon-comment + .tweet-stat')
            if comments:
                stats['replies'] = self._parse_count(await comments.text_content())

            retweets = await element.query_selector('.icon-retweet + .tweet-stat')
            if retweets:
                stats['retweets'] = self._parse_count(await retweets.text_content())

            quotes = await element.query_selector('.icon-quote + .tweet-stat')
            if quotes:
                stats['quotes'] = self._parse_count(await quotes.text_content())

            likes = await element.query_selector('.icon-heart + .tweet-stat')
            if likes:
                stats['likes'] = self._parse_count(await likes.text_content())

        except Exception as e:
            logger.debug(f"Error extracting tweet stats: {e}")

        return stats

    async def _extract_media(self, element) -> Dict:
        """Extract media URLs."""

        media_data = {
            'has_media': False,
            'media_urls': []
        }

        try:
            images = await element.query_selector_all('.attachment.image img')
            for img in images:
                img_url = await img.get_attribute('src')
                if img_url and not img_url.startswith('http'):
                    img_url = self.current_instance + img_url
                if img_url:
                    media_data['media_urls'].append(img_url)

            videos = await element.query_selector_all('.attachment.video')
            for video in videos:
                video_link = await video.query_selector('a')
                if video_link:
                    video_url = await video_link.get_attribute('href')
                    if video_url and not video_url.startswith('http'):
                        video_url = self.current_instance + video_url
                    if video_url:
                        media_data['media_urls'].append(video_url)

            media_data['has_media'] = len(media_data['media_urls']) > 0

        except Exception as e:
            logger.debug(f"Error extracting media: {e}")

        return media_data

    def _parse_count(self, text: str) -> int:
        """Parse count values."""
        text = text.strip().replace(',', '')

        if not text:
            return 0

        multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}

        for suffix, multiplier in multipliers.items():
            if suffix in text.upper():
                try:
                    num = float(text.upper().replace(suffix, ''))
                    return int(num * multiplier)
                except ValueError:
                    return 0

        try:
            return int(float(text))
        except ValueError:
            return 0

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions."""
        return re.findall(r'@(\w+)', text)

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract #hashtags."""
        return re.findall(r'#(\w+)', text)

    def _extract_urls(self, html: str) -> List[str]:
        """Extract URLs."""
        urls = re.findall(r'href="([^"]+)"', html)
        return [url for url in urls if not url.startswith('/') and 'nitter' not in url]
