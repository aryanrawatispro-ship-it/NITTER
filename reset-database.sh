#!/bin/bash

echo "=========================================="
echo "  Resetting Database and Migrations"
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

echo "Step 1: Resetting alembic version table in database..."
$COMPOSE_CMD exec -T postgres psql -U nitter_user -d nitter_db -c "DROP TABLE IF EXISTS alembic_version;"
echo "✓ Alembic version table dropped"
echo ""

echo "Step 2: Dropping all existing tables..."
$COMPOSE_CMD exec -T postgres psql -U nitter_user -d nitter_db -c "DROP TABLE IF EXISTS webhooks, tweets, search_queries, scraping_jobs, twitter_users CASCADE;"
echo "✓ All tables dropped"
echo ""

echo "Step 3: Generating initial migration..."
$COMPOSE_CMD exec -T api alembic revision --autogenerate -m "Initial database schema"
echo "✓ Migration generated"
echo ""

echo "Step 4: Applying migration to create all tables..."
$COMPOSE_CMD exec -T api alembic upgrade head
echo "✓ Migration applied"
echo ""

echo "Step 5: Verifying tables were created..."
$COMPOSE_CMD exec -T postgres psql -U nitter_user -d nitter_db -c "\dt"
echo ""

echo "Step 6: Restarting worker to clear any cached errors..."
$COMPOSE_CMD restart celery_worker celery_beat
echo ""

echo "=========================================="
echo "  Database Reset Complete!"
echo "=========================================="
echo ""
echo "You can now start scraping:"
echo "  python3 cli.py"
echo ""
echo "Or test with:"
echo "  curl -X POST http://localhost:8000/api/users/twitter/scrape"
echo "  sleep 30"
echo "  curl http://localhost:8000/api/jobs/recent?limit=1"
echo ""
