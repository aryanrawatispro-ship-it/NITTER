#!/bin/bash

echo "=========================================="
echo "  Fixing Playwright Installation"
echo "=========================================="
echo ""

# Detect Docker Compose command
if docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "ERROR: Docker Compose not found!"
    exit 1
fi

echo "Step 1: Stopping all containers..."
$COMPOSE_CMD down
echo ""

echo "Step 2: Rebuilding containers with fixed Playwright installation..."
echo "(This will take 2-3 minutes)"
$COMPOSE_CMD build --no-cache
echo ""

echo "Step 3: Starting containers..."
$COMPOSE_CMD up -d
echo ""

echo "Step 4: Waiting for services to start..."
sleep 15
echo ""

echo "Step 5: Running database migrations..."
$COMPOSE_CMD exec -T api alembic upgrade head
echo ""

echo "Step 6: Testing Playwright installation..."
$COMPOSE_CMD exec api python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright browser installed successfully!')"
echo ""

echo "Step 7: Checking container status..."
$COMPOSE_CMD ps
echo ""

echo "=========================================="
echo "  Fix Complete!"
echo "=========================================="
echo ""
echo "You can now start scraping:"
echo "  python3 cli.py"
echo ""
echo "Or test with:"
echo "  curl -X POST http://localhost:8000/api/users/twitter/scrape"
echo ""
