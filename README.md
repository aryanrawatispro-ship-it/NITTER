# Twitter Community Scraper

Simple system to scrape tweets from Twitter Communities using TwitterAPI.io or Twitter Direct browser scraping.

## What Does This Do?

Scrapes tweets from Twitter Communities including:
- Username
- Tweet content
- Likes, retweets, comments
- Tweet URL (direct link)
- Posted date

Export to CSV or JSON.

---

## Quick Start

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin -y
```

Logout and login again.

### 2. Clone & Configure

```bash
git clone -b claude/start-work-011CV5edTh7A3uaweF4SveNQ https://github.com/aryanrawatispro-ship-it/NITTER.git
cd NITTER
cp .env.example .env
nano .env  # Configure scraping method (see below)
```

### 3. Start

```bash
docker compose up -d
```

### 4. Scrape Communities

```bash
python3 cli.py
```

---

## Configuration (Choose ONE Method)

### Option A: FREE Scraping (Twitter Direct)

**Requirements:** Twitter account + join the community

```bash
# In .env file:
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json
```

**Get cookies:** See [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)

**Pros:** Free, unlimited
**Cons:** Slower, requires Twitter account, must join community

---

### Option B: FAST Scraping (TwitterAPI.io)

**Requirements:** API key (no Twitter account needed!)

```bash
# In .env file:
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_api_key_here
```

**Get API key:** https://twitterapi.io (free tier: 500 requests/month)

**Pros:** Fast, no Twitter account needed, don't need to join community
**Cons:** Costs money ($0.15 per 1K tweets after free tier)

---

## How to Use

### CLI (Interactive)

```bash
python3 cli.py
```

Menu options:
1. **Scrape a community** - One-time scrape (100, 500, 1000, or ALL tweets)
2. **Track a community** - Automatic periodic scraping
3. **View tracked communities** - See what's being monitored
4. **View community tweets** - Browse scraped tweets
5. **Export data** - Download as CSV or JSON
6. **API docs** - View API documentation

### API (Direct)

```bash
# Scrape community
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/scrape"

# Scrape ALL tweets
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/scrape?max_tweets="

# Get tweets
curl "http://localhost:8000/api/communities/COMMUNITY_ID/tweets"

# Export to CSV
curl "http://localhost:8000/api/export/community/csv?community_id=COMMUNITY_ID" > tweets.csv

# Track community (auto-scrape every hour)
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/track?check_interval=3600"
```

---

## Finding Community ID

1. Go to the community on Twitter
2. URL looks like: `twitter.com/i/communities/1234567890123456789`
3. The number at the end is the Community ID: `1234567890123456789`

---

## Common Commands

```bash
# Start system
docker compose up -d

# Stop system
docker compose down

# View logs
docker compose logs -f api

# Restart
docker compose restart

# Update
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
docker compose restart
```

---

## CSV Export Fields

When you export to CSV, you get these fields:

| Field | Description |
|-------|-------------|
| username | Twitter username |
| content | Tweet text |
| likes | Number of likes |
| retweets | Number of retweets |
| comments | Number of replies |
| post_link | Direct URL to tweet |
| posted_at | When the tweet was posted |

---

## API Endpoints

All endpoints available at `http://localhost:8000/docs`

**Communities:**
- `POST /api/communities/{community_id}/scrape` - Scrape tweets
- `POST /api/communities/{community_id}/track` - Track community
- `POST /api/communities/{community_id}/untrack` - Stop tracking
- `GET /api/communities/{community_id}/tweets` - Get scraped tweets
- `GET /api/communities/` - List tracked communities
- `GET /api/communities/{community_id}` - Get community info

**Export:**
- `GET /api/export/community/csv` - Export to CSV
- `GET /api/export/community/json` - Export to JSON

---

## Troubleshooting

### "API is not running"

```bash
docker compose ps  # Check if containers are running
docker compose logs api  # Check for errors
docker compose restart  # Restart everything
```

### "No scraping method enabled"

Configure at least one method in `.env`:
- `USE_TWITTERAPIIO=true` (and set API key)
- OR `USE_TWITTER_DIRECT=true` (and set cookies)

### "Failed to scrape community"

**For TwitterAPI.io:**
- Check API key is correct
- Check you have remaining quota

**For Twitter Direct:**
- Make sure you have valid cookies
- Make sure you joined the community on Twitter
- Cookies might have expired (get new ones)

### "Internal Server Error"

```bash
# Check logs
docker compose logs api

# Run database migrations
docker compose exec api alembic upgrade head

# Full reset
docker compose down -v
docker compose up -d
```

---

## Documentation

- **[HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)** - Get Twitter cookies for free scraping
- **[COMMUNITY_SCRAPING.md](COMMUNITY_SCRAPING.md)** - Detailed community scraping guide
- **[SCRAPING_METHODS_EXPLAINED.md](SCRAPING_METHODS_EXPLAINED.md)** - Free vs Paid comparison

---

## Architecture

```
Docker Containers:
├── postgres    - Database (stores tweets)
├── redis       - Cache & job queue
├── api         - FastAPI server
├── worker      - Background scraper
└── beat        - Task scheduler

Scraping Methods:
├── TwitterAPI.io  - Fast API calls ($0.15/1K tweets)
└── Twitter Direct - Free browser scraping (Playwright)
```

---

## Example Workflow

1. **Find a community** on Twitter
2. **Get the Community ID** from URL
3. **Configure .env** with API key or cookies
4. **Start system:** `docker compose up -d`
5. **Run CLI:** `python3 cli.py`
6. **Choose option 1:** Scrape a community
7. **Enter Community ID**
8. **Choose how many tweets:** 100, 500, 1000, or ALL
9. **Wait for scraping** to complete
10. **Export data:** Choose option 5 in CLI
11. **Download CSV** with all tweets!

---

## System Requirements

- **VPS/Server:** 2GB RAM minimum (4GB recommended)
- **Disk:** 10GB free space
- **OS:** Ubuntu 20.04+ or Debian 11+
- **Docker:** 20.10+
- **Python:** 3.10+ (for CLI only)

---

## Cost Comparison

| Method | Cost | Speed | Twitter Account Required? |
|--------|------|-------|--------------------------|
| **Twitter Direct** | FREE | Slow (browser) | YES (must join community) |
| **TwitterAPI.io** | $0.15/1K tweets | Fast (API) | NO |
| Official Twitter API | $100-5000/month | Fast | YES |

**Recommendation:**
- **Personal use, low volume:** Twitter Direct (free)
- **Business/high volume:** TwitterAPI.io ($0.15/1K)

---

## Support

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Logs:** `docker compose logs -f`

---

## License

MIT License - Use freely for any purpose.

---

**That's it!** You now have a simple Twitter Community scraper. 🚀

**Pull latest code:**
```bash
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
```
