# Nitter Twitter Scraping System

A comprehensive Twitter data scraping system using Nitter instances, designed to collect and analyze Twitter data without requiring Twitter API access.

## Features

- **Nitter Instance Manager**: Automatic health checking and rotation across 15+ Nitter instances
- **Multi-Purpose Scrapers**: Profile, timeline, search, thread, and follower list scraping
- **Data Processing**: Text cleaning, hashtag/mention extraction, sentiment analysis, engagement metrics
- **Task Scheduling**: Celery-based background job system with configurable intervals
- **REST API**: Query scraped data programmatically
- **Webhooks**: Real-time notifications for tracked accounts
- **Export Options**: CSV, JSON, and Excel export formats
- **Real-Time Dashboard**: Visualize metrics and scraped data
- **Anti-Detection**: Random user agents, delays, and proxy support
- **Scalable Architecture**: Docker-based deployment with Redis caching

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

```bash
docker-compose up -d
```

## Usage

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

## License

MIT License

## Disclaimer

This tool is for educational and research purposes only. Please respect Twitter's Terms of Service and rate limits. Always check robots.txt and use appropriate delays between requests.
