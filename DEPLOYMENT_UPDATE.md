# Quick Deployment Update - Fix Database Migrations

## Issue Fixed
The `alembic/versions` directory was missing in the Docker container, causing migration generation to fail with:
```
FileNotFoundError: /app/alembic/versions/xxx_initial_database_schema.py
```

## What Was Changed
1. Added `.gitkeep` file to `alembic/versions/` to ensure the directory is tracked
2. Updated `docker/Dockerfile` to explicitly create the directory during build

## How to Apply This Fix on Your VPS

### Step 1: Pull the Latest Changes
```bash
cd /path/to/NITTER
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
```

### Step 2: Rebuild the Docker Containers
```bash
# Stop the containers
docker compose down

# Rebuild with the updated Dockerfile
docker compose build --no-cache

# Start everything back up
docker compose up -d
```

### Step 3: Create Database Tables
Now the migration should work properly:

```bash
# Generate the initial migration
docker compose exec api alembic revision --autogenerate -m "Initial database schema"

# Apply the migration to create all tables
docker compose exec api alembic upgrade head
```

### Step 4: Verify Everything Works
```bash
# Check if tables were created
docker compose exec api python -c "from src.utils.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"

# Check API health
curl http://localhost:8000/health

# Test the CLI
python3 cli.py
```

## Expected Output

After running the migration, you should see:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'twitter_users'
INFO  [alembic.autogenerate.compare] Detected added table 'search_queries'
INFO  [alembic.autogenerate.compare] Detected added table 'scraping_jobs'
INFO  [alembic.autogenerate.compare] Detected added table 'webhooks'
INFO  [alembic.autogenerate.compare] Detected added table 'tweets'
  Generating /app/alembic/versions/xxx_initial_database_schema.py ...  done
```

Then after upgrade:
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxx, Initial database schema
```

## Troubleshooting

### If "docker compose" doesn't work
Try using `docker-compose` (with hyphen):
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### If rebuild fails with "permission denied"
```bash
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

### If git pull shows conflicts
```bash
git stash
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
git stash pop
```

### If tables still don't exist after migration
Check the database logs:
```bash
docker compose logs postgres
docker compose logs api
```

## Quick Start After Fix

Once migrations are complete, you can immediately start using the scraper:

```bash
# Using the CLI
python3 cli.py

# Or using curl
curl -X POST http://localhost:8000/api/users/track \
  -H "Content-Type: application/json" \
  -d '{"username": "elonmusk", "check_interval": 900}'
```

## What's Working Now
- ✓ All database tables will be created properly
- ✓ Profile scraping
- ✓ Timeline scraping (last 100 tweets)
- ✓ Search scraping (keywords/hashtags)
- ✓ Periodic tracking with configurable intervals
- ✓ One-time scraping on demand
- ✓ Data export (CSV/JSON)
- ✓ Interactive CLI
- ✓ REST API with documentation
- ✓ Background task scheduling with Celery
- ✓ Automatic Nitter instance rotation

## Next Steps
After applying this fix and creating the tables:
1. Try tracking a Twitter user (e.g., "elonmusk", "twitter")
2. Check the dashboard: http://your-vps-ip/dashboard
3. Monitor scraping jobs: http://your-vps-ip/docs
4. Export data to CSV/JSON
5. Set up webhooks for notifications (optional)
