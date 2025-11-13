#!/bin/bash

# Nitter Scraper Startup Script

echo "Starting Nitter Twitter Scraper..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Detect which Docker Compose version to use
if docker compose version > /dev/null 2>&1; then
    # Docker Compose v2 (recommended)
    COMPOSE_CMD="docker compose"
    echo "Using Docker Compose v2"
elif command -v docker-compose > /dev/null 2>&1; then
    # Docker Compose v1 (legacy)
    COMPOSE_CMD="docker-compose"
    echo "Using Docker Compose v1 (legacy)"
    echo "WARNING: Consider upgrading to Docker Compose v2 for better compatibility"
    echo "See: https://docs.docker.com/compose/install/"
else
    echo "ERROR: Docker Compose is not installed!"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "Building Docker images..."
$COMPOSE_CMD build

echo "Starting services..."
$COMPOSE_CMD up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Run database migrations
echo "Setting up database..."

# Check if migrations exist, if not create initial migration
MIGRATION_COUNT=$($COMPOSE_CMD exec -T api ls -1 /app/alembic/versions/*.py 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -eq "0" ]; then
    echo "Generating initial database migration..."
    $COMPOSE_CMD exec -T api alembic revision --autogenerate -m "Initial database schema"
fi

echo "Running database migrations..."
$COMPOSE_CMD exec -T api alembic upgrade head

echo ""
echo "================================================"
echo "Nitter Scraper is now running!"
echo "================================================"
echo ""
echo "Available endpoints:"
echo "  - Dashboard:  http://localhost/dashboard"
echo "  - API Docs:   http://localhost/docs"
echo "  - API:        http://localhost/api"
echo ""
echo "To view logs:"
echo "  $COMPOSE_CMD logs -f"
echo ""
echo "To stop:"
echo "  $COMPOSE_CMD down"
echo ""
