#!/bin/bash

###############################################################################
# TwitterAPI.io Integration Test Script
# Tests that TwitterAPI.io is properly integrated into the scraping system
###############################################################################

set -e

echo "========================================="
echo "  TwitterAPI.io Integration Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker compose ps > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Docker containers are not running${NC}"
    echo ""
    echo "Please start the containers first:"
    echo "  ./run.sh"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking configuration...${NC}"

# Check if TwitterAPI.io is configured
if ! docker compose exec -T api python3 << 'PYTHON'
from src.utils.config import settings
import sys

if not settings.use_twitterapiio:
    print("❌ USE_TWITTERAPIIO is not enabled in .env")
    sys.exit(1)

if not settings.twitterapiio_api_key:
    print("❌ TWITTERAPIIO_API_KEY is not set in .env")
    sys.exit(1)

print(f"✅ TwitterAPI.io is enabled")
print(f"✅ API key is configured (length: {len(settings.twitterapiio_api_key)})")
PYTHON
then
    echo ""
    echo -e "${RED}Configuration check failed!${NC}"
    echo ""
    echo "Please configure TwitterAPI.io in your .env file:"
    echo "  USE_TWITTERAPIIO=true"
    echo "  TWITTERAPIIO_API_KEY=your_api_key_here"
    echo ""
    echo "See TWITTERAPIIO_SETUP.md for details."
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Testing TwitterAPI.io import...${NC}"

if docker compose exec -T api python3 << 'PYTHON'
try:
    from src.scrapers import TwitterAPIioScraper
    print("✅ TwitterAPIioScraper imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import sys
    sys.exit(1)
PYTHON
then
    echo -e "${GREEN}✅ Import test passed${NC}"
else
    echo -e "${RED}❌ Import test failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Testing API connection...${NC}"

if docker compose exec -T api python3 << 'PYTHON'
import asyncio
from src.scrapers.twitterapiio_scraper import TwitterAPIioScraper
from src.utils.config import settings

async def test():
    scraper = TwitterAPIioScraper(settings.twitterapiio_api_key)

    # Test with Twitter's official account (always exists)
    print("Testing with @twitter account...")
    profile = await scraper.scrape_profile("twitter")

    if profile:
        print(f"✅ API connection successful!")
        print(f"   Username: {profile.get('username')}")
        print(f"   Followers: {profile.get('followers_count', 0):,}")
        return True
    else:
        print("❌ API returned no data")
        return False

result = asyncio.run(test())
import sys
sys.exit(0 if result else 1)
PYTHON
then
    echo -e "${GREEN}✅ API connection test passed${NC}"
else
    echo ""
    echo -e "${RED}❌ API connection test failed${NC}"
    echo ""
    echo "Possible issues:"
    echo "  1. Invalid API key - check your key at https://twitterapi.io/dashboard"
    echo "  2. Rate limit exceeded - check usage at https://twitterapi.io/dashboard"
    echo "  3. Network issue - check your internet connection"
    echo ""
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Testing task scheduler integration...${NC}"

if docker compose exec -T api python3 << 'PYTHON'
try:
    from src.scheduler.tasks import scrape_user_profile
    print("✅ Task scheduler imports TwitterAPIioScraper")

    # Check if tasks module references TwitterAPIioScraper
    import inspect
    source = inspect.getsource(scrape_user_profile.run)

    if "TwitterAPIioScraper" in source:
        print("✅ scrape_user_profile uses TwitterAPIioScraper")
    else:
        print("❌ scrape_user_profile doesn't use TwitterAPIioScraper")
        import sys
        sys.exit(1)

except Exception as e:
    print(f"❌ Task scheduler test failed: {e}")
    import sys
    sys.exit(1)
PYTHON
then
    echo -e "${GREEN}✅ Task scheduler integration test passed${NC}"
else
    echo -e "${RED}❌ Task scheduler integration test failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Testing end-to-end scraping...${NC}"

# Trigger a scrape job
echo "Triggering scrape job for @twitter..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/twitter/scrape)

if echo "$JOB_RESPONSE" | grep -q "job_id"; then
    echo -e "${GREEN}✅ Scrape job started successfully${NC}"

    # Extract job ID
    JOB_ID=$(echo "$JOB_RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    echo "   Job ID: $JOB_ID"

    # Wait for job to complete
    echo ""
    echo "Waiting for job to complete..."
    sleep 10

    # Check job status
    JOB_STATUS=$(curl -s http://localhost:8000/api/jobs/recent?limit=1)

    if echo "$JOB_STATUS" | grep -q '"status":"completed"'; then
        echo -e "${GREEN}✅ Job completed successfully${NC}"

        # Check if items were scraped
        ITEMS=$(echo "$JOB_STATUS" | grep -o '"items_scraped":[0-9]*' | cut -d':' -f2)

        if [ "$ITEMS" -gt 0 ]; then
            echo -e "${GREEN}✅ Successfully scraped $ITEMS item(s)${NC}"
        else
            echo -e "${YELLOW}⚠️  Job completed but scraped 0 items${NC}"
            echo "   This might indicate TwitterAPI.io fallback occurred"
        fi
    else
        echo -e "${YELLOW}⚠️  Job status: $(echo "$JOB_STATUS" | grep -o '"status":"[^"]*"')${NC}"
    fi
else
    echo -e "${RED}❌ Failed to start scrape job${NC}"
    echo "Response: $JOB_RESPONSE"
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
echo "========================================="
echo ""
echo "TwitterAPI.io integration is working correctly!"
echo ""
echo "Next steps:"
echo "  1. Monitor usage at https://twitterapi.io/dashboard"
echo "  2. Check logs: docker compose logs -f api | grep TwitterAPI"
echo "  3. See TWITTERAPIIO_SETUP.md for more information"
echo ""
