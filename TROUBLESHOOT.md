# Troubleshooting Scraping Failures

## Quick Diagnosis Commands

Run these commands on your VPS to diagnose the issue:

### 1. Check Container Status
```bash
docker compose ps
```

**Expected:** All 6 containers should show "Up"
- nitter_api
- nitter_celery_worker
- nitter_celery_beat
- nitter_postgres
- nitter_redis
- nitter_nginx

**If any show "Exited":** That container crashed

---

### 2. Check Celery Worker Logs (Most Important)
```bash
docker compose logs celery_worker --tail=100
```

**Look for:**
- ❌ "playwright" errors → Playwright installation issue
- ❌ "NitterInstance" errors → Nitter instances are down
- ❌ "Database" errors → Database connection issue
- ❌ "timeout" errors → Network or Nitter instance is slow

---

### 3. Check API Logs
```bash
docker compose logs api --tail=50
```

**Look for:**
- ❌ "500 Internal Server Error"
- ❌ Database connection errors
- ❌ Import errors

---

### 4. Check if Database Tables Exist
```bash
docker compose exec api python -c "from src.utils.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

**Expected:** Should list: `['twitter_users', 'tweets', 'search_queries', 'scraping_jobs', 'webhooks']`

**If empty:** Database tables weren't created

---

### 5. Test API Health
```bash
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy", "version": "1.0.0"}`

**If fails:** API isn't running

---

### 6. Check Recent Jobs
```bash
curl http://localhost:8000/api/jobs/recent?limit=5
```

**Look for:**
- Jobs with `"status": "failed"`
- Check `"error_message"` field

---

## Common Issues & Fixes

### Issue 1: Playwright Not Installed

**Symptoms:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Fix:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

### Issue 2: All Nitter Instances Down

**Symptoms:**
```
No healthy Nitter instances available
```

**Explanation:** Nitter instances go down frequently. The scraper tries 20+ instances.

**Check Instance Health:**
```bash
curl http://localhost:8000/api/dashboard/instance-health
```

**Fix:** Wait 5 minutes for health checker to find working instances, or manually test instances:
```bash
# Test a few Nitter instances manually
curl -I https://nitter.net
curl -I https://nitter.poast.org
curl -I https://nitter.privacydev.net
```

---

### Issue 3: Database Connection Failed

**Symptoms:**
```
could not connect to server: Connection refused
sqlalchemy.exc.OperationalError
```

**Check PostgreSQL:**
```bash
docker compose logs postgres --tail=30
docker compose exec postgres pg_isready -U nitter_user
```

**Fix:**
```bash
docker compose restart postgres
sleep 5
docker compose restart api celery_worker
```

---

### Issue 4: Redis Connection Failed

**Symptoms:**
```
Error connecting to Redis
ConnectionError
```

**Check Redis:**
```bash
docker compose logs redis --tail=20
docker compose exec redis redis-cli ping
```

**Expected:** Should return `PONG`

**Fix:**
```bash
docker compose restart redis
sleep 5
docker compose restart celery_worker celery_beat
```

---

### Issue 5: Playwright Browser Crashed

**Symptoms:**
```
Protocol error (Browser.close): Browser closed
Target closed
```

**Fix:**
```bash
# Increase container memory limits
# Edit docker-compose.yml and add under celery_worker:
# deploy:
#   resources:
#     limits:
#       memory: 2G

docker compose down
docker compose up -d
```

---

### Issue 6: Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Fix:**
```bash
# Fix logs directory permissions
sudo chown -R $USER:$USER ~/NITTER/logs
chmod -R 755 ~/NITTER/logs

docker compose restart api celery_worker
```

---

### Issue 7: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'xxx'
ImportError: cannot import name 'xxx'
```

**Fix:**
```bash
# Rebuild containers with fresh dependencies
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Step-by-Step Diagnosis

### Step 1: Are containers running?
```bash
docker compose ps
```

If not all "Up":
```bash
docker compose up -d
docker compose ps
```

---

### Step 2: Can you reach the API?
```bash
curl http://localhost:8000/health
```

If fails:
```bash
docker compose logs api --tail=50
docker compose restart api
```

---

