#!/usr/bin/env python3
"""
Example script to scrape ALL tweets from a Twitter community.

This script demonstrates how to scrape all tweets from a community and
export the data with the fields you requested:
- username
- content (text)
- likes
- retweets
- comments (replies)
- post link (tweet_url)
"""

import asyncio
import json
import csv
from src.scrapers import TwitterAPIioScraper, TwitterDirectScraper
from src.nitter_manager import NitterInstanceManager
from src.utils.config import settings


async def scrape_community_all_tweets(community_id: str, method: str = "api"):
    """
    Scrape ALL tweets from a community.

    Args:
        community_id: Twitter community ID
        method: 'api' for TwitterAPI.io or 'direct' for Twitter Direct

    Returns:
        List of tweet dictionaries
    """
    print(f"🚀 Scraping ALL tweets from community: {community_id}")
    print(f"   Method: {method}")
    print()

    if method == "api":
        # Method 1: TwitterAPI.io (faster, paid)
        if not settings.twitterapiio_api_key:
            print("❌ No TwitterAPI.io API key configured!")
            print("   Set TWITTERAPIIO_API_KEY in .env file")
            return []

        scraper = TwitterAPIioScraper(settings.twitterapiio_api_key)

        # Get community details first
        community = await scraper.get_community(community_id)
        if community:
            print(f"📊 Community: {community['name']}")
            print(f"   Members: {community['member_count']:,}")
            print()

        # Scrape ALL tweets (max_tweets=None)
        print("⏳ Scraping tweets (this may take a while)...")
        tweets = await scraper.scrape_community_tweets(community_id, max_tweets=None)

    else:
        # Method 2: Twitter Direct (free, slower)
        manager = NitterInstanceManager()

        # Load cookies
        from src.utils.twitter_auth import load_cookies_from_file
        cookies = load_cookies_from_file(settings.twitter_cookies_file) if settings.twitter_cookies_file else None

        if not cookies and not (settings.twitter_username and settings.twitter_password):
            print("❌ No authentication configured!")
            print("   Set either TWITTER_COOKIES_FILE or TWITTER_USERNAME/PASSWORD in .env")
            return []

        async with TwitterDirectScraper(manager, settings.twitter_username, settings.twitter_password, cookies) as scraper:
            # Get community details
            community = await scraper.get_community(community_id)
            if community:
                print(f"📊 Community: {community['name']}")
                print(f"   Members: {community['member_count']:,}")
                print()

            # Scrape ALL tweets (max_tweets=None)
            print("⏳ Scraping tweets (this may take a while)...")
            tweets = await scraper.scrape_community_tweets(community_id, max_tweets=None)

    print(f"✅ Scraped {len(tweets)} tweets!")
    print()
    return tweets


def export_to_csv(tweets: list, filename: str = "community_tweets.csv"):
    """
    Export tweets to CSV with requested fields.

    Fields exported:
    - username
    - content (text)
    - likes (likes_count)
    - retweets (retweets_count)
    - comments (replies_count)
    - post_link (tweet_url)
    """
    if not tweets:
        print("❌ No tweets to export!")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'username',
            'content',
            'likes',
            'retweets',
            'comments',
            'post_link'
        ])

        # Data
        for tweet in tweets:
            writer.writerow([
                tweet.get('username', ''),
                tweet.get('text', ''),
                tweet.get('likes_count', 0),
                tweet.get('retweets_count', 0),
                tweet.get('replies_count', 0),
                tweet.get('tweet_url', '')
            ])

    print(f"✅ Exported to {filename}")
    print()


def export_to_json(tweets: list, filename: str = "community_tweets.json"):
    """
    Export tweets to JSON with all fields.
    """
    if not tweets:
        print("❌ No tweets to export!")
        return

    # Extract only the fields you requested
    simplified_tweets = []
    for tweet in tweets:
        simplified_tweets.append({
            'username': tweet.get('username', ''),
            'content': tweet.get('text', ''),
            'likes': tweet.get('likes_count', 0),
            'retweets': tweet.get('retweets_count', 0),
            'comments': tweet.get('replies_count', 0),
            'post_link': tweet.get('tweet_url', ''),
            # Bonus fields (optional)
            'posted_at': tweet.get('posted_at').isoformat() if tweet.get('posted_at') else None,
            'hashtags': tweet.get('hashtags', []),
            'mentions': tweet.get('mentions', []),
        })

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(simplified_tweets, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported to {filename}")
    print()


async def main():
    """Main function."""
    print("="*60)
    print("  Twitter Community Scraper")
    print("="*60)
    print()

    # CONFIGURE THIS:
    community_id = "1234567890123456789"  # Replace with your community ID
    method = "api"  # "api" or "direct"

    print(f"🎯 Target Community ID: {community_id}")
    print()

    # Scrape ALL tweets
    tweets = await scrape_community_all_tweets(community_id, method)

    if not tweets:
        print("❌ No tweets scraped!")
        return

    # Export data
    print("📤 Exporting data...")
    print()
    export_to_csv(tweets)
    export_to_json(tweets)

    # Show sample
    print("📊 Sample data (first 3 tweets):")
    print()
    for i, tweet in enumerate(tweets[:3], 1):
        print(f"{i}. @{tweet['username']}")
        print(f"   Content: {tweet['text'][:80]}...")
        print(f"   Likes: {tweet['likes_count']}, Retweets: {tweet['retweets_count']}, Comments: {tweet['replies_count']}")
        print(f"   Link: {tweet['tweet_url']}")
        print()

    print("="*60)
    print("✅ DONE!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
