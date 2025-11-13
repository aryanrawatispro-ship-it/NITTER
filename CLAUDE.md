Build a Twitter scraping system using Nitter instances WITHOUT Twitter API:

1. NITTER INSTANCE MANAGER:
   - List of 15+ working Nitter instances
   - Auto health-check every 5 minutes
   - Rotate to working instances automatically
   - Fallback chain when instances fail

2. SCRAPING ENGINE:
   - Python with Playwright/Selenium
   - Scrape user profiles: bio, followers count, tweets
   - Scrape tweets: text, likes, retweets, replies, timestamp
   - Scrape search results for keywords/hashtags
   - Download media files (images/videos)
   - Handle pagination for scrolling through timelines

3. DATA PROCESSING:
   - Clean and normalize tweet text
   - Extract hashtags, mentions, URLs
   - Calculate engagement rates
   - Detect sentiment (positive/negative/neutral)
   - Store in PostgreSQL database

4. SCHEDULING SYSTEM:
   - Celery for background jobs
   - Monitor accounts every 15 minutes to 24 hours (configurable)
   - Queue system to prevent overwhelming instances
   - Retry failed scrapes with exponential backoff

5. CLIENT FEATURES:
   - REST API to query scraped data
   - Webhook notifications for new tweets from tracked accounts
   - Export to CSV/JSON/Excel
   - Real-time dashboard with charts

6. ANTI-DETECTION:
   - Random user agents
   - Random delays between requests (2-8 seconds)
   - Respect robots.txt
   - Proxy rotation support (optional)

7. DEPLOYMENT:
   - Docker Compose setup
   - Redis for caching
   - Nginx reverse proxy
   - PM2 or Supervisor for process management

Include these specific scrapers:
- Profile scraper (username → all profile data)
- Timeline scraper (get last 100 tweets from user)
- Search scraper (keyword → matching tweets)
- Thread scraper (tweet URL → full thread)
- Follower list scraper (if available on Nitter)
