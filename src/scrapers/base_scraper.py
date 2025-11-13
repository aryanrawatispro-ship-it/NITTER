"""
Base scraper class with common functionality for all scrapers.
"""

import asyncio
import random
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from fake_useragent import UserAgent
from loguru import logger

from src.nitter_manager import NitterInstanceManager
from src.utils.config import settings


class BaseScraper:
    """Base class for all Nitter scrapers."""

    def __init__(self, instance_manager: NitterInstanceManager):
        """
        Initialize the base scraper.

        Args:
            instance_manager: NitterInstanceManager instance for rotating instances
        """
        self.instance_manager = instance_manager
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.ua = UserAgent()
        self.current_instance = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser and create a new page."""
        playwright = await async_playwright().start()

        # Launch browser with anti-detection settings
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

        # Create context with random user agent
        context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080}
        )

        # Add anti-detection JavaScript
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = await context.new_page()
        logger.info("Browser started successfully")

    async def close(self):
        """Close the browser."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")

    async def random_delay(self):
        """Add a random delay between requests to avoid detection."""
        delay = random.uniform(settings.min_request_delay, settings.max_request_delay)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)

    async def get_instance_url(self) -> str:
        """Get a healthy Nitter instance URL."""
        instance = await self.instance_manager.get_instance()
        if not instance:
            raise Exception("No healthy Nitter instances available")

        self.current_instance = instance.url
        return instance.url

    async def navigate_to_url(self, url: str, max_retries: int = 3) -> bool:
        """
        Navigate to a URL with retry logic.

        Args:
            url: The URL to navigate to
            max_retries: Maximum number of retry attempts

        Returns:
            True if navigation succeeded, False otherwise
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Navigating to {url} (attempt {attempt + 1}/{max_retries})")

                await self.page.goto(url, wait_until='networkidle', timeout=settings.request_timeout * 1000)

                # Check if we got rate limited or blocked
                content = await self.page.content()
                if "rate limit" in content.lower() or "too many requests" in content.lower():
                    logger.warning(f"Rate limited on {self.current_instance}, trying different instance")
                    # Get a new instance and retry
                    new_url = url.replace(self.current_instance, await self.get_instance_url())
                    url = new_url
                    await self.random_delay()
                    continue

                return True

            except PlaywrightTimeout:
                logger.warning(f"Timeout navigating to {url}")
                if attempt < max_retries - 1:
                    await self.random_delay()
                    continue
                return False

            except Exception as e:
                logger.error(f"Error navigating to {url}: {e}")
                if attempt < max_retries - 1:
                    await self.random_delay()
                    continue
                return False

        return False

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        """
        Wait for a selector to appear on the page.

        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds

        Returns:
            True if selector found, False otherwise
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeout:
            logger.debug(f"Selector '{selector}' not found within {timeout}ms")
            return False
        except Exception as e:
            logger.error(f"Error waiting for selector '{selector}': {e}")
            return False

    async def extract_text(self, selector: str, default: str = "") -> str:
        """
        Extract text content from a selector.

        Args:
            selector: CSS selector
            default: Default value if selector not found

        Returns:
            Text content or default value
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                return (await element.text_content()).strip()
            return default
        except Exception as e:
            logger.debug(f"Error extracting text from '{selector}': {e}")
            return default

    async def extract_attribute(self, selector: str, attribute: str, default: str = "") -> str:
        """
        Extract an attribute value from a selector.

        Args:
            selector: CSS selector
            attribute: Attribute name
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return value if value else default
            return default
        except Exception as e:
            logger.debug(f"Error extracting attribute '{attribute}' from '{selector}': {e}")
            return default

    async def scroll_to_bottom(self, max_scrolls: int = 10, scroll_pause: float = 2.0):
        """
        Scroll to the bottom of the page to load more content.

        Args:
            max_scrolls: Maximum number of scroll attempts
            scroll_pause: Pause between scrolls in seconds
        """
        previous_height = await self.page.evaluate("document.body.scrollHeight")

        for i in range(max_scrolls):
            # Scroll down
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_pause)

            # Check if we've reached the bottom
            new_height = await self.page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                logger.debug(f"Reached bottom after {i + 1} scrolls")
                break

            previous_height = new_height
            logger.debug(f"Scrolled {i + 1}/{max_scrolls} times")
