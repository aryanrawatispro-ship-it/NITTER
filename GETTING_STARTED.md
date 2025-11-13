# Getting Started - Deploy NITTER on Your VPS

Complete step-by-step guide to get NITTER Twitter scraping system running on your VPS from scratch.

---

## 📋 Prerequisites

Before you start, make sure your VPS has:

- **Operating System**: Ubuntu 20.04+ or Debian 11+ (recommended)
- **RAM**: Minimum 2GB (4GB recommended for browser scraping)
- **Disk Space**: Minimum 10GB free
- **Docker**: Version 20.10+ with Docker Compose
- **Git**: For cloning the repository
- **Port 8000**: Available for the API (or choose another)

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone the repository
git clone <repository-url> NITTER
cd NITTER

# 2. Choose your scraping method and configure
cp .env.example .env
nano .env  # Edit configuration (see Configuration section below)

# 3. Start the system
docker compose up -d

# 4. Check it's running
docker compose ps

# 5. Test scraping
python3 cli.py
```

**That's it!** Your scraping system is running.

---

## 📖 Detailed Step-by-Step Guide

### Step 1: Install Prerequisites on VPS

If you don't have Docker installed:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
# SSH back into your VPS

# Install Docker Compose (if not included)
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone the Repository

```bash
# Clone to your VPS
cd ~
git clone <repository-url> NITTER
cd NITTER

# Check files are there
ls -la
```

You should see:
- `docker-compose.yml`
- `.env.example`
- `requirements.txt`
- `src/` directory
- etc.

### Step 3: Configuration

Copy the example configuration and edit it:

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**IMPORTANT: Choose your scraping method and configure it!**

#### Option A: FREE Scraping (Twitter Direct)

If you want **FREE** scraping with browser automation:

```bash
# In .env file, set:
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json

# Optional (more secure than cookies):
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password

# Disable paid options
USE_TWITTERAPIIO=false
```

**Then get your Twitter cookies:**

See [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md) for detailed instructions.

Quick version:
1. Log into twitter.com in your browser
2. Open DevTools (F12) → Application → Cookies
3. Export cookies to `twitter_cookies.json`
4. Upload to your VPS in the NITTER directory

#### Option B: FAST Scraping (TwitterAPI.io)

If you want **FAST** scraping without Twitter account:

```bash
# In .env file, set:
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_api_key_here

# Optional: Enable browser as fallback
USE_TWITTER_DIRECT=false
```

**Get API key:**
1. Go to https://twitterapi.io
2. Sign up (free tier: 500 requests/month)
3. Copy your API key
4. Paste into `.env`

#### Option C: BOTH (Recommended)

Use API for speed, fallback to browser for free backup:

```bash
# In .env file, set:
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_api_key_here
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json
```

#### Other Important Settings

```bash
# Database settings (can leave defaults)
POSTGRES_USER=nitter_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=nitter_db

# API settings
API_PORT=8000  # Change if port 8000 is taken

# Redis settings (can leave defaults)
REDIS_HOST=redis
REDIS_PORT=6379

# Celery settings (can leave defaults)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**Save and exit** (Ctrl+X, then Y, then Enter)

### Step 4: Start the System

```bash
# Build and start all services
docker compose up -d

# This will start:
# - PostgreSQL database
# - Redis cache
# - API server (FastAPI)
# - Celery worker (background tasks)
# - Celery beat (scheduler)
```

Wait about 30 seconds for everything to start.

### Step 5: Verify It's Running

```bash
# Check all containers are running
docker compose ps

# Should show 5 containers with "Up" status:
# - nitter-postgres
# - nitter-redis
# - nitter-api
# - nitter-worker
# - nitter-beat
```

All should show `Up` status. If any show `Exit` or `Restarting`, check logs:

```bash
# Check logs for errors
docker compose logs api
docker compose logs worker
```

### Step 6: Check API is Accessible

```bash
# Test API health endpoint
curl http://localhost:8000/health

# Should return:
# {"status": "healthy"}
```

