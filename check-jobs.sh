#!/bin/bash

echo "=========================================="
echo "  Detailed Job Analysis"
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

echo "1. Recent Jobs with Details:"
echo "----------------------------"
curl -s http://localhost:8000/api/jobs/recent?limit=10 | python3 -m json.tool
echo ""
echo ""

echo "2. Last 100 Lines of Worker Logs:"
echo "-----------------------------------"
$COMPOSE_CMD logs celery_worker --tail=100 | grep -E "(ERROR|INFO|Starting|completed|failed|scrape)" || $COMPOSE_CMD logs celery_worker --tail=100
echo ""
echo ""

echo "3. Check if Playwright Browser Exists:"
echo "---------------------------------------"
$COMPOSE_CMD exec api ls -la /ms-playwright/chromium-*/chrome-linux/chrome 2>&1 || echo "❌ Playwright browser NOT found"
echo ""
echo ""

echo "4. Test Playwright from Inside Container:"
echo "------------------------------------------"
$COMPOSE_CMD exec api python3 -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        print('✅ Playwright browser launched successfully!')
        browser.close()
except Exception as e:
    print(f'❌ Playwright error: {e}')
" 2>&1
echo ""
echo ""

echo "5. Check Nitter Instance Health:"
echo "---------------------------------"
curl -s http://localhost:8000/api/dashboard/instance-health 2>/dev/null | python3 -m json.tool || echo "Instance health endpoint not available"
echo ""
echo ""

echo "6. Database Tables Check:"
echo "-------------------------"
$COMPOSE_CMD exec api python3 -c "
from src.utils.database import engine
from sqlalchemy import inspect
tables = inspect(engine).get_table_names()
print(f'Tables: {tables}')
print(f'Total: {len(tables)} tables')
" 2>&1
echo ""
echo ""

echo "=========================================="
echo "  Analysis Complete"
echo "=========================================="
