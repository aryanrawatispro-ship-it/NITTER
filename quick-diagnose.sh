#!/bin/bash

echo "=========================================="
echo "  Quick Diagnosis Script"
echo "=========================================="
echo ""

echo "1. Container Status:"
docker compose ps
echo ""

echo "2. Failed Jobs Details:"
curl -s http://localhost:8000/api/jobs/recent?limit=5 | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/jobs/recent?limit=5
echo ""

echo "3. Last 50 lines of Worker Logs:"
docker compose logs celery_worker --tail=50
echo ""

echo "4. API Health:"
curl -s http://localhost:8000/health
echo ""

echo "5. Nitter Instance Health:"
curl -s http://localhost:8000/api/dashboard/instance-health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Could not fetch instance health"
echo ""

echo "=========================================="
echo "  Diagnosis Complete"
echo "=========================================="
