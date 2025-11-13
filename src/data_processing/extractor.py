"""
Data extraction utilities for tweets.
"""

import re
from typing import List, Dict
from loguru import logger


class DataExtractor:
    """Extract structured data from tweets."""

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """
        Extract all @mentions from text.

        Args:
            text: Tweet text

        Returns:
            List of mentioned usernames (without @)
        """
        mentions = re.findall(r'@(\w+)', text)
        return list(set(mentions))  # Remove duplicates

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """
        Extract all #hashtags from text.

        Args:
            text: Tweet text

        Returns:
            List of hashtags (without #)
        """
        hashtags = re.findall(r'#(\w+)', text)
        return list(set(hashtags))  # Remove duplicates

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        Extract all URLs from text.

        Args:
            text: Tweet text

        Returns:
            List of URLs
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates

    @staticmethod
    def extract_cashtags(text: str) -> List[str]:
        """
        Extract stock ticker symbols ($AAPL, $TSLA, etc.).

        Args:
            text: Tweet text

        Returns:
            List of cashtags (without $)
        """
        cashtags = re.findall(r'\$([A-Z]{1,5})\b', text)
        return list(set(cashtags))

    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """
        Extract email addresses from text.

        Args:
            text: Text to search

        Returns:
            List of email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers from text.

        Args:
            text: Text to search

        Returns:
            List of phone numbers
        """
        # Match common phone number patterns
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)
        return ['-'.join(phone) for phone in phones]

    @staticmethod
    def extract_all_metadata(text: str) -> Dict:
        """
        Extract all metadata from tweet text.

        Args:
            text: Tweet text

        Returns:
            Dictionary with all extracted metadata
        """
        return {
            'mentions': DataExtractor.extract_mentions(text),
            'hashtags': DataExtractor.extract_hashtags(text),
            'urls': DataExtractor.extract_urls(text),
            'cashtags': DataExtractor.extract_cashtags(text),
            'email_addresses': DataExtractor.extract_email_addresses(text),
            'phone_numbers': DataExtractor.extract_phone_numbers(text),
            'mention_count': len(DataExtractor.extract_mentions(text)),
            'hashtag_count': len(DataExtractor.extract_hashtags(text)),
            'url_count': len(DataExtractor.extract_urls(text)),
        }

    @staticmethod
    def detect_language_indicators(text: str) -> Dict[str, bool]:
        """
        Detect language indicators in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with language indicators
        """
        indicators = {
            'has_non_ascii': bool(re.search(r'[^\x00-\x7F]', text)),
            'has_cyrillic': bool(re.search(r'[а-яА-Я]', text)),
            'has_arabic': bool(re.search(r'[\u0600-\u06FF]', text)),
            'has_chinese': bool(re.search(r'[\u4e00-\u9fff]', text)),
            'has_japanese': bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text)),
            'has_korean': bool(re.search(r'[\uac00-\ud7af]', text)),
        }

        return indicators

    @staticmethod
    def count_words(text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to count

        Returns:
            Word count
        """
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    @staticmethod
    def count_characters(text: str) -> Dict[str, int]:
        """
        Count various character types in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with character counts
        """
        return {
            'total': len(text),
            'letters': sum(c.isalpha() for c in text),
            'digits': sum(c.isdigit() for c in text),
            'spaces': sum(c.isspace() for c in text),
            'special': sum(not c.isalnum() and not c.isspace() for c in text),
        }
