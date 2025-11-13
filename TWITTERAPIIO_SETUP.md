# TwitterAPI.io Setup Guide

## What is TwitterAPI.io?

TwitterAPI.io is an **unofficial Twitter API service** that provides access to Twitter data without requiring official Twitter API credentials. It's a paid service but **dramatically cheaper** than Twitter's official API.

### Why Use TwitterAPI.io?

✅ **Much Cheaper** - $0.15 per 1,000 tweets vs $100+/month for official Twitter API
✅ **No Rate Limits** - Unlike Nitter (often blocked) or Twitter Direct (slower)
✅ **Fast & Reliable** - API calls return instantly
✅ **Easy Integration** - Simple REST API with JSON responses
✅ **No Browser Needed** - Unlike Twitter Direct scraping
✅ **Works When Nitter is Blocked** - Independent infrastructure

---

## Pricing Comparison

| Method | Cost | Speed | Reliability | Setup Difficulty |
|--------|------|-------|-------------|-----------------|
| **Nitter** | Free | Fast | ❌ Blocked | Easy |
| **Twitter Direct** | Free | 🐌 Slow | ✅ Good | Medium (cookies) |
| **TwitterAPI.io** | **$0.15/1K tweets** | ⚡ Instant | ✅ Excellent | Very Easy |
| **Official Twitter API** | $100-5000/month | ⚡ Instant | ✅ Excellent | Hard |

### TwitterAPI.io Pricing Tiers

Based on https://twitterapi.io/pricing:

- **Free Tier**: 500 requests/month (great for testing)
- **Starter**: $9/month - 10,000 requests
- **Growth**: $49/month - 100,000 requests
- **Business**: $199/month - 500,000 requests
- **Enterprise**: Custom pricing for higher volumes

**Example calculation:**
- Scraping 100 tweets = 1-2 API requests
- 10,000 requests = scrape ~500,000 tweets
- **Cost: $49/month** vs Twitter's official $100-5000/month

---

## How to Sign Up

### Step 1: Create Account

1. Go to https://twitterapi.io/
2. Click "Sign Up" or "Get Started"
3. Enter your email and create password
4. Verify your email address

### Step 2: Get API Key

1. Login to your TwitterAPI.io dashboard
2. Go to "API Keys" section
3. Click "Create New API Key"
4. Copy your API key (looks like: `api_abc123xyz456...`)
5. **Save it securely** - you won't see it again!

### Step 3: Test Your API Key (Optional)

Test with curl:

```bash
curl -X GET "https://api.twitterapi.io/users/by/username/twitter" \
  -H "x-api-key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json"
```

You should see Twitter's profile data in JSON format.

---

## Configuration

### Step 1: Edit .env File

```bash
cd ~/NITTER
nano .env
```

Add these lines:

