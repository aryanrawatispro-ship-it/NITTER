#!/bin/bash

echo "=========================================="
echo "  Testing Nitter Instances"
echo "=========================================="
echo ""

# Test a few Nitter instances
instances=(
    "https://nitter.net"
    "https://nitter.poast.org"
    "https://nitter.privacydev.net"
    "https://nitter.it"
    "https://nitter.eu"
    "https://nitter.tiekoetter.com"
)

echo "Testing instances for @elonmusk profile:"
echo ""

for instance in "${instances[@]}"; do
    echo "Testing: $instance"

    # Try to fetch the profile
    response=$(curl -s -L -m 10 "$instance/elonmusk" 2>&1 | head -c 500)

    # Check if we got HTML
    if echo "$response" | grep -q "profile-card\|timeline\|error\|404\|suspended"; then
        if echo "$response" | grep -q "profile-card"; then
            echo "  ✅ SUCCESS - Found profile-card"
        elif echo "$response" | grep -q "timeline"; then
            echo "  ⚠️  PARTIAL - Found timeline but no profile-card"
        elif echo "$response" | grep -q "error\|404\|suspended"; then
            echo "  ❌ ERROR - Account suspended or not found"
        fi
    else
        echo "  ❌ FAILED - No response or wrong content"
    fi

    echo ""
done

echo "=========================================="
echo "  Testing with Playwright in Container"
echo "=========================================="
echo ""

# Detect Docker Compose command
if docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "Scraping elonmusk profile with Playwright..."
$COMPOSE_CMD exec api python3 << 'PYTHON'
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        instances = [
            "https://nitter.net/elonmusk",
            "https://nitter.poast.org/elonmusk",
        ]

        for url in instances:
            print(f"\nTesting: {url}")
            try:
                await page.goto(url, timeout=10000)
                content = await page.content()

                # Check for key selectors
                has_profile = '.profile-card' in content or 'class="profile-card"' in content
                has_timeline = '.timeline-item' in content or 'class="timeline-item"' in content
                has_error = 'error-panel' in content or 'User not found' in content or 'Account suspended' in content

                print(f"  Profile card found: {has_profile}")
                print(f"  Timeline found: {has_timeline}")
                print(f"  Error page: {has_error}")

                # Print first 500 chars of HTML
                print(f"  HTML preview: {content[:500]}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

        await browser.close()

asyncio.run(test())
PYTHON

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="
