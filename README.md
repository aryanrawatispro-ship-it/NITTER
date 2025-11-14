# Twitter Community Scraper

Fast Twitter Community scraping using **TwitterAPI.io** - no Twitter account needed!

## What It Does

Scrapes **ALL tweets** from any Twitter Community and exports to CSV:

| Field | Description |
|-------|-------------|
| **username** | Author's Twitter handle |
| **content** | Tweet text |
| **likes** | Number of likes |
| **retweets** | Number of retweets |
| **comments** | Number of replies |
| **post_link** | Direct URL to tweet |
| **posted_at** | When posted |

---

## Quick Start (4 Steps)

### 1. Get TwitterAPI.io API Key

1. Go to https://twitterapi.io
2. Sign up (free tier: 500 requests/month)
3. Copy your API key

**Cost:** $0.15 per 1K tweets after free tier (way cheaper than Twitter's official API at $100-5000/month!)

### 2. Install & Configure

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin -y
# Logout and login again

# Clone repo
git clone -b claude/start-work-011CV5edTh7A3uaweF4SveNQ https://github.com/aryanrawatispro-ship-it/NITTER.git
cd NITTER

# Configure
cp .env.example .env
nano .env
# Set: TWITTERAPIIO_API_KEY=your_api_key_here
```

### 3. Start System

```bash
docker compose up -d
```

### 4. Scrape Community

```bash
python3 cli.py
# Choose option 1
# Enter Community ID: 1977017211303690504
# Choose option 4 (ALL tweets)
# Wait for scraping...
# Choose option 5 to export CSV
```

**Done!** You have a CSV file with all community tweets.

---

## Scrape Your Community

### Find Community ID

From URL: `https://x.com/i/communities/1977017211303690504`

Community ID: `1977017211303690504`

### Using CLI

```bash
python3 cli.py
```

**Menu:**
1. Scrape a community (one-time)
2. Track a community (automatic)
3. View tracked communities
4. View scraped tweets
5. Export to CSV/JSON
6. API docs
7. Exit

### Using API

```bash
# Scrape ALL tweets
curl -X POST "http://localhost:8000/api/communities/1977017211303690504/scrape"

# Export to CSV
curl "http://localhost:8000/api/export/community/csv?community_id=1977017211303690504&limit=100000" > tweets.csv
```

---

## Example: Scrape Community 1977017211303690504

```bash
# Start system
docker compose up -d && sleep 30

# Scrape ALL posts
curl -X POST "http://localhost:8000/api/communities/1977017211303690504/scrape"

# Wait for completion (watch logs)
docker compose logs -f worker

# Export to CSV
curl "http://localhost:8000/api/export/community/csv?community_id=1977017211303690504&limit=100000" > community.csv

# Open community.csv - Done!
```

**CSV Output:**
```csv
username,content,likes,retweets,comments,post_link,posted_at
elonmusk,"Great discussion!",1500,250,100,https://twitter.com/elonmusk/status/123...,2024-01-15
user2,"Another tweet",300,50,20,https://twitter.com/user2/status/456...,2024-01-14
```

---

## Features

- ✅ **No Twitter account needed** - TwitterAPI.io handles everything
- ✅ **Scrape ALL tweets** - No limits, get entire community history
- ✅ **Fast** - API-based, much faster than browser scraping
- ✅ **Reliable** - Professional infrastructure, rarely fails
- ✅ **Export CSV/JSON** - Ready for Excel, Google Sheets, analysis
- ✅ **Track communities** - Automatic periodic scraping
- ✅ **Complete data** - Username, likes, retweets, comments, links

---

## Configuration

Edit `.env` file:

```bash
# Required - Get from https://twitterapi.io
TWITTERAPIIO_API_KEY=your_api_key_here

# Optional - Change if needed
DATABASE_URL=postgresql://nitter_user:nitter_pass@postgres:5432/nitter_db
REDIS_URL=redis://redis:6379/0
API_PORT=8000
LOG_LEVEL=INFO
```

---

## API Endpoints

Full docs at: http://localhost:8000/docs

**Communities:**
- `POST /api/communities/{id}/scrape` - Scrape tweets
- `POST /api/communities/{id}/track` - Auto-scrape
- `GET /api/communities/{id}/tweets` - View tweets
- `GET /api/communities/` - List tracked

**Export:**
- `GET /api/export/community/csv` - Export CSV
- `GET /api/export/community/json` - Export JSON

---

## Common Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f api
docker compose logs -f worker

# Restart
docker compose restart

# Update
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
docker compose restart
```

---

## Troubleshooting

### "API key not configured"

```bash
nano .env
# Add: TWITTERAPIIO_API_KEY=your_key_here
docker compose restart
```

### "API is not running"

```bash
docker compose ps
docker compose logs api
docker compose restart
```

### "No tweets found"

- Check community ID is correct
- Community might be private
- Check API key has remaining quota

### "Internal Server Error"

```bash
# Check logs
docker compose logs api

# Run migrations
docker compose exec api alembic upgrade head

# Full reset
docker compose down -v
docker compose up -d
```

---

## Cost

| Usage | Cost |
|-------|------|
| **Free tier** | 500 requests/month |
| **Paid** | $0.15 per 1,000 tweets |
| **Example** | 10,000 tweets = $1.50 |

**vs Twitter Official API:** $100-5000/month minimum

---

## Why TwitterAPI.io?

✅ **No Twitter account needed**
✅ **Don't need to join communities**
✅ **Fast API calls (not browser)**
✅ **Very affordable ($0.15/1K)**
✅ **Reliable infrastructure**
✅ **Simple to use**

---

## System Requirements

- **VPS/Server:** 2GB RAM minimum
- **Disk:** 10GB free
- **OS:** Ubuntu 20.04+ or Debian 11+
- **Docker:** 20.10+
- **Python:** 3.10+ (for CLI)

---

## Architecture

```
Docker Containers:
├── postgres    - Database (stores tweets)
├── redis       - Cache & job queue
├── api         - FastAPI server
├── worker      - Background scraper (TwitterAPI.io)
└── beat        - Task scheduler

Data Flow:
1. CLI/API request → Worker
2. Worker calls TwitterAPI.io
3. Tweets saved to PostgreSQL
4. Export via API
```

---

## Support

- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Logs:** `docker compose logs -f`
- **TwitterAPI.io:** https://twitterapi.io

---

## License

MIT - Use freely for any purpose

---

**Ready to scrape!** 🚀

```bash
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
docker compose up -d
python3 cli.py
```
