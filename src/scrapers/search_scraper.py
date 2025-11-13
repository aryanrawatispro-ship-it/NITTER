"""
Search scraper for finding tweets by keyword or hashtag on Nitter.
"""

from typing import List, Dict, Optional
from urllib.parse import quote
from loguru import logger
from datetime import datetime
import re

from .base_scraper import BaseScraper


class SearchScraper(BaseScraper):
    """Scraper for search results."""

    async def scrape_search(
        self,
        query: str,
        max_tweets: int = 100,
        search_type: str = "keyword"
    ) -> List[Dict]:
        """
        Search for tweets by keyword or hashtag.

        Args:
            query: Search query (keyword or hashtag)
            max_tweets: Maximum number of tweets to scrape
            search_type: Type of search ("keyword" or "hashtag")

        Returns:
            List of tweet dictionaries
        """
        # Format query based on type
        if search_type == "hashtag" and not query.startswith('#'):
            query = f"#{query}"

        instance_url = await self.get_instance_url()
        encoded_query = quote(query)
        search_url = f"{instance_url}/search?f=tweets&q={encoded_query}"

        logger.info(f"Searching for: {query} (type: {search_type}, max {max_tweets} tweets)")

        success = await self.navigate_to_url(search_url)
        if not success:
            logger.error(f"Failed to navigate to search: {query}")
            return []

        # Wait for results to load
        if not await self.wait_for_selector('.timeline-item', timeout=10000):
            logger.warning(f"No results found for: {query}")
            return []

        await self.random_delay()

        # Scroll to load more results
        await self.scroll_to_bottom(max_scrolls=10, scroll_pause=2.0)

        # Extract tweets
        tweets = await self._extract_search_results(query, max_tweets)

        logger.info(f"Successfully scraped {len(tweets)} tweets for query: {query}")
        return tweets

    async def _extract_search_results(self, query: str, max_tweets: int) -> List[Dict]:
        """Extract tweet data from search results."""

        tweets = []
        tweet_elements = await self.page.query_selector_all('.timeline-item')

        for element in tweet_elements[:max_tweets]:
            try:
                tweet_data = await self._extract_tweet_data(element)
                if tweet_data:
                    tweet_data['search_query'] = query
                    tweets.append(tweet_data)
            except Exception as e:
                logger.debug(f"Error extracting search result: {e}")
                continue

        return tweets

    async def _extract_tweet_data(self, element) -> Optional[Dict]:
        """Extract data from a single tweet element in search results."""

        try:
            # Extract username
            username_element = await element.query_selector('.username')
            username = ''
            if username_element:
                username_text = await username_element.text_content()
                username = username_text.strip().lstrip('@')

            # Extract tweet ID from the link
            tweet_link = await element.query_selector('.tweet-link')
            if not tweet_link:
                return None

            tweet_url = await tweet_link.get_attribute('href')
            tweet_id = tweet_url.split('/')[-1].split('#')[0] if tweet_url else None

            if not tweet_id or not username:
                return None

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
                'text': text,
                'html_text': html_text,
                'posted_at': posted_at,
                'likes_count': stats['likes'],
                'retweets_count': stats['retweets'],
                'replies_count': stats['replies'],
                'quotes_count': stats['quotes'],
                'is_retweet': is_retweet,
                'is_reply': is_reply,
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
        """Extract likes, retweets, replies counts."""

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
        """Extract media URLs from a tweet."""

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
        """Extract @mentions from text."""
        return re.findall(r'@(\w+)', text)

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract #hashtags from text."""
        return re.findall(r'#(\w+)', text)

    def _extract_urls(self, html: str) -> List[str]:
        """Extract URLs from HTML."""
        urls = re.findall(r'href="([^"]+)"', html)
        return [url for url in urls if not url.startswith('/') and 'nitter' not in url]
