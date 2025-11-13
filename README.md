# Twitter Scraping System

A comprehensive Twitter data scraping system with **multiple scraping methods**, designed to collect and analyze Twitter data reliably and affordably.

## Features

- **Multiple Scraping Methods**: 3-tier fallback strategy (TwitterAPI.io → Twitter Direct → Nitter)
- **Nitter Instance Manager**: Automatic health checking and rotation across 15+ Nitter instances
- **Twitter Direct Scraping**: Browser-based scraping with cookie authentication (no API needed!)
- **TwitterAPI.io Integration**: Fast, reliable paid API ($0.15 per 1K tweets vs $100+/month official)
- **Multi-Purpose Scrapers**: Profile, timeline, search, thread, and follower list scraping
- **Data Processing**: Text cleaning, hashtag/mention extraction, sentiment analysis, engagement metrics
- **Task Scheduling**: Celery-based background job system with configurable intervals
- **REST API**: Query scraped data programmatically
- **Webhooks**: Real-time notifications for tracked accounts
- **Export Options**: CSV, JSON, and Excel export formats
- **Real-Time Dashboard**: Visualize metrics and scraped data
- **Anti-Detection**: Random user agents, delays, and proxy support
- **Scalable Architecture**: Docker-based deployment with Redis caching

## Scraping Methods

This system supports **3 different scraping methods** with automatic fallback:

### 1. TwitterAPI.io (Recommended for Production)
- ⚡ **Fastest**: API calls return instantly
- ✅ **Most Reliable**: Professional infrastructure
- 💰 **Affordable**: $0.15 per 1K tweets (free tier: 500 requests/month)
- 📚 **Setup**: See [TWITTERAPIIO_SETUP.md](TWITTERAPIIO_SETUP.md)

### 2. Twitter Direct (Best for Free Usage)
- 🆓 **Free**: No costs, unlimited usage
- 🔒 **Cookie-based**: More secure than password login
- ✅ **Works when Nitter blocked**: Scrapes twitter.com directly
- 📚 **Setup**: See [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)

### 3. Nitter Instances (Fallback)
- 🆓 **Free**: No costs
- ⚠️ **Currently Blocked**: Twitter blocked most Nitter instances in 2024
- 🔄 **Auto-rotation**: Tries multiple instances automatically
- 📚 **Status**: See [NITTER_STATUS.md](NITTER_STATUS.md)

### Priority & Fallback

The system automatically tries methods in order:
1. **TwitterAPI.io** (if enabled) - fastest
2. **Twitter Direct** (if cookies/credentials set) - free
3. **Nitter** (always tries last) - last resort

If one method fails, it automatically falls back to the next. This ensures **maximum reliability** - you always get data!

### Comparison

| Method | Cost | Speed | Reliability | Setup |
|--------|------|-------|-------------|-------|
| **TwitterAPI.io** | $0.15/1K | ⚡ Instant | ✅✅✅ Excellent | Easy |
| **Twitter Direct** | Free | 🐌 Slow | ✅✅ Good | Medium |
| **Nitter** | Free | ⚡ Fast | ❌ Blocked | Easy |
| Official Twitter API | $100-5000/mo | ⚡ Instant | ✅✅✅ Excellent | Hard |

## Architecture

```
nitter-scraper/
├── src/
│   ├── nitter_manager/    # Instance health checking & rotation
│   ├── scrapers/          # Profile, timeline, search, thread scrapers
│   ├── data_processing/   # Text cleaning, sentiment, extraction
│   ├── api/               # FastAPI REST endpoints
│   ├── scheduler/         # Celery tasks and scheduling
│   ├── webhooks/          # Webhook notification system
│   ├── dashboard/         # Real-time web dashboard
│   └── utils/             # Shared utilities
├── tests/                 # Unit and integration tests
├── config/                # Configuration files
└── docker/                # Docker configuration
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd NITTER
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
alembic upgrade head
```

### Running the Application

#### Development Mode

```bash
# Start API server
uvicorn src.api.main:app --reload --port 8000

# Start Celery worker
celery -A src.scheduler.celery_app worker --loglevel=info

# Start Celery beat scheduler
celery -A src.scheduler.celery_app beat --loglevel=info
```

#### Production Mode (Docker)

**Easiest way - Use the startup script:**
```bash
chmod +x run.sh
./run.sh
```

**Or manually:**
```bash
docker-compose up -d
```

## Usage

### Interactive CLI

The easiest way to use the scraper is through the interactive CLI:

```bash
python3 cli.py
```

Features:
- Track users with configurable intervals
- One-time scraping on demand
- View tracked users and scraped tweets
- Search for tweets by keyword/hashtag
- Export data to CSV/JSON
- View scraping jobs and statistics

### API Examples

```python
import requests

# Track a Twitter user
response = requests.post('http://localhost:8000/api/users/track', json={
    'username': 'elonmusk',
    'check_interval': 900  # Check every 15 minutes
})

# Search tweets by keyword
response = requests.get('http://localhost:8000/api/tweets/search', params={
    'keyword': 'AI',
    'limit': 100
})

# Export data
response = requests.get('http://localhost:8000/api/export/tweets', params={
    'username': 'elonmusk',
    'format': 'csv'
})
```

### Dashboard

Access the web dashboard at: http://localhost:8000/dashboard

## Configuration

See `.env.example` for all available configuration options.

Key settings:
- `MIN_REQUEST_DELAY` / `MAX_REQUEST_DELAY`: Random delay between requests (anti-detection)
- `HEALTH_CHECK_INTERVAL`: How often to check Nitter instance health (seconds)
- `MAX_RETRIES`: Number of retry attempts for failed scrapes

## Development

### Running Tests

```bash
pytest tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Documentation

### Setup Guides
- **[QUICK_START.md](QUICK_START.md)** - 5-minute quick start guide
- **[TWITTERAPIIO_SETUP.md](TWITTERAPIIO_SETUP.md)** - TwitterAPI.io integration guide (recommended for production)
- **[HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)** - Cookie extraction guide for Twitter Direct scraping
- **[TWITTER_DIRECT_SETUP.md](TWITTER_DIRECT_SETUP.md)** - Twitter Direct scraping setup

### Deployment
- **[VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md)** - Complete guide for deploying on a VPS (DigitalOcean, AWS, Hetzner, etc.)
- **[DEPLOYMENT_UPDATE.md](DEPLOYMENT_UPDATE.md)** - Quick update guide for applying latest fixes

### Reference
- **[FIXES_APPLIED.md](FIXES_APPLIED.md)** - Detailed changelog of recent fixes and improvements
- **[NITTER_STATUS.md](NITTER_STATUS.md)** - Why Nitter is blocked + all solutions
- **[TROUBLESHOOT.md](TROUBLESHOOT.md)** - Complete troubleshooting guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guidelines for contributing to the project

### Troubleshooting

If you encounter database migration issues, see [FIXES_APPLIED.md](FIXES_APPLIED.md) for solutions.

Common issues:
- **Database tables don't exist**: Run `./run.sh` which auto-generates migrations
- **Port conflicts**: Stop conflicting services or change ports in docker-compose.yml
- **Out of memory**: Add swap space (see VPS_DEPLOYMENT.md)
- **Nitter instances failing**: Health checker will automatically rotate to working instances

## License

MIT License

## Disclaimer

This tool is for educational and research purposes only. Please respect Twitter's Terms of Service and rate limits. Always check robots.txt and use appropriate delays between requests.