If you get "Connection refused", check:
- API container is running: `docker compose ps`
- Port is correct: Check `API_PORT` in `.env`
- Firewall allows the port (if accessing remotely)

### Step 7: Test Scraping

Now test that scraping actually works!

#### Test with CLI

```bash
# Install Python dependencies for CLI (optional)
pip3 install requests

# Run CLI
python3 cli.py
```

You'll see a menu:

```
========================================
  NITTER Twitter Scraping System - CLI
========================================

Choose an option:
1. Scrape user profile
2. Scrape user timeline
3. Scrape search results
4. Scrape community tweets
5. View scraped data
6. Exit

Enter choice (1-6):
```

**Try scraping a profile:**

```
Enter choice: 1
Enter Twitter username: elonmusk
Max tweets (default 100): 50
```

If it works, you'll see:
```
✅ Successfully scraped profile for @elonmusk
✅ Scraped 50 tweets
```

#### Test with API (Alternative)

```bash
# Scrape a user profile
curl -X POST "http://localhost:8000/api/users/elonmusk/scrape?max_tweets=10"

# Check tracked users
curl http://localhost:8000/api/users/

# Scrape community (requires community ID)
curl -X POST "http://localhost:8000/api/communities/1234567890/scrape?max_tweets=50"
```

---

## 🎯 What to Do Next

### 1. Set Up Community Scraping

If you want to scrape Twitter communities:

```bash
# Get community ID from URL: https://twitter.com/i/communities/1234567890
# Then scrape it:
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/scrape?max_tweets=100"
```

See [COMMUNITY_SCRAPING.md](COMMUNITY_SCRAPING.md) for full guide.

### 2. Track Users/Communities Automatically

```bash
# Track a user (scrapes every hour automatically)
curl -X POST "http://localhost:8000/api/users/elonmusk/track" \
  -H "Content-Type: application/json" \
  -d '{"check_interval": 3600}'

# Track a community
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/track" \
  -H "Content-Type: application/json" \
  -d '{"check_interval": 3600}'
```

The system will now automatically scrape them in the background!

### 3. Export Data

```bash
# Export to CSV
curl "http://localhost:8000/api/export/csv?username=elonmusk" > tweets.csv

# Export to JSON
curl "http://localhost:8000/api/export/json?username=elonmusk" > tweets.json
```

### 4. View Logs

```bash
# View API logs (web server)
docker compose logs -f api

# View worker logs (background tasks)
docker compose logs -f worker

# View all logs
docker compose logs -f
```

---

## 🔧 Common Issues & Fixes

### Issue 1: "Connection refused" when accessing API

**Fix:**
```bash
# Check if API is running
docker compose ps api

# If it's not running, check logs
docker compose logs api

# Restart it
docker compose restart api
```

### Issue 2: "No scraping method enabled"

**Fix:**
You need to enable at least one scraping method in `.env`:

```bash
nano .env

# Set at least one of these to true:
USE_TWITTERAPIIO=true  # (and set TWITTERAPIIO_API_KEY)
# OR
USE_TWITTER_DIRECT=true  # (and set TWITTER_COOKIES_FILE)

# Restart services
docker compose restart
```

### Issue 3: Browser scraping fails with "Not authenticated"

**Fix:**
You need valid Twitter cookies or credentials:

```bash
# Option 1: Add cookies file
# See HOW_TO_GET_COOKIES.md to export cookies
# Upload twitter_cookies.json to NITTER directory

# Option 2: Add credentials to .env
nano .env
# Set:
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password

# Restart
docker compose restart
```

### Issue 4: "Community requires membership"

**Fix:**
For Twitter Direct scraping, you must join the community first:
1. Log into Twitter with the account whose cookies you're using
2. Visit the community page
3. Click "Join" if you haven't already
4. Wait a few minutes
5. Try scraping again

**OR** use TwitterAPI.io which doesn't require membership for public communities.

### Issue 5: Database errors or "relation does not exist"

**Fix:**
Run database migrations:

```bash
# Run migrations
docker compose exec api alembic upgrade head

# If that doesn't work, recreate database
docker compose down -v
docker compose up -d
```

### Issue 6: Port 8000 already in use

