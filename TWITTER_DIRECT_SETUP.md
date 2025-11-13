# Twitter Direct Scraping Setup (No API Required!)

## What This Does

Scrapes Twitter.com directly using browser automation - **no Twitter API needed!**

### How It Works:
1. Logs into Twitter.com with your account
2. Navigates to profiles and extracts data
3. Works just like Nitter but more reliable
4. Same database, API, CLI - everything stays the same

---

## Setup (5 Minutes)

### Step 1: Create a Twitter Account (If You Don't Have One)

1. Go to https://twitter.com/signup
2. Create a free account
3. Complete verification (email/phone)
4. **Important:** Don't use your main account - create a dedicated scraping account

### Step 2: Configure Credentials

```bash
cd ~/NITTER

# Edit .env file
nano .env

# Add these lines (or update if they exist):
USE_TWITTER_DIRECT=true
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password
```

**Example:**
```
USE_TWITTER_DIRECT=true
TWITTER_USERNAME=scraper_bot_123
TWITTER_PASSWORD=MySecureP@ssword123
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 3: Rebuild and Restart

```bash
# Stop containers
docker compose down

# Rebuild with new code
docker compose build --no-cache

# Start
docker compose up -d

# Wait for startup
sleep 15

# Check logs
docker compose logs -f celery_worker
```

---

## Test It

```bash
# Test profile scraping
curl -X POST http://localhost:8000/api/users/elonmusk/scrape

# Wait 30 seconds
sleep 30

# Check if it worked
curl http://localhost:8000/api/jobs/recent?limit=1

# Should see:
# "status": "completed"
# "items_scraped": 100  (not 0!)
```

---

## How It Works

### Without Credentials (Nitter Only):
```
User requests scrape → Try Nitter → 403 Error → Failed
```

### With Credentials (Hybrid Mode):
```
User requests scrape → Try Nitter first → If fails → Use Twitter Direct → Success!
```

### With USE_TWITTER_DIRECT=true:
```
User requests scrape → Use Twitter Direct immediately → Success!
```

---

## Advantages

✅ **Free** - No API costs
✅ **Reliable** - Twitter.com always works
✅ **More Data** - Get full profiles and tweets
✅ **No Rate Limits** - (within reason, don't spam)
✅ **Same Interface** - CLI, API, database all work the same

## Disadvantages

⚠️ **Slower** - Loads full web pages (3-5 seconds per profile)
⚠️ **Needs Account** - Must have Twitter login
⚠️ **Risk of Ban** - If you scrape too aggressively
⚠️ **Login Required** - One-time setup needed

---

## Best Practices

### 1. Use a Dedicated Account
- Don't use your personal Twitter
- Create "scraper_bot_xxx" account
- Use temporary email if needed

### 2. Be Reasonable with Scraping
```
✅ Good: Track 10-50 accounts, check hourly
❌ Bad: Track 1000 accounts, check every minute
```

### 3. Set Reasonable Intervals
```bash
# In CLI, when tracking users:
Check interval: 3600  # 1 hour - GOOD
Check interval: 60    # 1 minute - TOO AGGRESSIVE
```

### 4. Monitor for Errors
```bash
# Check if account gets rate limited
docker compose logs celery_worker | grep -i "rate limit\|suspended"
```

---

## Troubleshooting

### "Login failed"

**Check:**
1. Username/password correct in .env
2. Account not suspended
3. Twitter didn't prompt for verification

**Fix:**
```bash
# Test login manually
docker compose exec api python3 << 'PYTHON'
from src.scrapers.twitter_direct_scraper import TwitterDirectScraper
from src.nitter_manager import NitterInstanceManager
import asyncio

async def test():
    manager = NitterInstanceManager()
    async with TwitterDirectScraper(manager, "YOUR_USERNAME", "YOUR_PASSWORD") as scraper:
        success = await scraper.login()
        print(f"Login success: {success}")

asyncio.run(test())
PYTHON
```

### "Account suspended"

Your Twitter account got flagged. This happens if:
- Scraping too aggressively
- New account with suspicious activity
- Using VPN/proxy

**Fix:**
1. Create new Twitter account
2. Wait 24 hours before scraping
3. Reduce scraping frequency

### "Still getting 0 items"

**Check:**
```bash
# 1. Is USE_TWITTER_DIRECT enabled?
cat .env | grep USE_TWITTER_DIRECT

# Should show: USE_TWITTER_DIRECT=true

# 2. Are credentials set?
cat .env | grep TWITTER_

# Should show your username/password

# 3. Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Security

