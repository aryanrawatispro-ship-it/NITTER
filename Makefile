.PHONY: help install dev build up down logs clean migrate test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	pip install -r requirements.txt
	playwright install chromium

dev: ## Run development server
	uvicorn src.api.main:app --reload --port 8000

build: ## Build Docker images
	docker-compose build

up: ## Start all services with Docker Compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

clean: ## Stop services and remove volumes
	docker-compose down -v

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

test: ## Run tests
	pytest tests/ -v

worker: ## Run Celery worker
	celery -A src.scheduler.celery_app worker --loglevel=info

beat: ## Run Celery beat scheduler
	celery -A src.scheduler.celery_app beat --loglevel=info

flower: ## Run Celery Flower monitoring
	celery -A src.scheduler.celery_app flower --port=5555

shell: ## Open Python shell with app context
	python -i -c "from src.utils.database import SessionLocal; from src.utils.models import *; db = SessionLocal()"

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U nitter_user -d nitter_db

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

status: ## Show status of all services
	docker-compose ps

restart: ## Restart all services
	docker-compose restart
