# Quick Start Guide - TL;DR Version

For people who just want to get started FAST. Full guide: [GETTING_STARTED.md](GETTING_STARTED.md)

---

## ⚡ 1-Minute Setup

```bash
# Clone and configure
git clone <repo-url> NITTER && cd NITTER
cp .env.example .env
nano .env  # Add your API key OR cookies (see below)

# Start
docker compose up -d

# Test
python3 cli.py
```

Done! ✅

---

## 🔑 Configuration (Choose ONE)

### Option A: FREE (Need Twitter account)

```bash
# In .env:
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json
```

Get cookies: [HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)

### Option B: FAST (No Twitter account needed)

```bash
# In .env:
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_key_here
```

Get key: https://twitterapi.io (free tier available)

---

## 🎯 Common Commands

```bash
# Start/Stop
docker compose up -d          # Start all services
docker compose down           # Stop all services
docker compose restart        # Restart services

# Check Status
docker compose ps             # Are services running?
docker compose logs -f api    # View API logs
docker compose logs -f worker # View worker logs

# Update
./update.sh                   # Pull latest code & restart

# Scraping
python3 cli.py                # Interactive CLI
curl -X POST "http://localhost:8000/api/users/elonmusk/scrape"

# Export
curl "http://localhost:8000/api/export/csv?username=elonmusk" > tweets.csv
```

---

## 🏘️ Scrape Communities

```bash
# Find community ID from URL:
# https://twitter.com/i/communities/1234567890
#                                   ^^^^^^^^^^^ This is the ID

# Scrape ALL tweets from a community:
curl -X POST "http://localhost:8000/api/communities/COMMUNITY_ID/scrape"

# Export to CSV:
curl "http://localhost:8000/api/export/csv?community_id=COMMUNITY_ID" > community.csv
```

Full guide: [COMMUNITY_SCRAPING.md](COMMUNITY_SCRAPING.md)

---

## 🐛 Troubleshooting

```bash
# Not working? Try these:
docker compose ps              # All services "Up"?
docker compose logs api        # Any errors?
docker compose restart         # Restart everything

# Still not working?
docker compose down -v         # Nuclear option: delete everything
docker compose up -d           # Start fresh
```

---

## 📚 Full Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Complete step-by-step guide
- **[COMMUNITY_SCRAPING.md](COMMUNITY_SCRAPING.md)** - Scrape Twitter communities
- **[SCRAPING_METHODS_EXPLAINED.md](SCRAPING_METHODS_EXPLAINED.md)** - Free vs Paid
- **[UPDATE_GUIDE.md](UPDATE_GUIDE.md)** - How to update
- **[HOW_TO_GET_COOKIES.md](HOW_TO_GET_COOKIES.md)** - Free scraping setup

---

That's it! You're ready to scrape. 🚀