```bash
# TwitterAPI.io Configuration
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key from Step 2.

### Step 2: Rebuild Docker Containers

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

Wait 20 seconds for services to start:

```bash
sleep 20
```

---

## Testing

### Test 1: Scrape a Profile

```bash
curl -X POST http://localhost:8000/api/users/elonmusk/scrape
```

Expected response:
```json
{
  "status": "success",
  "message": "Scraping job started",
  "job_id": "..."
}
```

### Test 2: Check Job Status

Wait 10 seconds, then:

```bash
curl http://localhost:8000/api/jobs/recent?limit=1
```

Expected result:
```json
{
  "jobs": [
    {
      "job_id": "...",
      "status": "completed",
      "items_scraped": 1,
      "duration": 0.5
    }
  ]
}
```

✅ **Success if `items_scraped: 1`** - TwitterAPI.io is working!

### Test 3: Verify Profile Data

```bash
curl http://localhost:8000/api/users/elonmusk
```

You should see the full profile data with followers count, bio, etc.

### Test 4: Scrape Timeline

```bash
curl -X POST http://localhost:8000/api/users/elonmusk/timeline/scrape
```

Wait 15 seconds:

```bash
sleep 15
curl http://localhost:8000/api/jobs/recent?limit=1
```

Should show `items_scraped: 100` (or however many tweets were found).

---

## How It Works

### Scraping Priority Order

The system now uses a **3-tier fallback strategy**:

1. **TwitterAPI.io** (if enabled) - Fastest, most reliable
2. **Twitter Direct** (if cookies/credentials set) - Free but slower
3. **Nitter** (always tried last) - Free but often blocked

### Automatic Fallback

If TwitterAPI.io fails (e.g., rate limit hit, API down), the system automatically tries:
- Twitter Direct (if you have cookies set)
- Nitter instances (as last resort)

This ensures **maximum reliability** - you always get data!

### Logs

Check which method was used:

```bash
docker compose logs -f api | grep "Using"
```

You'll see:
- `Using TwitterAPI.io for elonmusk` ✅
- `Using Twitter Direct scraper for elonmusk` (fallback)
- `Using Nitter scraper for elonmusk` (last resort)

---

## API Endpoints Used

TwitterAPI.io provides several endpoints we use:

### 1. Get User Profile
```
GET /users/by/username/{username}
```

Returns: User profile data (bio, followers, etc.)

### 2. Get User Tweets
```
GET /users/{user_id}/tweets
```

Parameters:
- `max_results`: Number of tweets (1-100)
- `tweet.fields`: Additional data to include

Returns: List of user's tweets

### 3. Search Tweets
```
GET /tweets/search/recent
```

Parameters:
- `query`: Search query
- `max_results`: Number of results (1-100)

Returns: Tweets matching the search query

See full API docs: https://docs.twitterapi.io/

---

## Cost Management

### Monitor Usage

1. Login to https://twitterapi.io/dashboard
2. Check "Usage" section
3. See requests used this month

### Set Budget Alerts

1. Go to "Settings" → "Notifications"
2. Set alert at 80% of monthly limit
3. Get email when approaching limit

### Optimize Costs

**Tip 1: Use Free Methods First**

In `.env`, set priority:
```bash
USE_TWITTER_DIRECT=true        # Try free method first
TWITTER_COOKIES_FILE=twitter_cookies.json

USE_TWITTERAPIIO=false         # Only as fallback
TWITTERAPIIO_API_KEY=...
```

TwitterAPI.io will only be used if Twitter Direct fails.

**Tip 2: Reduce Scraping Frequency**

For tracked users, increase check interval:
```bash
# Check every 6 hours instead of 15 minutes
curl -X POST http://localhost:8000/api/users/elonmusk/track \
  -H "Content-Type: application/json" \
  -d '{"interval": 21600}'
```

**Tip 3: Scrape Only When Needed**

Use on-demand scraping instead of continuous tracking:
```bash
# Only scrape when you need fresh data
curl -X POST http://localhost:8000/api/users/elonmusk/scrape
```

---

## Troubleshooting

### Error: "Invalid API Key"

**Problem:** API key is incorrect or expired

**Solution:**
1. Go to https://twitterapi.io/dashboard
2. Check "API Keys" section
3. Generate new key if needed
4. Update `.env` with correct key
5. Rebuild containers: `docker compose down && docker compose up -d`

### Error: "Rate Limit Exceeded"

**Problem:** You've hit your monthly request limit

**Solutions:**
1. Wait until next month (free tier resets)
2. Upgrade plan at https://twitterapi.io/pricing
3. Use Twitter Direct as fallback (set `USE_TWITTER_DIRECT=true`)

### Error: "Timeout"

**Problem:** API request took too long

**Solution:** This is rare but can happen. The system will automatically retry with fallback methods.

### Jobs Complete but `items_scraped: 0`

**Problem:** TwitterAPI.io returned no data

**Check:**
1. Is the username correct? Try `@elonmusk` or other popular account
2. Is the account suspended/private?
3. Check API dashboard for errors

**Solution:**
```bash
# Check logs for specific error
docker compose logs api | grep -i "error\|failed"

