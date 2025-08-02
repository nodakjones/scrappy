# Docker Setup for Contractor Enrichment System

This guide will help you set up and run the Contractor Enrichment System using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed
- API keys for OpenAI (required) and optional search APIs

## Quick Start

1. **Clone and navigate to the project directory**
   ```bash
   cd scrappy
   ```

2. **Run the Docker setup script**
   ```bash
   python scripts/docker_setup.py
   ```

3. **Configure your API keys**
   ```bash
   # Edit the .env file with your API keys
   nano .env
   ```

4. **Start the services**
   ```bash
   docker-compose up -d
   ```

## Manual Setup

If you prefer to set up manually:

### 1. Environment Configuration

Copy the example environment file and configure your API keys:

```bash
cp env.example .env
```

Edit `.env` file with your actual API keys:
```bash
# Required
OPENAI_API_KEY=your_actual_openai_api_key

# Optional
SERPAPI_KEY=your_serpapi_key
BING_SEARCH_API_KEY=your_bing_search_api_key
```

### 2. Build and Start Services

```bash
# Build the Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

## Services

The Docker setup includes:

- **PostgreSQL Database** (`postgres`): Stores contractor data and processing results
- **Python Application** (`app`): Main contractor enrichment application

## Useful Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
docker-compose logs -f postgres
```

### Container Access
```bash
# Access the application container
docker-compose exec app bash

# Access the database
docker-compose exec postgres psql -U postgres -d contractor_enrichment

# Run Python scripts inside container
docker-compose exec app python scripts/setup_database.py
docker-compose exec app python scripts/import_data.py
```

### Data Management
```bash
# Copy data files to container
docker cp ./data/contractors.csv contractor_app:/app/data/

# Copy exports from container
docker cp contractor_app:/app/exports/ ./exports/
```

## Directory Structure

```
scrappy/
├── data/                    # Input data files (mounted to container)
├── exports/                 # Output files (mounted to container)
├── sql/                     # Database initialization scripts
├── src/                     # Application source code
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Main Docker Compose configuration
├── docker-compose.override.yml  # Development overrides
├── Dockerfile              # Application container definition
└── .env                    # Environment variables (create from env.example)
```

## Development Mode

For development, use the override file which mounts the source code:

```bash
# Development mode with live code reloading
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :5432
   lsof -i :8000
   
   # Change ports in docker-compose.yml if needed
   ```

2. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **Permission issues**
   ```bash
   # Fix file permissions
   chmod +x scripts/*.py
   ```

4. **API key issues**
   ```bash
   # Check environment variables
   docker-compose exec app env | grep OPENAI
   ```

### Logs and Debugging

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service logs
docker-compose logs -f app

# Check container status
docker-compose ps

# Inspect container
docker-compose exec app bash
```

## Database Management

### Initialize Database
```bash
# Run database setup
docker-compose exec app python scripts/setup_database.py
```

### Import Data
```bash
# Import contractor data
docker-compose exec app python scripts/import_data.py
```

### Database Backup/Restore
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres contractor_enrichment > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres contractor_enrichment < backup.sql
```

## Performance Tuning

### Resource Limits
Edit `docker-compose.yml` to set resource limits:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Database Optimization
```bash
# Connect to database and run optimizations
docker-compose exec postgres psql -U postgres -d contractor_enrichment -f /docker-entrypoint-initdb.d/03_optimize_indexes.sql
```

## Production Deployment

For production deployment:

1. Remove development overrides
2. Set appropriate resource limits
3. Use external database if needed
4. Configure proper logging
5. Set up monitoring

```bash
# Production mode (without development overrides)
docker-compose -f docker-compose.yml up -d
```

## Security Notes

- Change default database passwords in production
- Use secrets management for API keys
- Regularly update Docker images
- Monitor container logs for security issues

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose exec app env`
3. Test database connection: `docker-compose exec app python -c "from src.database.connection import db_pool; import asyncio; asyncio.run(db_pool.initialize())"`
4. Check container health: `docker-compose ps` 