"""
Database connection pool management
"""
import asyncio
import asyncpg
from typing import Optional, Dict, Any
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import config

logger = logging.getLogger(__name__)


class DatabasePool:
    """Manages PostgreSQL connection pool"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                min_size=config.DB_MIN_CONNECTIONS,
                max_size=config.DB_MAX_CONNECTIONS,
                command_timeout=60
            )
            logger.info(f"Database pool initialized with {config.DB_MIN_CONNECTIONS}-{config.DB_MAX_CONNECTIONS} connections")
            
            # Test the connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query that doesn't return data"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def transaction(self):
        """Get a transaction context"""
        return self.pool.acquire()
    
    async def execute_many(self, query: str, args_list: list) -> None:
        """Execute many queries with different parameters"""
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)
    
    async def copy_records_to_table(self, table_name: str, records: list, columns: list):
        """Bulk insert records using COPY"""
        async with self.pool.acquire() as conn:
            await conn.copy_records_to_table(
                table_name,
                records=records,
                columns=columns
            )


# Global database pool instance
db_pool = DatabasePool()