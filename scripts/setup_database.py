#!/usr/bin/env python3
"""
Database setup script for contractor enrichment system
"""
import asyncio
import asyncpg
import sys
import logging
from pathlib import Path
import os

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect to postgres database to create our database
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database='postgres'
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            config.DB_NAME
        )
        
        if not exists:
            logger.info(f"Creating database: {config.DB_NAME}")
            await conn.execute(f'CREATE DATABASE "{config.DB_NAME}"')
            logger.info(f"Database {config.DB_NAME} created successfully")
        else:
            logger.info(f"Database {config.DB_NAME} already exists")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


async def execute_sql_file(file_path: Path):
    """Execute SQL commands from a file"""
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        
        logger.info(f"Executing SQL file: {file_path}")
        await conn.execute(sql_content)
        logger.info(f"Successfully executed: {file_path}")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error executing {file_path}: {e}")
        raise


async def setup_database():
    """Main database setup function"""
    logger.info("Starting database setup...")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        return False
    
    try:
        # Create database if it doesn't exist
        await create_database_if_not_exists()
        
        # Get the SQL directory path
        sql_dir = Path(__file__).parent.parent / 'sql'
        
        # Execute SQL files in order
        sql_files = [
            '01_create_schema.sql',
            '02_create_indexes.sql',
            '03_insert_categories.sql'
        ]
        
        for sql_file in sql_files:
            file_path = sql_dir / sql_file
            if file_path.exists():
                await execute_sql_file(file_path)
            else:
                logger.warning(f"SQL file not found: {file_path}")
        
        # Test the connection and verify tables
        conn = await asyncpg.connect(config.database_url)
        
        # Check if main tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        logger.info(f"Created tables: {', '.join(table_names)}")
        
        # Check categories count
        categories_count = await conn.fetchval("SELECT COUNT(*) FROM mailer_categories")
        logger.info(f"Inserted {categories_count} mailer categories")
        
        await conn.close()
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


def main():
    """Main entry point"""
    if not asyncio.run(setup_database()):
        sys.exit(1)
    
    print("\n✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and configure your settings")
    print("2. Run: python scripts/import_data.py to load contractor data")
    print("3. Run: python scripts/run_processing.py to start processing")


if __name__ == "__main__":
    main()