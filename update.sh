#!/bin/bash

###############################################################################
# Update Script for NITTER Twitter Scraping System
# Run this on your VPS to pull latest changes and restart services
###############################################################################

set -e

echo "========================================="
echo "  Updating NITTER Scraping System"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ ERROR: docker-compose.yml not found${NC}"
    echo "Please run this script from the NITTER directory"
    exit 1
fi

echo -e "${YELLOW}Step 1: Pulling latest changes from git...${NC}"
git fetch origin
git pull origin claude/start-work-011CV5edTh7A3uaweF4SveNQ

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull failed${NC}"
    echo "Please resolve any conflicts manually"
    exit 1
fi

echo -e "${GREEN}✅ Code updated successfully${NC}"
echo ""

echo -e "${YELLOW}Step 2: Checking for new dependencies...${NC}"
if docker compose exec -T api pip install -q -r requirements.txt; then
    echo -e "${GREEN}✅ Dependencies up to date${NC}"
else
    echo -e "${YELLOW}⚠️  Could not update dependencies (containers might be down)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3: Running database migrations...${NC}"
if docker compose exec -T api alembic upgrade head; then
    echo -e "${GREEN}✅ Database migrations applied${NC}"
else
    echo -e "${YELLOW}⚠️  Could not run migrations (will be run on next restart)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 4: Restarting services...${NC}"
docker compose restart api worker beat

echo ""
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services restarted successfully${NC}"
else
    echo -e "${RED}❌ Some services may not be running${NC}"
    echo "Run 'docker compose ps' to check status"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ UPDATE COMPLETE!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  • Check logs: docker compose logs -f api"
echo "  • Check status: docker compose ps"
echo "  • Test scraping: python3 cli.py"
echo ""