**Fix:**
Change the port in `.env`:

```bash
nano .env

# Change:
API_PORT=8001  # Or any available port

# Restart
docker compose down
docker compose up -d
```

### Issue 7: Out of memory errors

**Fix:**
Disable browser scraping or increase VPS RAM:

```bash
nano .env

# Disable browser scraping (uses less RAM)
USE_TWITTER_DIRECT=false
USE_TWITTERAPIIO=true  # Use API instead

# Restart
docker compose restart
```

---

## 📊 Monitoring Your System

### Check System Status

```bash
# All containers running?
docker compose ps

# How much resources being used?
docker stats

# Recent logs
docker compose logs --tail=50
```

### Check Database

```bash
# Connect to database
docker compose exec postgres psql -U nitter_user -d nitter_db

# Run queries
SELECT COUNT(*) FROM tweets;
SELECT COUNT(*) FROM twitter_users;
SELECT COUNT(*) FROM twitter_communities WHERE is_tracked = true;

# Exit
\q
```

### Check Redis Cache

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check stats
INFO stats

# Exit
exit
```

### Check Background Tasks

```bash
# View worker logs
docker compose logs -f worker

# View scheduler logs
docker compose logs -f beat
```

---

## 🔐 Security Best Practices

### 1. Secure Your .env File

```bash
# Make sure .env is not world-readable
chmod 600 .env

# Never commit .env to git
git update-index --assume-unchanged .env
```

### 2. Use Strong Passwords

```bash
# Generate strong password
openssl rand -base64 32

# Use it for POSTGRES_PASSWORD in .env
```

### 3. Restrict API Access (Production)

```bash
# Use firewall to restrict port 8000
sudo ufw allow from YOUR_IP_ADDRESS to any port 8000

# OR use nginx reverse proxy with authentication
```

### 4. Keep Cookies Secure

```bash
# Restrict cookie file permissions
chmod 600 twitter_cookies.json

# Rotate cookies regularly (every 30 days)
```

---

## 🔄 Maintenance

### Daily

```bash
# Check logs for errors
docker compose logs --tail=100 | grep -i error
```

### Weekly

```bash
# Check disk usage
docker system df

# Clean up old images/containers
docker system prune -a
```

### Monthly

```bash
# Update system
./update.sh

# OR manually:
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
docker compose down
docker compose build
docker compose up -d
```

### Backup Database

```bash
# Backup database
docker compose exec postgres pg_dump -U nitter_user nitter_db > backup-$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T postgres psql -U nitter_user nitter_db < backup-20241113.sql
```

---

## 📚 Next Steps

Now that your system is running, check out:

1. **[COMMUNITY_SCRAPING.md](COMMUNITY_SCRAPING.md)** - How to scrape Twitter communities
2. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Full API reference
3. **[HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)** - Get Twitter cookies for free scraping
4. **[TWITTERAPIIO_SETUP.md](TWITTERAPIIO_SETUP.md)** - Set up fast API scraping
5. **[UPDATE_GUIDE.md](UPDATE_GUIDE.md)** - How to update the system

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `docker compose logs -f`
2. **Check this guide**: Most issues covered above
3. **Check status**: `docker compose ps`
4. **Restart services**: `docker compose restart`
5. **Full restart**: `docker compose down && docker compose up -d`

---

## 📝 Summary - Quick Commands

```bash
# Start system
docker compose up -d

# Stop system
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart

# Update system
./update.sh

# Scrape via CLI
python3 cli.py

# Scrape via API
curl -X POST "http://localhost:8000/api/users/USERNAME/scrape"

# Export data
curl "http://localhost:8000/api/export/csv?username=USERNAME" > tweets.csv
```

---

## ✅ Checklist

Before you start:
- [ ] VPS has Docker installed
- [ ] VPS has 2GB+ RAM
- [ ] Port 8000 is available
- [ ] You have chosen a scraping method

After starting:
- [ ] All 5 containers show "Up" status
- [ ] API responds to health check
- [ ] Test scrape works
- [ ] Logs show no errors

You're all set! 🎉
