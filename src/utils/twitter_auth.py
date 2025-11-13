"""
Utility functions for Twitter authentication.
"""

import json
import os
from typing import List, Dict, Optional
from loguru import logger


def load_cookies_from_file(file_path: str) -> Optional[List[Dict]]:
    """
    Load Twitter cookies from a JSON file.

    Args:
        file_path: Path to the cookies JSON file

    Returns:
        List of cookie dictionaries, or None if failed
    """
    if not file_path or not os.path.exists(file_path):
        logger.debug(f"Cookie file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r') as f:
            cookies = json.load(f)

        # Validate cookie format
        if not isinstance(cookies, list):
            logger.error("Cookies file must contain a JSON array")
            return None

        # Check if cookies have required fields
        required_fields = ['name', 'value', 'domain']
        for cookie in cookies:
            if not all(field in cookie for field in required_fields):
                logger.warning(f"Cookie missing required fields: {cookie}")

        logger.info(f"Loaded {len(cookies)} cookies from {file_path}")
        return cookies

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cookies file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading cookies from {file_path}: {e}")
        return None


def validate_cookies(cookies: List[Dict]) -> bool:
    """
    Validate that cookies have the required format for Playwright.

    Args:
        cookies: List of cookie dictionaries

    Returns:
        True if cookies are valid, False otherwise
    """
    if not cookies or not isinstance(cookies, list):
        return False

    required_fields = ['name', 'value', 'domain']

    for cookie in cookies:
        if not isinstance(cookie, dict):
            logger.error(f"Cookie must be a dictionary, got {type(cookie)}")
            return False

        if not all(field in cookie for field in required_fields):
            logger.error(f"Cookie missing required fields. Has: {cookie.keys()}, needs: {required_fields}")
            return False

        # Ensure domain is for Twitter
        if 'twitter.com' not in cookie.get('domain', '') and 'x.com' not in cookie.get('domain', ''):
            logger.warning(f"Cookie domain doesn't appear to be Twitter: {cookie.get('domain')}")

    return True


def get_auth_method(username: str = None, password: str = None, cookies_file: str = None) -> str:
    """
    Determine which authentication method to use.

    Args:
        username: Twitter username
        password: Twitter password
        cookies_file: Path to cookies file

    Returns:
        'cookies', 'password', or 'none'
    """
    # Prefer cookies
    if cookies_file and os.path.exists(cookies_file):
        return 'cookies'

    # Fallback to password
    if username and password:
        return 'password'

    return 'none'
