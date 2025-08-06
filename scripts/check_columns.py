#!/usr/bin/env python3
"""
Check Database Columns
====================

Check the actual column names in the contractors table.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_columns():
    """Check the actual column names"""
    await db_pool.initialize()
    
    print("🔍 CONTRACTORS TABLE COLUMNS")
    print("=" * 50)
    
    # Get column names
    columns_query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'contractors' 
        ORDER BY ordinal_position
    """
    
    columns = await db_pool.fetch(columns_query)
    
    print(f"📊 Contractor Table Columns:")
    for column in columns:
        name = column['column_name']
        data_type = column['data_type']
        print(f"   - {name} ({data_type})")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_columns()) 