### Protecting Your Credentials

1. **Never commit .env to Git**
```bash
# Already in .gitignore, but double-check
cat .gitignore | grep ".env"
```

2. **Use Strong Password**
```
❌ Bad: password123
✅ Good: Xk9$mP2@vL4^nQ8
```

3. **Enable 2FA on Account**
- If Twitter prompts for 2FA, disable it for scraper account
- Or handle verification codes manually

---

## Comparison

### Nitter (When It Works):
- Speed: ⚡ Fast (1-2 seconds)
- Reliability: ❌ Currently blocked
- Setup: ✅ Easy (no login)
- Cost: ✅ Free

### Twitter Direct (This Solution):
- Speed: 🐌 Slower (3-5 seconds)
- Reliability: ✅ Works now
- Setup: ⚠️ Medium (need account)
- Cost: ✅ Free

### Twitter API:
- Speed: ⚡ Fast (1-2 seconds)
- Reliability: ✅ Always works
- Setup: ❌ Complex (apply for access)
- Cost: ❌ $100-5000/month

---

## Example Usage

### Track Users:
```bash
python3 cli.py

# Choose: 1 (Track user)
# Username: elonmusk
# Interval: 3600 (1 hour)

# It will:
# 1. Login to Twitter with your account
# 2. Navigate to @elonmusk profile
# 3. Extract profile data
# 4. Scroll and get tweets
# 5. Save to database
# 6. Check again in 1 hour
```

### One-Time Scrape:
```bash
python3 cli.py

# Choose: 2 (Scrape user now)
# Username: twitter

# Gets:
# - Profile: bio, followers, following
# - Tweets: last 100 tweets
# - Media: images/videos
# - Engagement: likes, retweets, replies
```

---

## Performance

### Expected Times:
- Login: 5-10 seconds (once per session)
- Profile scrape: 3-5 seconds
- Timeline scrape (100 tweets): 20-30 seconds
- Search: 30-60 seconds

### Resource Usage:
- CPU: ~20-30% during scraping
- RAM: ~500MB per worker
- Disk: Minimal (just database)

---

## Monitoring

### Check If It's Working:
```bash
# Watch live scraping
docker compose logs -f celery_worker

# Should see:
# "Logging in to Twitter..."
# "Successfully logged in to Twitter"
# "Scraping Twitter profile: elonmusk"
# "Successfully scraped Twitter profile: elonmusk"
# "Successfully scraped 100 tweets"
```

### Check Success Rate:
```bash
curl http://localhost:8000/api/jobs/stats/summary

# Should show:
# "completed": > 0
# "items_scraped": > 0
```

---

## Switching Back to Nitter

If Nitter instances come back online:

```bash
# Edit .env
nano .env

# Change:
USE_TWITTER_DIRECT=false

# Restart
docker compose restart celery_worker celery_beat
```

Or keep both (hybrid mode):
```bash
USE_TWITTER_DIRECT=false  # Try Nitter first
TWITTER_USERNAME=...      # Fallback to direct if Nitter fails
TWITTER_PASSWORD=...
```

---

## FAQ

**Q: Will my account get banned?**
A: Possibly if you scrape too much. Use reasonable intervals and don't spam.

**Q: Can I use my main Twitter account?**
A: Not recommended. Create a dedicated scraping account.

**Q: Does this violate Twitter's TOS?**
A: Yes, technically. Use at your own risk for research/personal projects.

**Q: How many accounts can I track?**
A: 10-50 accounts safely. More may trigger rate limits.

**Q: Can I scrape without logging in?**
A: No, Twitter requires login to view profiles now.

**Q: Is this better than Nitter?**
A: More reliable now that Nitter is blocked, but slower.

---

## Success Indicators

You'll know it's working when:

✅ Logs show "Successfully logged in to Twitter"
✅ Jobs show "completed" status
✅ "items_scraped" is > 0
✅ Tweets appear in database
✅ CLI shows tweet data

---

## Next Steps

1. **Set up credentials** (2 minutes)
2. **Rebuild containers** (3 minutes)
3. **Test with one user** (1 minute)
4. **Add more users to track** (ongoing)
5. **Monitor for issues** (daily)

---

## Support

If it's not working:

1. Check logs: `docker compose logs celery_worker | tail -100`
2. Verify credentials: `cat .env | grep TWITTER`
3. Test login manually (see Troubleshooting section)
4. Check Twitter account isn't suspended

---

**You now have a working Twitter scraper that doesn't need API keys!** 🎉

Just add your credentials, rebuild, and start scraping!