### Step 3: Are Nitter instances healthy?
```bash
curl http://localhost:8000/api/dashboard/instance-health
```

Should show at least 1-2 healthy instances.

If all unhealthy, wait 5 minutes for health check to run.

---

### Step 4: Try a manual scrape
```bash
curl -X POST http://localhost:8000/api/users/twitter/scrape
```

Wait 30 seconds, then check job status:
```bash
curl http://localhost:8000/api/jobs/recent?limit=1
```

Look at the response to see if job succeeded or failed.

---

### Step 5: Watch worker logs in real-time
```bash
docker compose logs -f celery_worker
```

Then in another terminal, trigger a scrape:
```bash
curl -X POST http://localhost:8000/api/users/elonmusk/scrape
```

Watch the logs to see what error occurs.

---

## Full Reset (Nuclear Option)

If nothing works, completely reset:

```bash
# Stop everything
docker compose down -v

# Remove all containers and images
docker system prune -a --volumes

# Rebuild from scratch
./run.sh

# Wait for startup
sleep 30

# Test
curl http://localhost:8000/health
python3 cli.py
```

---

## Get Detailed Error Info

### See FULL worker logs:
```bash
docker compose logs celery_worker --tail=500 > worker_logs.txt
cat worker_logs.txt
```

### See FULL api logs:
```bash
docker compose logs api --tail=500 > api_logs.txt
cat api_logs.txt
```

### Check database logs:
```bash
docker compose logs postgres --tail=200
```

---

## Test Nitter Instances Manually

Some Nitter instances go down. Test them manually:

```bash
# Test multiple instances
curl -I https://nitter.net
curl -I https://nitter.poast.org
curl -I https://nitter.privacydev.net
curl -I https://nitter.woodland.cafe
curl -I https://nitter.1d4.us
```

If ALL return errors, Nitter might be having global issues. Wait and try later.

---

## Check System Resources

### Memory usage:
```bash
free -h
```

If low memory:
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Disk space:
```bash
df -h
```

If low disk:
```bash
# Clean Docker
docker system prune -a
```

### CPU usage:
```bash
top
```

Press 'q' to quit.

---

## Common Error Messages Decoded

### "playwright._impl._api_types.Error"
→ Playwright not installed properly
→ Fix: Rebuild containers

### "No healthy Nitter instances available"
→ All Nitter instances are down
→ Fix: Wait 5 minutes, instances rotate automatically

### "could not connect to server"
→ PostgreSQL isn't running
→ Fix: Check postgres container

### "Connection refused" (Redis)
→ Redis isn't running
→ Fix: Check redis container

### "Target closed" or "Browser closed"
→ Browser crashed (usually memory)
→ Fix: Add more memory or reduce concurrent workers

### "IntegrityError: duplicate key"
→ Trying to insert duplicate data
→ Fix: This is normal, scraper handles it

### "TimeoutError"
→ Nitter instance is slow
→ Fix: Instance manager will rotate to faster one

---

## What to Share for Help

If you need help, share:

1. **Container status:**
```bash
docker compose ps
```

2. **Last 100 lines of worker logs:**
```bash
docker compose logs celery_worker --tail=100
```

3. **API health:**
```bash
curl http://localhost:8000/health
```

4. **Recent job status:**
```bash
curl http://localhost:8000/api/jobs/recent?limit=3
```

5. **System info:**
```bash
free -h
df -h
docker --version
docker compose version
```

---

## Success Indicators

You'll know it's working when:

✅ All 6 containers show "Up"
✅ `curl http://localhost:8000/health` returns healthy
✅ Worker logs show "Successfully completed ... scrape job"
✅ `curl http://localhost:8000/api/jobs/recent` shows completed jobs
✅ CLI shows tweets when you view them

---

## Quick Test Command

Test if scraping works end-to-end:

```bash
# Trigger scrape
echo "Triggering scrape..."
curl -X POST http://localhost:8000/api/users/twitter/scrape

# Wait for job
echo "Waiting 60 seconds for scraping..."
sleep 60

# Check result
echo "Checking result..."
curl http://localhost:8000/api/tweets/user/twitter?limit=5

# Should see tweets!
```

If you see tweets, it's working! 🎉
