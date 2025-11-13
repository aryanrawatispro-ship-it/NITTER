"""
Profile scraper for extracting Twitter user profile data from Nitter.
"""

from typing import Optional, Dict
from loguru import logger
from datetime import datetime

from .base_scraper import BaseScraper


class ProfileScraper(BaseScraper):
    """Scraper for Twitter user profiles."""

    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape a Twitter user's profile.

        Args:
            username: Twitter username (without @)

        Returns:
            Dictionary containing profile data or None if failed
        """
        username = username.lstrip('@')
        instance_url = await self.get_instance_url()
        profile_url = f"{instance_url}/{username}"

        logger.info(f"Scraping profile: {username}")

        success = await self.navigate_to_url(profile_url)
        if not success:
            logger.error(f"Failed to navigate to profile: {username}")
            return None

        # Check if profile exists
        if await self.wait_for_selector('.error-panel', timeout=3000):
            logger.warning(f"Profile not found or suspended: {username}")
            return None

        # Wait for profile to load
        if not await self.wait_for_selector('.profile-card', timeout=10000):
            logger.error(f"Profile card not found for: {username}")
            return None

        await self.random_delay()

        try:
            profile_data = await self._extract_profile_data(username)
            logger.info(f"Successfully scraped profile: {username}")
            return profile_data

        except Exception as e:
            logger.error(f"Error extracting profile data for {username}: {e}")
            return None

    async def _extract_profile_data(self, username: str) -> Dict:
        """Extract profile data from the page."""

        # Extract display name
        display_name = await self.extract_text('.profile-card-fullname', username)

        # Extract bio
        bio = await self.extract_text('.profile-bio', '')

        # Extract location
        location = await self.extract_text('.profile-location', '')

        # Extract website
        website = await self.extract_attribute('.profile-website a', 'href', '')

        # Extract profile image
        profile_image = await self.extract_attribute('.profile-card-avatar', 'src', '')
        if profile_image and not profile_image.startswith('http'):
            profile_image = self.current_instance + profile_image

        # Extract banner image
        banner_image = await self.extract_attribute('.profile-banner img', 'src', '')
        if banner_image and not banner_image.startswith('http'):
            banner_image = self.current_instance + banner_image

        # Extract stats
        stats = await self._extract_stats()

        # Check verification status
        is_verified = await self.page.query_selector('.profile-card-fullname .icon-verified') is not None

        # Check if protected
        is_protected = await self.page.query_selector('.timeline-protected') is not None

        # Extract join date if available
        joined_date = None
        join_date_text = await self.extract_text('.profile-joindate', '')
        if join_date_text:
            try:
                # Parse join date (format: "Joined February 2009")
                join_date_text = join_date_text.replace('Joined ', '')
                joined_date = datetime.strptime(join_date_text, '%B %Y')
            except:
                pass

        return {
            'username': username,
            'display_name': display_name,
            'bio': bio,
            'location': location,
            'website': website,
            'profile_image_url': profile_image,
            'banner_image_url': banner_image,
            'followers_count': stats['followers'],
            'following_count': stats['following'],
            'tweets_count': stats['tweets'],
            'is_verified': is_verified,
            'is_protected': is_protected,
            'joined_date': joined_date,
        }

    async def _extract_stats(self) -> Dict[str, int]:
        """Extract follower/following/tweet counts."""

        stats = {
            'followers': 0,
            'following': 0,
            'tweets': 0
        }

        try:
            # Get all stat elements
            stat_elements = await self.page.query_selector_all('.profile-stat-num')

            for element in stat_elements:
                value_text = await element.text_content()
                value = self._parse_stat_value(value_text.strip())

                # Determine which stat this is based on the label
                parent = await element.evaluate_handle('el => el.parentElement')
                parent_text = await parent.text_content()

                if 'Tweets' in parent_text or 'Posts' in parent_text:
                    stats['tweets'] = value
                elif 'Following' in parent_text:
                    stats['following'] = value
                elif 'Followers' in parent_text:
                    stats['followers'] = value

        except Exception as e:
            logger.warning(f"Error extracting stats: {e}")

        return stats

    def _parse_stat_value(self, value: str) -> int:
        """
        Parse stat values that might contain K, M, B suffixes.

        Args:
            value: String like "1.2K", "3.5M", "123"

        Returns:
            Integer value
        """
        value = value.replace(',', '').strip()

        if not value:
            return 0

        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000
        }

        for suffix, multiplier in multipliers.items():
            if suffix in value.upper():
                try:
                    num = float(value.upper().replace(suffix, ''))
                    return int(num * multiplier)
                except ValueError:
                    return 0

        try:
            return int(float(value))
        except ValueError:
            return 0
