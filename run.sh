#!/bin/bash

# Nitter Scraper Startup Script

echo "Starting Nitter Twitter Scraper..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Run database migrations
echo "Setting up database..."

# Check if migrations exist, if not create initial migration
MIGRATION_COUNT=$(docker-compose exec -T api ls -1 /app/alembic/versions/*.py 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -eq "0" ]; then
    echo "Generating initial database migration..."
    docker-compose exec -T api alembic revision --autogenerate -m "Initial database schema"
fi

echo "Running database migrations..."
docker-compose exec -T api alembic upgrade head

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
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
