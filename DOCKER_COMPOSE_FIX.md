# Docker Compose Compatibility Fix

## Problem

You're experiencing this error when running `./run.sh`:

```
TypeError: HTTPConnection.request() got an unexpected keyword argument 'chunked'
```

**Cause:** Your VPS has Docker Compose v1.29.2 (Python-based, legacy) which is incompatible with urllib3 v2.5.0.

---

## Solution: Upgrade to Docker Compose v2

Docker Compose v2 is the modern, standalone version written in Go. It's faster, more reliable, and doesn't have Python dependency issues.

### Step 1: Install Docker Compose v2

Run these commands on your VPS:

```bash
# Remove old docker-compose v1 (optional but recommended)
sudo apt-get remove docker-compose

# Download and install Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose version
```

You should see output like: `Docker Compose version v2.x.x`

### Step 2: Alternative - Use Docker Plugin

If you have Docker Engine 20.10+, you already have Compose v2 as a plugin:

```bash
# Check if it's available
docker compose version

# If it works, you're all set!
```

If `docker compose` works, you can use it directly instead of `docker-compose`.

### Step 3: Pull Latest Code and Run

```bash
cd ~/NITTER
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ
chmod +x run.sh
./run.sh
```

The updated `run.sh` script now automatically detects and uses the correct Docker Compose version.

---

## Quick Fix (If You Can't Upgrade)

If you can't upgrade Docker Compose right now, downgrade urllib3:

```bash
# Downgrade urllib3 to compatible version
sudo pip3 install 'urllib3<2.0'

# Then run the script
./run.sh
```

**Note:** This is a temporary workaround. Upgrading to Docker Compose v2 is the better solution.

---

## Verification

After upgrading, verify everything works:

```bash
# Check Docker Compose version
docker compose version

# Or
docker-compose version

# Should show v2.x.x or higher

# Run the scraper
./run.sh

# Check services are running
docker compose ps
```

Expected output:
```
NAME                   IMAGE              STATUS
nitter_api             ...                Up
nitter_celery_beat     ...                Up
nitter_celery_worker   ...                Up
nitter_nginx           ...                Up
nitter_postgres        ...                Up
nitter_redis           ...                Up
```

---

## Why Docker Compose v2?

**Docker Compose v1 (legacy):**
- Python-based
- Requires Python dependencies (causes conflicts like this)
- No longer actively maintained
- Command: `docker-compose`

**Docker Compose v2 (modern):**
- Standalone Go binary
- No Python dependencies
- Actively maintained by Docker
- Faster and more reliable
- Command: `docker compose` (space, not hyphen)
- Backward compatible with v1 configs

---

## Manual Installation (Detailed)

If the quick commands above don't work, follow these detailed steps:

### For Ubuntu/Debian:

```bash
# Update package list
sudo apt-get update

# Install prerequisites
sudo apt-get install -y curl

# Get latest version number
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)

# Download Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink (optional)
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify
docker-compose version
```

### For systems with Docker Engine 20.10+:

```bash
# Install as Docker CLI plugin
mkdir -p ~/.docker/cli-plugins/
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# Verify
docker compose version
```

---

## Troubleshooting

### Error: "docker-compose: command not found" after upgrade

```bash
# Check installation location
which docker-compose

# If empty, ensure it's in your PATH
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or create symlink
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

### Error: "Permission denied" when downloading

```bash
# Use sudo for the curl command
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

### Error: Still getting urllib3 errors

```bash
# Clear Python cache
sudo rm -rf /usr/lib/python3/dist-packages/urllib3/__pycache__
sudo rm -rf /usr/local/lib/python3.10/dist-packages/urllib3/__pycache__

# Verify Docker Compose v2 is being used
docker-compose version  # Should show v2.x.x

# Force use Docker Compose v2
docker compose up -d  # Use "compose" not "compose"
```

---

## Updated Commands

After upgrading, you can use either:

### Docker Compose v2 (plugin style):
```bash
docker compose up -d
docker compose down
docker compose ps
docker compose logs -f
```

### Docker Compose v2 (standalone):
```bash
docker-compose up -d
docker-compose down
docker-compose ps
docker-compose logs -f
```

Both work with v2, but `docker compose` (space) is the recommended modern syntax.

---

## What Changed in run.sh

The updated `run.sh` script now:

1. **Auto-detects** which Docker Compose version is available
2. **Prefers** Docker Compose v2 if available
3. **Falls back** to v1 if v2 isn't installed
4. **Warns** if using the legacy v1 version
5. **Uses** the correct command throughout the script

This ensures compatibility with both old and new installations.

---

## Next Steps After Fix

Once Docker Compose is upgraded and working:

```bash
# 1. Pull latest code
cd ~/NITTER
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ

# 2. Make script executable
chmod +x run.sh

# 3. Run the scraper
./run.sh

# 4. Verify services
docker compose ps

# 5. Check API health
curl http://localhost:8000/health

# 6. Test scraping
python3 cli.py
```

---

## Success Indicators

You'll know the fix worked when:

✅ No urllib3 errors
✅ All 6 containers start successfully
✅ `docker compose ps` shows all services "Up"
✅ API responds at http://localhost:8000/health
✅ Dashboard loads at http://localhost/dashboard
✅ CLI connects and can track users

---

## Support

If issues persist after upgrading:

1. **Check Docker version:**
   ```bash
   docker --version  # Should be 20.10+
   ```

2. **Check Docker Compose version:**
   ```bash
   docker compose version  # Should be v2.x.x
   ```

3. **Clean up and rebuild:**
   ```bash
   docker compose down -v
   docker system prune -a
   ./run.sh
   ```

4. **Check logs:**
   ```bash
   docker compose logs api
   docker compose logs postgres
   ```

---

## References

- [Docker Compose v2 Documentation](https://docs.docker.com/compose/)
- [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)
- [Docker Compose v2 Release Notes](https://github.com/docker/compose/releases)
- [Migrating from v1 to v2](https://docs.docker.com/compose/migrate/)

---

## Summary

**Problem:** urllib3 v2.5.0 incompatible with docker-compose v1.29.2
**Solution:** Upgrade to Docker Compose v2
**Time:** 2-5 minutes
**Difficulty:** Easy
**Benefit:** Better performance, no Python dependency conflicts

After this fix, your Nitter scraper will run smoothly! 🚀
