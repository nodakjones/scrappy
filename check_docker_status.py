#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import db_pool

async def check_status():
    await db_pool.initialize()
    
    async with db_pool.pool.acquire() as conn:
        # Check processing status
        result = await conn.fetch('''
            SELECT processing_status, COUNT(*) 
            FROM contractors 
            GROUP BY processing_status
        ''')
        
        print("Processing Status:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        # Check review status
        result = await conn.fetch('''
            SELECT review_status, COUNT(*) 
            FROM contractors 
            WHERE processing_status = 'completed'
            GROUP BY review_status
        ''')
        
        print("\nReview Status (completed contractors):")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        # Check pending contractors
        result = await conn.fetch('''
            SELECT COUNT(*) 
            FROM contractors 
            WHERE processing_status = 'pending'
        ''')
        
        print(f"\nPending contractors: {result[0][0]}")
        
        # Show some examples of pending contractors
        result = await conn.fetch('''
            SELECT business_name, city, state 
            FROM contractors 
            WHERE processing_status = 'pending'
            LIMIT 5
        ''')
        
        print("\nSample pending contractors:")
        for row in result:
            print(f"  {row[0]} ({row[1]}, {row[2]})")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_status()) 