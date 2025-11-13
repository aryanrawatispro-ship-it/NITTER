"""
Text cleaning and normalization utilities.
"""

import re
from loguru import logger


class TextCleaner:
    """Clean and normalize tweet text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean tweet text by removing unnecessary whitespace and normalizing.

        Args:
            text: Raw tweet text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Normalize unicode characters
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        return text

    @staticmethod
    def remove_urls(text: str) -> str:
        """
        Remove URLs from text.

        Args:
            text: Text containing URLs

        Returns:
            Text with URLs removed
        """
        # Remove http/https URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove remaining URL-like patterns
        text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def remove_mentions(text: str) -> str:
        """
        Remove @mentions from text.

        Args:
            text: Text containing mentions

        Returns:
            Text with mentions removed
        """
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def remove_hashtags(text: str) -> str:
        """
        Remove #hashtags from text.

        Args:
            text: Text containing hashtags

        Returns:
            Text with hashtags removed
        """
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def remove_emojis(text: str) -> str:
        """
        Remove emojis from text.

        Args:
            text: Text containing emojis

        Returns:
            Text with emojis removed
        """
        # Remove emojis using regex pattern
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def normalize_text(text: str, remove_urls: bool = True, remove_mentions: bool = False,
                      remove_hashtags: bool = False, remove_emojis: bool = False) -> str:
        """
        Fully normalize text with configurable options.

        Args:
            text: Raw text
            remove_urls: Whether to remove URLs
            remove_mentions: Whether to remove @mentions
            remove_hashtags: Whether to remove #hashtags
            remove_emojis: Whether to remove emojis

        Returns:
            Normalized text
        """
        text = TextCleaner.clean_text(text)

        if remove_urls:
            text = TextCleaner.remove_urls(text)

        if remove_mentions:
            text = TextCleaner.remove_mentions(text)

        if remove_hashtags:
            text = TextCleaner.remove_hashtags(text)

        if remove_emojis:
            text = TextCleaner.remove_emojis(text)

        return text

    @staticmethod
    def extract_clean_words(text: str) -> list:
        """
        Extract clean words from text (for word frequency analysis).

        Args:
            text: Text to process

        Returns:
            List of clean words
        """
        # Normalize text
        text = TextCleaner.normalize_text(
            text,
            remove_urls=True,
            remove_mentions=True,
            remove_hashtags=True,
            remove_emojis=True
        )

        # Convert to lowercase
        text = text.lower()

        # Extract words (alphanumeric only)
        words = re.findall(r'\b[a-z]+\b', text)

        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                     'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                     'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}

        words = [word for word in words if len(word) > 2 and word not in stop_words]

        return words
