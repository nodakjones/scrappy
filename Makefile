# Makefile for Contractor Enrichment System Docker Operations

.PHONY: help build up down logs clean setup test dev prod

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup    - Run Docker setup script"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services in background"
	@echo "  make down     - Stop services"
	@echo "  make logs     - Follow logs"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make dev      - Start in development mode"
	@echo "  make prod     - Start in production mode"
	@echo "  make test     - Run tests in container"
	@echo "  make shell    - Access app container shell"
	@echo "  make db       - Access database shell"

# Setup
setup:
	@echo "Running Docker setup..."
	python scripts/docker_setup.py

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down

# Follow logs
logs:
	@echo "Following logs..."
	docker-compose logs -f

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development mode
dev:
	@echo "Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Production mode
prod:
	@echo "Starting in production mode..."
	docker-compose -f docker-compose.yml up -d

# Run tests
test:
	@echo "Running tests in container..."
	docker-compose exec app python -m pytest tests/ -v

# Access app shell
shell:
	@echo "Accessing app container shell..."
	docker-compose exec app bash

# Access database
db:
	@echo "Accessing database..."
	docker-compose exec postgres psql -U postgres -d contractor_enrichment

# Database setup
db-setup:
	@echo "Setting up database..."
	docker-compose exec app python scripts/setup_database.py

# Import data
import-data:
	@echo "Importing data..."
	docker-compose exec app python scripts/import_data.py

# Export data
export-data:
	@echo "Exporting data..."
	docker-compose exec app python scripts/export_contractors.py

# Check status
status:
	@echo "Service status:"
	docker-compose ps

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Backup database
backup:
	@echo "Backing up database..."
	docker-compose exec postgres pg_dump -U postgres contractor_enrichment > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker-compose exec -T postgres psql -U postgres contractor_enrichment < $$backup_file 