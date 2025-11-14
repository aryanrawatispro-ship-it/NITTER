#!/usr/bin/env python3
"""
Simple Twitter Community Scraper - Direct to CSV
No database, no Docker needed - just scrape and save to CSV!

Usage:
    python3 simple_scrape.py <community_id> [output.csv]

Example:
    python3 simple_scrape.py 1977017211303690504 tweets.csv
"""

import asyncio
import sys
import csv
from datetime import datetime
import os

# You need to install: pip install httpx
import httpx


class SimpleCommunityScraper:
    """Simple scraper that saves directly to CSV - no database!"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def scrape_community(self, community_id: str) -> list:
        """Scrape ALL tweets from a community."""
        print(f"🔍 Scraping community {community_id}...")

        all_tweets = []
        pagination_token = None
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                print(f"📥 Fetching page {page}...")

                params = {
                    "max_results": 100,
                    "tweet.fields": "created_at,public_metrics,entities,author_id",
                    "expansions": "author_id"
                }

                if pagination_token:
                    params["pagination_token"] = pagination_token

                try:
                    response = await client.get(
                        f"{self.base_url}/communities/{community_id}/tweets",
                        headers=self.headers,
                        params=params,
                        timeout=30.0
                    )

                    if response.status_code != 200:
                        print(f"❌ Error: {response.status_code} - {response.text}")
                        break

                    data = response.json()

                    if not data.get('data'):
                        print("✅ No more tweets")
                        break

                    # Build user lookup
                    users = {}
                    if 'includes' in data and 'users' in data['includes']:
                        for user in data['includes']['users']:
                            users[user['id']] = user['username']

                    # Process tweets
                    for tweet in data['data']:
                        tweet_id = tweet['id']
                        author_id = tweet.get('author_id')
                        username = users.get(author_id, 'unknown')
                        text = tweet.get('text', '')
                        metrics = tweet.get('public_metrics', {})
                        created_at = tweet.get('created_at', '')

                        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

                        all_tweets.append({
                            'username': username,
                            'content': text,
                            'likes': metrics.get('like_count', 0),
                            'retweets': metrics.get('retweet_count', 0),
                            'comments': metrics.get('reply_count', 0),
                            'post_link': tweet_url,
                            'posted_at': created_at
                        })

                    print(f"   Found {len(data['data'])} tweets (total: {len(all_tweets)})")

                    # Check for next page
                    if 'meta' in data and 'next_token' in data['meta']:
                        pagination_token = data['meta']['next_token']
                        page += 1
                    else:
                        print("✅ Reached end of tweets")
                        break

                except Exception as e:
                    print(f"❌ Error: {e}")
                    break

        return all_tweets

    def save_to_csv(self, tweets: list, filename: str):
        """Save tweets to CSV file."""
        print(f"\n💾 Saving {len(tweets)} tweets to {filename}...")

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'username', 'content', 'likes', 'retweets',
                'comments', 'post_link', 'posted_at'
            ])

            writer.writeheader()
            writer.writerows(tweets)

        print(f"✅ Saved to {filename}")
        print(f"📊 Total tweets: {len(tweets)}")


async def main():
    # Get API key from environment or command line
    api_key = os.getenv('TWITTERAPIIO_API_KEY')

    if not api_key:
        print("❌ Error: TWITTERAPIIO_API_KEY not set")
        print("\nSet it with:")
        print("  export TWITTERAPIIO_API_KEY=your_key_here")
        print("\nOr get your API key from: https://twitterapi.io")
        sys.exit(1)

    # Get community ID from command line
    if len(sys.argv) < 2:
        print("Usage: python3 simple_scrape.py <community_id> [output.csv]")
        print("\nExample:")
        print("  python3 simple_scrape.py 1977017211303690504 tweets.csv")
        sys.exit(1)

    community_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"community_{community_id}.csv"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║   Twitter Community Scraper - Direct to CSV             ║
║   No database needed!                                    ║
╚══════════════════════════════════════════════════════════╝

Community ID: {community_id}
Output file:  {output_file}
API Key:      {api_key[:10]}...

""")

    # Scrape
    scraper = SimpleCommunityScraper(api_key)
    tweets = await scraper.scrape_community(community_id)

    if tweets:
        scraper.save_to_csv(tweets, output_file)
        print(f"\n🎉 Done! Open {output_file} to see your tweets.")
    else:
        print("\n❌ No tweets found. Check:")
        print("  - Community ID is correct")
        print("  - API key is valid")
        print("  - You have API quota remaining")


if __name__ == "__main__":
    asyncio.run(main())
