# Twitter Community Scraping Guide

## What are Twitter Communities?

Twitter Communities are groups on Twitter where people with shared interests can connect and discuss specific topics. Unlike regular tweets that go to all your followers, community tweets are only visible to community members.

### Why Scrape Communities?

✅ **Targeted Content** - Get tweets from specific interest groups
✅ **Quality Discussions** - Communities often have more focused, high-quality conversations
✅ **Market Research** - Understand sentiment in specific niches
✅ **Trend Analysis** - Track topics within particular communities
✅ **Content Curation** - Collect relevant content from your target audience

---

## Features

This scraper supports **full community scraping** with two methods:

### 1. TwitterAPI.io (Recommended)
- ⚡ **Fast**: API calls return instantly
- ✅ **Reliable**: Professional API infrastructure
- 📊 **Complete Data**: Gets community details + tweets
- 💰 **Affordable**: Same pricing as regular scraping

### 2. Twitter Direct (Free Alternative)
- 🆓 **Free**: No API costs
- 🔒 **Cookie-based Auth**: Uses your Twitter cookies
- ⚠️ **Requires Auth**: Must be a community member to scrape
- 🐌 **Slower**: Browser-based scraping

---

## Requirements

### To Scrape a Community, You Need:

1. **Community ID** - Find this in the community URL
2. **Authentication** - Either:
   - TwitterAPI.io API key, OR
   - Twitter cookies/credentials (see [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md))
3. **Community Membership** (for Twitter Direct method)
   - You must join the community on Twitter first
   - TwitterAPI.io can access public communities without membership

---

## How to Find Community IDs

### Method 1: From Community URL

When you visit a community, the URL looks like:
```
https://twitter.com/i/communities/1234567890123456789
                                   ^^^^^^^^^^^^^^^^^^^
                                   This is the Community ID
```

### Method 2: Using Browser DevTools

1. Go to the community page on Twitter
2. Open DevTools (F12)
3. Go to Network tab
4. Look for requests containing "communities"
5. Find the community ID in the URL

### Method 3: From API Response

If you're already scraping a user's communities:
```python
# This will list communities a user is in (if API supports it)
user_communities = await scraper.get_user_communities(username)
```

---

## Quick Start

### Option 1: Using TwitterAPI.io (Easiest)

```bash
# 1. Configure .env
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_api_key_here

# 2. Restart containers
docker compose restart api

# 3. Scrape a community
curl -X POST http://localhost:8000/api/communities/1234567890123456789/scrape
```

### Option 2: Using Twitter Direct (Free)

```bash
# 1. Get your Twitter cookies (see HOW_TO_GET_COOKIES.md)
# 2. Configure .env
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json

# 3. Make sure you're a member of the community on Twitter!

# 4. Restart containers
docker compose restart api

# 5. Scrape a community
curl -X POST http://localhost:8000/api/communities/1234567890123456789/scrape
```

---

## API Usage

### Scrape Community Tweets

**Endpoint:** `POST /api/communities/{community_id}/scrape`

