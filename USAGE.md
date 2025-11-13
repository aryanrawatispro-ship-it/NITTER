# Usage Guide

## Quick Start

### 1. Using Docker (Recommended)

```bash
# Start all services
./run.sh

# Or manually with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python setup_db.py
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload

# In separate terminals, start Celery
celery -A src.scheduler.celery_app worker --loglevel=info
celery -A src.scheduler.celery_app beat --loglevel=info
```

## API Usage Examples

### Track a User

```bash
curl -X POST "http://localhost:8000/api/users/track" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "elonmusk",
    "check_interval": 900
  }'
```

### Get User Tweets

```bash
curl "http://localhost:8000/api/tweets/user/elonmusk?limit=50"
```

### Search Tweets

```bash
curl -X POST "http://localhost:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "search_type": "keyword",
    "track": true,
    "check_interval": 3600
  }'
```

### Export Data

```bash
# Export tweets to CSV
curl "http://localhost:8000/api/export/tweets/csv?username=elonmusk" -o tweets.csv

# Export to JSON
curl "http://localhost:8000/api/export/tweets/json?username=elonmusk" -o tweets.json
```

### Create Webhook

```bash
curl -X POST "http://localhost:8000/api/webhooks/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-webhook-url.com/notify",
    "event_type": "new_tweet",
    "username": "elonmusk"
  }'
```

## Python Client Example

```python
import requests

API_BASE = "http://localhost:8000"

# Track a user
response = requests.post(f"{API_BASE}/api/users/track", json={
    "username": "OpenAI",
    "check_interval": 900  # Check every 15 minutes
})
print(response.json())

# Get tracked users
users = requests.get(f"{API_BASE}/api/users/tracked").json()
print(f"Tracking {len(users)} users")

# Get user statistics
stats = requests.get(f"{API_BASE}/api/users/OpenAI/stats").json()
print(f"Average engagement: {stats['avg_engagement_rate']}%")

# Get top tweets
top_tweets = requests.get(
    f"{API_BASE}/api/tweets/user/OpenAI/top",
    params={"metric": "engagement_rate", "limit": 10}
).json()

for tweet in top_tweets:
    print(f"Tweet: {tweet['text'][:50]}... - Engagement: {tweet['engagement_rate']}%")

# Search for tweets
response = requests.post(f"{API_BASE}/api/search/", json={
    "query": "#AI",
    "search_type": "hashtag",
    "track": True
})

# Export data
csv_data = requests.get(
    f"{API_BASE}/api/export/tweets/csv",
    params={"username": "OpenAI", "limit": 1000}
)
with open("tweets.csv", "wb") as f:
    f.write(csv_data.content)
```

## Dashboard Access

Open your browser and navigate to:
- **Dashboard**: http://localhost/dashboard or http://localhost:8000/dashboard
- **API Documentation**: http://localhost/docs or http://localhost:8000/docs
- **ReDoc**: http://localhost/redoc or http://localhost:8000/redoc

## Advanced Configuration

### Adjust Scraping Intervals

Edit `.env` file:

```bash
# Time between requests (seconds)
MIN_REQUEST_DELAY=2
MAX_REQUEST_DELAY=8

# Health check interval for Nitter instances (seconds)
HEALTH_CHECK_INTERVAL=300

# Request timeout (seconds)
REQUEST_TIMEOUT=30
```

### Enable Proxy Support

```bash
USE_PROXY=true
PROXY_URL=http://your-proxy:port
```

### Configure Logging

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/nitter_scraper.log
```

## Monitoring

### View Celery Tasks

```bash
# Install Flower (Celery monitoring tool)
pip install flower

# Start Flower
celery -A src.scheduler.celery_app flower --port=5555

# Access at http://localhost:5555
```

### Database Access

```bash
# Using Docker
docker-compose exec postgres psql -U nitter_user -d nitter_db

# Manually
psql -U nitter_user -d nitter_db
```

### Redis CLI

```bash
# Using Docker
docker-compose exec redis redis-cli

# Check queue length
LLEN celery

# Monitor commands
MONITOR
```

## Troubleshooting

### No healthy Nitter instances

The Nitter instance list may become outdated. Update `src/nitter_manager/instances.py` with working instances.

### Scraping fails

- Check if Nitter instances are accessible
- Verify Playwright browser is installed: `playwright install chromium`
- Check logs: `docker-compose logs celery_worker`

### Database connection errors

- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Verify credentials

### Celery tasks not running

- Check Redis is running: `docker-compose ps redis`
- Verify Celery worker is running: `docker-compose ps celery_worker`
- Check Celery logs: `docker-compose logs celery_worker`

## Best Practices

1. **Rate Limiting**: Don't set check intervals too low (minimum 900 seconds / 15 minutes recommended)
2. **Instance Rotation**: The system automatically rotates through healthy Nitter instances
3. **Error Handling**: Failed scrapes are automatically retried with exponential backoff
4. **Data Cleanup**: Old scraping jobs are automatically cleaned up after 30 days
5. **Monitoring**: Use the dashboard to monitor system health and scraping statistics

## Scaling

### Increase Celery Workers

Edit `docker-compose.yml`:

```yaml
celery_worker:
  command: celery -A src.scheduler.celery_app worker --loglevel=info --concurrency=8
```

### Add More Workers

```yaml
celery_worker_2:
  # Copy celery_worker service configuration
  container_name: nitter_celery_worker_2
```

### Database Performance

- Add indexes for frequently queried fields
- Use connection pooling (already configured)
- Consider read replicas for high-traffic deployments
