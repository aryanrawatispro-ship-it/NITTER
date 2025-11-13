# VPS Deployment Guide

## Prerequisites

### Minimum VPS Requirements:
- **RAM**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum (4 cores recommended)
- **Storage**: 20GB minimum (50GB+ recommended for data)
- **OS**: Ubuntu 20.04/22.04, Debian 10/11, or CentOS 7/8
- **Network**: Public IP with open ports 80, 443

---

## Step 1: Initial VPS Setup

### Connect to your VPS
```bash
ssh root@your-vps-ip
```

### Update system
```bash
apt update && apt upgrade -y  # Ubuntu/Debian
# OR
yum update -y  # CentOS
```

### Create a non-root user (recommended)
```bash
adduser nitter
usermod -aG sudo nitter
su - nitter
```

---

## Step 2: Install Docker & Docker Compose

### Ubuntu/Debian
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### CentOS/RHEL
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## Step 3: Deploy the Application

### Clone or upload the project
```bash
# Option 1: Clone from GitHub
git clone https://github.com/your-repo/NITTER.git
cd NITTER

# Option 2: Upload via SCP
# From your local machine:
# scp -r /path/to/NITTER user@vps-ip:/home/user/
```

### Configure environment
```bash
cp .env.example .env
nano .env  # Edit configuration
```

**Important `.env` settings:**
```bash
# Database (use strong passwords!)
DATABASE_URL=postgresql://nitter_user:CHANGE_THIS_PASSWORD@postgres:5432/nitter_db

# API
API_SECRET_KEY=GENERATE_A_RANDOM_SECRET_KEY_HERE

# Scraping (adjust based on your needs)
MIN_REQUEST_DELAY=2
MAX_REQUEST_DELAY=8
```

### Generate secret key
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 4: Configure Firewall

### UFW (Ubuntu/Debian)
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (if using SSL)
sudo ufw enable
sudo ufw status
```

### Firewalld (CentOS)
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## Step 5: Launch the Application

### Start all services
```bash
chmod +x run.sh
./run.sh
```

### Or manually with Docker Compose
```bash
docker-compose up -d
```

### Check service status
```bash
docker-compose ps
```

### View logs
```bash
docker-compose logs -f
```

---

## Step 6: Verify Deployment

### Run validation
```bash
python3 validate.py
```

### Test API
```bash
curl http://localhost:8000/health
```

### Access from browser
```
http://your-vps-ip/dashboard
http://your-vps-ip/docs
```

---

## Step 7: Setup SSL/HTTPS (Recommended)

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Get SSL certificate
```bash
sudo certbot --nginx -d your-domain.com
```

### Update Nginx configuration
Edit `docker/nginx.conf` to add SSL support, then:
```bash
docker-compose restart nginx
```

---

## Troubleshooting

### Services won't start
```bash
# Check Docker logs
docker-compose logs

# Check individual service
docker-compose logs api
docker-compose logs celery_worker

# Restart services
docker-compose restart
```

### Out of memory
```bash
# Check memory usage
free -h
docker stats

# Increase swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Database connection errors
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Playwright browser issues
```bash
# Rebuild with updated dependencies
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use
```bash
# Find process using port 80
sudo lsof -i :80
# OR
sudo netstat -tlnp | grep :80

# Kill process
sudo kill -9 <PID>
```

---

## Performance Optimization

### Increase Celery workers
Edit `docker-compose.yml`:
```yaml
celery_worker:
  command: celery -A src.scheduler.celery_app worker --loglevel=info --concurrency=8
```

### Add more worker containers
```yaml
celery_worker_2:
  build:
    context: .
    dockerfile: docker/Dockerfile
  container_name: nitter_celery_worker_2
  # ... (same config as celery_worker)
```

### Enable Redis persistence
Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

---

## Monitoring

### View resource usage
```bash
docker stats
htop
```

### Monitor logs in real-time
```bash
tail -f logs/nitter_scraper.log
```

### Setup log rotation
```bash
sudo nano /etc/logrotate.d/nitter
```

Add:
```
/home/user/NITTER/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Maintenance

### Update the application
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Backup database
```bash
docker-compose exec postgres pg_dump -U nitter_user nitter_db > backup.sql
```

### Restore database
```bash
cat backup.sql | docker-compose exec -T postgres psql -U nitter_user nitter_db
```

### Clean up old Docker resources
```bash
docker system prune -a
docker volume prune
```

### Auto-start on boot
```bash
# Create systemd service
sudo nano /etc/systemd/system/nitter-scraper.service
```

Add:
```ini
[Unit]
Description=Nitter Scraper
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/NITTER
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=user

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable nitter-scraper
sudo systemctl start nitter-scraper
```

---

## Common VPS Provider Specific Notes

### DigitalOcean
- Minimum $12/month droplet (4GB RAM)
- Firewall configured via web panel
- Floating IP recommended for production

### AWS EC2
- t3.medium or larger recommended
- Configure Security Groups for ports
- Use Elastic IP
- Consider RDS for PostgreSQL (separate)

### Hetzner
- CX31 or better (8GB RAM)
- Excellent price/performance
- Built-in firewall

### Linode
- 4GB plan minimum
- NodeBalancer for load balancing
- Backup service available

### Vultr
- High Frequency 4GB plan recommended
- Block storage for data
- DDoS protection included

---

## Security Best Practices

1. **Change default passwords** in `.env`
2. **Use SSH keys** instead of passwords
3. **Disable root SSH login**
4. **Keep system updated**: `apt update && apt upgrade`
5. **Setup fail2ban**: `sudo apt install fail2ban`
6. **Use SSL/TLS** for production
7. **Backup regularly** (database + code)
8. **Monitor logs** for suspicious activity
9. **Limit API access** with authentication (add if needed)
10. **Use environment-specific secrets**

---

## Testing on VPS

After deployment, run these tests:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Track a user
curl -X POST http://localhost:8000/api/users/track \
  -H "Content-Type: application/json" \
  -d '{"username": "twitter", "check_interval": 3600}'

# 3. Check jobs
curl http://localhost:8000/api/jobs/stats/summary

# 4. Check instance health
curl http://localhost:8000/api/dashboard/instance/health

# 5. Export test
curl http://localhost:8000/api/export/tweets/csv?username=twitter -o test.csv
```

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Check service status: `docker-compose ps`
3. Review `.env` configuration
4. Ensure ports are open
5. Check VPS resources: `htop` or `docker stats`
6. Verify Nitter instances are accessible
7. Check GitHub issues

---

## Cost Estimates

### VPS Costs (Monthly)
- **Small deployment**: $12-20 (4GB RAM, 2 vCPU)
- **Medium deployment**: $24-40 (8GB RAM, 4 vCPU)
- **Large deployment**: $80+ (16GB+ RAM, 8+ vCPU)

### Recommendations by usage:
- **Personal/Testing**: 4GB VPS
- **Small team (1-10 users)**: 8GB VPS
- **Medium scale (10-50 users)**: 16GB VPS
- **Large scale**: Multiple VPS + load balancer

---

## Next Steps

Once deployed:
1. Monitor for 24 hours to ensure stability
2. Set up automated backups
3. Configure alerting (optional)
4. Add authentication to API (if needed)
5. Set up SSL certificate
6. Configure custom domain
7. Optimize based on usage patterns