**Parameters:**
- `max_tweets` (optional): Maximum tweets to scrape (default: 100)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/communities/1234567890123456789/scrape?max_tweets=200"
```

**Response:**
```json
{
  "status": "success",
  "message": "Community scraping job started",
  "job_id": "abc-123-def",
  "community_id": "1234567890123456789"
}
```

### Get Community Details

**Endpoint:** `GET /api/communities/{community_id}`

**Example:**
```bash
curl http://localhost:8000/api/communities/1234567890123456789
```

**Response:**
```json
{
  "community_id": "1234567890123456789",
  "name": "Web Development",
  "description": "A community for web developers",
  "member_count": 15000,
  "url": "https://twitter.com/i/communities/1234567890123456789",
  "last_scraped": "2025-01-15T10:30:00Z"
}
```

### Track a Community

**Endpoint:** `POST /api/communities/{community_id}/track`

**Body:**
```json
{
  "interval": 3600
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/communities/1234567890123456789/track \
  -H "Content-Type: application/json" \
  -d '{"interval": 3600}'
```

This will scrape the community every hour (3600 seconds).

### Get Community Tweets

**Endpoint:** `GET /api/communities/{community_id}/tweets`

**Parameters:**
- `limit` (optional): Number of tweets to return (default: 100)
- `offset` (optional): Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/communities/1234567890123456789/tweets?limit=50"
```

**Response:**
```json
{
  "tweets": [
    {
      "tweet_id": "123456789",
      "username": "johndoe",
      "text": "Great discussion in this community!",
      "likes_count": 42,
      "retweets_count": 10,
      "posted_at": "2025-01-15T10:00:00Z",
      "community_id": "1234567890123456789"
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

---

## Python Usage

### Using the Scraper Directly

```python
import asyncio
from src.scrapers import TwitterAPIioScraper, TwitterDirectScraper
from src.nitter_manager import NitterInstanceManager
import json

async def scrape_community_example():
    community_id = "1234567890123456789"

    # Option 1: Using TwitterAPI.io
    scraper = TwitterAPIioScraper(api_key="your_api_key")

    # Get community details
    community = await scraper.get_community(community_id)
    print(f"Community: {community['name']}")
    print(f"Members: {community['member_count']}")

    # Scrape tweets
    tweets = await scraper.scrape_community_tweets(community_id, max_tweets=100)
    print(f"Scraped {len(tweets)} tweets")

    for tweet in tweets[:5]:
        print(f"- @{tweet['username']}: {tweet['text'][:100]}")


    # Option 2: Using Twitter Direct (with cookies)
    with open('twitter_cookies.json', 'r') as f:
        cookies = json.load(f)

    manager = NitterInstanceManager()
    async with TwitterDirectScraper(manager, cookies=cookies) as scraper:
        # Get community details
        community = await scraper.get_community(community_id)
        print(f"Community: {community['name']}")

        # Scrape tweets
        tweets = await scraper.scrape_community_tweets(community_id, max_tweets=100)
        print(f"Scraped {len(tweets)} tweets")

asyncio.run(scrape_community_example())
```

### Using the Task Scheduler

```python
from src.scheduler.tasks import scrape_community_tweets

# Trigger a one-time scrape
job = scrape_community_tweets.delay("1234567890123456789", max_tweets=200)

# Check job status
print(f"Job ID: {job.id}")
```

---

## Database Schema

### TwitterCommunity Model

```python
class TwitterCommunity(Base):
    id = Integer  # Primary key
    community_id = String  # Twitter community ID (unique)
    name = String  # Community name
    description = Text  # Community description
    member_count = Integer  # Number of members
    admin_count = Integer  # Number of admins
    moderator_count = Integer  # Number of moderators
    url = String  # Community URL
    rules = JSON  # List of community rules

    # Tracking
    is_tracked = Boolean  # Whether to auto-scrape
    check_interval = Integer  # Scraping interval (seconds)
    last_scraped = DateTime  # Last scrape time

    # Metadata
    created_at = DateTime
    updated_at = DateTime
```

### Tweet Model (Enhanced)

All tweets now include a `community_id` field:

```python
class Tweet(Base):
    # ... existing fields ...
    community_id = String  # NEW: Community ID if tweet is from a community
```

You can query community tweets:

```sql
SELECT * FROM tweets WHERE community_id = '1234567890123456789';
```

---

## Tracking Communities

### Enable Automatic Tracking

```python
from src.utils.database import get_db_context
from src.utils.models import TwitterCommunity

with get_db_context() as db:
    # Add community to database
    community = TwitterCommunity(
        community_id="1234567890123456789",
        name="Web Development",
        description="A community for web developers",
        is_tracked=True,
        check_interval=3600  # Scrape every hour
    )
    db.add(community)
    db.commit()
```

The `check_tracked_communities` periodic task will automatically scrape it.

### Configure Celery Beat Schedule

In your `celeryconfig.py` or `celery_app.py`, add:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'check-tracked-communities': {
        'task': 'src.scheduler.tasks.check_tracked_communities',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

---

## Use Cases

### 1. Market Research

Track competitor communities:

```bash
# Track startup community
curl -X POST http://localhost:8000/api/communities/startup_community_id/track

# Get tweets from last 24 hours
curl "http://localhost:8000/api/communities/startup_community_id/tweets?since=24h"
```

### 2. Trend Analysis

Monitor trending topics in a community:

```python
from src.utils.database import get_db_context
from src.utils.models import Tweet
from collections import Counter

with get_db_context() as db:
    tweets = db.query(Tweet).filter_by(
        community_id="1234567890123456789"
    ).all()

    # Get top hashtags
    all_hashtags = []
    for tweet in tweets:
        all_hashtags.extend(tweet.hashtags or [])

    top_hashtags = Counter(all_hashtags).most_common(10)
    print("Top 10 hashtags:", top_hashtags)
```

### 3. Content Curation

Find high-engagement tweets:

```python
with get_db_context() as db:
    top_tweets = db.query(Tweet).filter_by(
        community_id="1234567890123456789"
    ).order_by(
        Tweet.engagement_rate.desc()
    ).limit(20).all()

    for tweet in top_tweets:
        print(f"@{tweet.user.username}: {tweet.text}")
        print(f"Engagement: {tweet.engagement_rate:.2%}")
        print()
```

### 4. Sentiment Analysis

Track community sentiment over time:

```python
from datetime import datetime, timedelta

with get_db_context() as db:
    # Last 7 days
    since = datetime.utcnow() - timedelta(days=7)

    tweets = db.query(Tweet).filter(
        Tweet.community_id == "1234567890123456789",
        Tweet.posted_at >= since
    ).all()

    sentiments = [t.sentiment for t in tweets]
    positive_pct = sentiments.count('positive') / len(sentiments) * 100

    print(f"Community sentiment: {positive_pct:.1f}% positive")
```

---

## Troubleshooting

### "Community not found" Error

**Problem:** API returns 404 or community doesn't exist

**Solutions:**
1. Verify the community ID is correct
2. Check if the community is public or private
3. For Twitter Direct: Make sure you're a member of the community

### "Authentication required" Error

**Problem:** Community scraping requires authentication

**Solutions:**
1. Check that `USE_TWITTER_DIRECT=true` and cookies are loaded
2. Verify your cookies are still valid (they expire after ~30 days)
3. For TwitterAPI.io, check your API key is correct

### "No tweets found" Error

**Problem:** Scraper completes but finds 0 tweets

**Possible reasons:**
1. Community has no recent tweets
2. You're not a member (Twitter Direct only)
3. Community is private
4. Rate limit hit (try again later)

**Debug:**
```bash
# Check logs
docker compose logs api | grep -i community

# Verify community exists
curl http://localhost:8000/api/communities/COMMUNITY_ID
```

### "Rate limit exceeded"

**Problem:** Hit API rate limits

**Solutions:**
1. Reduce scraping frequency (increase `check_interval`)
2. Upgrade your TwitterAPI.io plan
3. Use Twitter Direct as fallback (free, no rate limits)

---

## Best Practices

### 1. Start Small

Test with one community first:

```bash
# Scrape once to test
curl -X POST http://localhost:8000/api/communities/COMMUNITY_ID/scrape

# Check results
curl http://localhost:8000/api/jobs/recent?limit=1
```

### 2. Respect Rate Limits

- **TwitterAPI.io**: Track your usage at https://twitterapi.io/dashboard
- **Twitter Direct**: Add delays between scrapes (already built-in)

### 3. Join Communities First

For Twitter Direct scraping:
- Join the community on Twitter before scraping
- Some communities are private and require approval

### 4. Monitor Costs

If using TwitterAPI.io:
- Community scraping uses same API credits as user scraping
- 100 tweets ≈ 1-2 API requests
- Set budget alerts in your TwitterAPI.io dashboard

### 5. Clean Old Data

Community tweets can accumulate quickly:

```sql
-- Delete community tweets older than 90 days
DELETE FROM tweets
WHERE community_id IS NOT NULL
AND posted_at < NOW() - INTERVAL '90 days';
```

---

## Limitations

### TwitterAPI.io
- May not support all communities (check API docs)
- Requires API key (free tier: 500 requests/month)
- Rate limits apply

### Twitter Direct
- **Must be a community member** to scrape
- Slower than API (browser automation)
- Requires valid cookies (expire after ~30 days)
- Private communities only accessible if you're approved

### General
- Cannot scrape private communities without membership
- Historical data limited to what's currently visible
- Deleted tweets won't be captured

---

## FAQ

### Q: How do I find communities to scrape?

A: Browse Twitter's communities section, or search for communities related to your interests. Note the community ID from the URL.

### Q: Can I scrape private communities?

A: Yes, but you must be a member. TwitterAPI.io may not support private communities - use Twitter Direct instead.

### Q: How often should I scrape?

A: Depends on community activity:
- High-activity: Every 15-30 minutes
- Medium-activity: Every 1-2 hours
- Low-activity: Every 6-24 hours

### Q: Do I need to join every community I want to scrape?

A:
- **TwitterAPI.io**: No, can access public communities
- **Twitter Direct**: Yes, must be a member

### Q: Can I scrape all communities at once?

A: Not recommended. Start with 1-5 communities and monitor resource usage.

### Q: What's the difference between community tweets and regular tweets?

A: Community tweets are only visible to community members and marked with `community_id` in the database.

---

## Examples

### Example 1: Track Tech Communities

```python
tech_communities = [
    "1234567890123456789",  # Web Development
    "9876543210987654321",  # AI & Machine Learning
    "1111111111111111111",  # DevOps
]

for community_id in tech_communities:
    # Track with 1-hour interval
    requests.post(
        f"http://localhost:8000/api/communities/{community_id}/track",
        json={"interval": 3600}
    )
```

### Example 2: Compare Communities

```python
def compare_communities(community_ids):
    for cid in community_ids:
        response = requests.get(f"http://localhost:8000/api/communities/{cid}/tweets")
        tweets = response.json()['tweets']

        avg_engagement = sum(t['likes_count'] for t in tweets) / len(tweets)
        print(f"Community {cid}: Avg {avg_engagement:.1f} likes per tweet")
```

### Example 3: Export Community Data

```python
import pandas as pd

# Get all tweets from a community
response = requests.get(f"http://localhost:8000/api/communities/COMMUNITY_ID/tweets?limit=1000")
tweets = response.json()['tweets']

# Convert to DataFrame
df = pd.DataFrame(tweets)

# Export to CSV
df.to_csv('community_tweets.csv', index=False)
```

---

## Summary

**Community scraping is now fully supported!**

✅ Scrape tweets from specific Twitter communities
✅ Two methods: TwitterAPI.io (fast) and Twitter Direct (free)
✅ Automatic tracking with configurable intervals
✅ Database support for communities and community tweets
✅ Full API endpoints for integration

**Get started in 3 steps:**
1. Find a community ID
2. Configure authentication (API key or cookies)
3. Start scraping!

For more help:
- TwitterAPI.io setup: See [TWITTERAPIIO_SETUP.md](TWITTERAPIIO_SETUP.md)
- Cookie authentication: See [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)
- General troubleshooting: See [TROUBLESHOOT.md](TROUBLESHOOT.md)
