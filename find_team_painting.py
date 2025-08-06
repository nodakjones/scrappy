#!/usr/bin/env python3
"""
Find A TEAM PAINTING contractor
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import db_pool

async def find_contractor():
    """Find A TEAM PAINTING contractor"""
    
    await db_pool.initialize()
    
    query = """
    SELECT id, business_name FROM contractors 
    WHERE business_name ILIKE '%A TEAM PAINTING%'
    """
    
    rows = await db_pool.fetch(query)
    
    print("Found:")
    for row in rows:
        print(f"  {row['business_name']} (ID: {row['id']})")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(find_contractor()) 