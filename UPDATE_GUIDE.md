# How to Update NITTER on Your VPS

This guide shows you how to pull the latest changes and update your VPS deployment.

## Quick Update (Easiest)

```bash
# On your VPS
cd /path/to/NITTER
./update.sh
```

That's it! The script will:
1. Pull latest code from git
2. Install new dependencies
3. Run database migrations
4. Restart all services

---

## Manual Update (Step by Step)

If you prefer to update manually:

### 1. Pull Latest Code

```bash
cd /path/to/NITTER

# Pull latest changes
git fetch origin
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
```

### 2. Update Dependencies (if needed)

```bash
# If containers are running
docker compose exec api pip install -r requirements.txt

# OR rebuild if major changes
docker compose build api
```

### 3. Run Database Migrations

```bash
# Apply any new database changes
docker compose exec api alembic upgrade head
```

### 4. Restart Services

```bash
# Restart all services
docker compose restart

# OR restart individual services
docker compose restart api worker beat
```

### 5. Verify Everything Works

```bash
# Check service status
docker compose ps

# Check logs
docker compose logs -f api

# Test scraping
python3 cli.py
```

---

## Common Update Scenarios

### Scenario 1: Adding New Features (like Community Scraping)

```bash
# 1. Pull latest code
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ

# 2. Run migrations (adds new database tables)
docker compose exec api alembic upgrade head

# 3. Restart services
docker compose restart

# 4. Test new feature
curl -X POST http://localhost:8000/api/communities/COMMUNITY_ID/scrape
```

### Scenario 2: Configuration Changes Only

```bash
# 1. Pull latest code
git pull

# 2. Update .env if needed (check .env.example for new variables)
nano .env

# 3. Restart services
docker compose restart
```

### Scenario 3: Dependency Updates

```bash
# 1. Pull latest code
git pull

# 2. Rebuild containers (includes new dependencies)
docker compose down
docker compose build
docker compose up -d
```

### Scenario 4: Major Version Update

```bash
# 1. Backup database first!
docker compose exec postgres pg_dump -U nitter_user nitter_db > backup.sql

# 2. Pull latest code
git pull

# 3. Rebuild everything
docker compose down
docker compose build
docker compose up -d

# 4. Run migrations
docker compose exec api alembic upgrade head
```

---

## Checking What's New

### View Recent Commits

```bash
# See what changed
git log --oneline -10

# See detailed changes
git log -p -5
```

### View Changelog

Check these files for details on what's new:
- `FIXES_APPLIED.md` - Recent fixes and improvements
- `COMMUNITY_SCRAPING.md` - New community scraping feature
- `README.md` - Updated feature list

---

## Troubleshooting Updates

### Problem: Git Pull Fails (Merge Conflicts)

```bash
# If you have local changes that conflict
git stash                # Save your local changes
git pull                 # Pull latest code
git stash pop            # Restore your changes
# Manually resolve conflicts
```

### Problem: Services Won't Start After Update

```bash
# Check logs
docker compose logs api

# Try rebuilding
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Problem: Database Migration Fails

```bash
# Check migration status
docker compose exec api alembic current

# Try running migrations manually
docker compose exec api alembic upgrade head

# If still fails, check logs
docker compose logs api | grep -i alembic
```

### Problem: "Module Not Found" Error

```bash
# Rebuild containers with fresh dependencies
docker compose down
docker compose build --no-cache api
docker compose up -d
```

---

## Automatic Updates (Optional)

You can set up automatic updates with a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to update daily at 3 AM
0 3 * * * cd /path/to/NITTER && ./update.sh >> /var/log/nitter-update.log 2>&1
```

**⚠️ Warning**: Only do this if you trust automatic updates. Manual updates are safer.

---

## Rolling Back (If Something Breaks)

### Rollback to Previous Version

```bash
# See recent commits
git log --oneline -10

# Rollback to specific commit
git checkout COMMIT_HASH

# Restart services
docker compose restart

# If you want to stay at old version
git checkout -b old-stable
```

### Restore from Backup

```bash
# Restore database
docker compose exec -T postgres psql -U nitter_user nitter_db < backup.sql

# Restore code
git checkout PREVIOUS_COMMIT
docker compose restart
```

---

## Update Checklist

Before updating:
- ✅ Backup database (important!)
- ✅ Check current system is working
- ✅ Read FIXES_APPLIED.md for breaking changes
- ✅ Note current commit: `git rev-parse HEAD`

After updating:
- ✅ Check service status: `docker compose ps`
- ✅ Check logs: `docker compose logs -f`
- ✅ Test scraping: Use CLI or API
- ✅ Verify new features work

---

## Getting Help

If you encounter issues:
1. Check logs: `docker compose logs api`
2. Check service status: `docker compose ps`
3. Check TROUBLESHOOT.md
4. Check recent commits: `git log -p -5`
5. Ask for help with error messages

---

## Summary

**Easiest way to update:**
```bash
./update.sh
```

**Manual way:**
```bash
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
docker compose exec api alembic upgrade head
docker compose restart
```

**Full rebuild (if needed):**
```bash
docker compose down
git pull
docker compose build
docker compose up -d
```