# Try with fallback method
echo "USE_TWITTER_DIRECT=true" >> .env
echo "TWITTER_COOKIES_FILE=twitter_cookies.json" >> .env
docker compose restart api
```

### High Costs

**Problem:** Burning through requests too fast

**Solutions:**
1. Reduce tracked users:
   ```bash
   curl -X DELETE http://localhost:8000/api/users/{username}/track
   ```

2. Increase scraping intervals (see Cost Management above)

3. Switch to free method as primary:
   ```bash
   # In .env
   USE_TWITTER_DIRECT=true
   USE_TWITTERAPIIO=false  # Only as fallback
   ```

---

## Comparison: All Methods

### When to Use Each Method

| Use Case | Best Method | Why |
|----------|-------------|-----|
| **Testing/Development** | TwitterAPI.io Free Tier | 500 free requests/month |
| **Low Volume (<10K tweets/month)** | Twitter Direct + Cookies | Free, no costs |
| **Medium Volume (10K-100K tweets/month)** | TwitterAPI.io Starter ($9-49) | Fast, reliable, cheap |
| **High Volume (100K+ tweets/month)** | TwitterAPI.io + Twitter Direct Hybrid | Use free when possible, API when needed |
| **Budget = $0** | Twitter Direct + Cookies only | 100% free |
| **Need Maximum Speed** | TwitterAPI.io | Instant API responses |

### Performance Comparison

**Time to scrape 100 tweets:**

- **Nitter**: 5-10 seconds (when working) ❌ Currently blocked
- **Twitter Direct**: 30-60 seconds (browser automation)
- **TwitterAPI.io**: 0.5-2 seconds ⚡ Fastest!
- **Official Twitter API**: 0.5-2 seconds (but $100-5000/month)

---

## Advanced: Hybrid Configuration

### Best of Both Worlds

Use TwitterAPI.io for important/time-sensitive scrapes, Twitter Direct for everything else:

```bash
# .env configuration
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json

USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_key_here
```

**How it works:**
1. System tries TwitterAPI.io first (fast!)
2. If API limit hit → falls back to Twitter Direct (free!)
3. If Twitter Direct fails → tries Nitter (last resort)

**Result:** You get speed when needed, but don't waste API credits on bulk scraping.

### Per-User Configuration (Future Enhancement)

Coming soon - ability to specify which method per user:
- VIP users → Always use TwitterAPI.io (fast)
- Regular users → Use Twitter Direct (free)

---

## FAQ

### Q: Is TwitterAPI.io legal?

A: TwitterAPI.io is an unofficial service. Review Twitter's Terms of Service and use responsibly. This tool is for research/personal use.

### Q: Can I use the free tier forever?

A: Yes! The free tier gives you 500 requests/month permanently. Perfect for small projects.

### Q: What happens if I run out of credits?

A: The system automatically falls back to Twitter Direct (cookies) or Nitter. Your scraping continues, just slower.

### Q: Is my API key secure?

A: Yes, it's stored in `.env` which should NEVER be committed to Git. Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

### Q: Can I share my API key with teammates?

A: Yes, but be careful - you share the same rate limit. Consider getting separate keys or a team plan.

### Q: Does this work with private accounts?

A: No, TwitterAPI.io can only access public data. For private accounts, use Twitter Direct with cookies from an authorized account.

---

## Summary

### Quick Setup (2 minutes)

1. Sign up at https://twitterapi.io/
2. Get API key from dashboard
3. Add to `.env`:
   ```bash
   USE_TWITTERAPIIO=true
   TWITTERAPIIO_API_KEY=your_key_here
   ```
4. Rebuild: `docker compose down && docker compose up -d`
5. Test: `curl -X POST http://localhost:8000/api/users/twitter/scrape`

### Recommended Configuration

**For maximum reliability and low cost:**

```bash
# Try free method first
USE_TWITTER_DIRECT=true
TWITTER_COOKIES_FILE=twitter_cookies.json

# Fallback to paid API if needed
USE_TWITTERAPIIO=true
TWITTERAPIIO_API_KEY=your_key_here
```

This gives you:
- ✅ **Free** scraping when Twitter Direct works
- ✅ **Fast** fallback when you need speed
- ✅ **Reliable** - always get data

---

## Support

- **TwitterAPI.io Docs**: https://docs.twitterapi.io/
- **TwitterAPI.io Support**: support@twitterapi.io
- **Pricing**: https://twitterapi.io/pricing
- **Status Page**: https://status.twitterapi.io/

For issues with this integration, check the logs:
```bash
docker compose logs -f api
```

---

## Next Steps

1. ✅ Sign up for TwitterAPI.io (free tier to start)
2. ✅ Configure `.env` with API key
3. ✅ Test with a scrape job
4. 📊 Monitor usage in dashboard
5. 🚀 Scale up as needed

**Happy scraping!** 🎉
