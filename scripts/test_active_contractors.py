#!/usr/bin/env python3
"""
Test ACTIVE Contractor Filtering
===============================

Test the filtering for ACTIVE contractors only.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def test_active_contractors():
    """Test ACTIVE contractor filtering"""
    await db_pool.initialize()
    
    print("🔍 TESTING ACTIVE CONTRACTOR FILTERING")
    print("=" * 50)
    
    # Test Puget Sound ACTIVE contractors
    puget_active_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'pending' 
        AND puget_sound = TRUE
        AND status_code = 'A'
    """
    
    puget_active = await db_pool.fetchrow(puget_active_query)
    puget_active_count = puget_active['count']
    
    print(f"📊 ACTIVE Puget Sound Pending: {puget_active_count:,}")
    
    # Test all ACTIVE contractors
    all_active_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'pending'
        AND status_code = 'A'
    """
    
    all_active = await db_pool.fetchrow(all_active_query)
    all_active_count = all_active['count']
    
    print(f"📊 All ACTIVE Pending: {all_active_count:,}")
    
    # Show some sample records
    sample_query = """
        SELECT id, business_name, city, state, status_code, processing_status, puget_sound
        FROM contractors 
        WHERE processing_status = 'pending' 
        AND puget_sound = TRUE
        AND status_code = 'A'
        LIMIT 5
    """
    
    samples = await db_pool.fetch(sample_query)
    
    print(f"\n📋 Sample ACTIVE Puget Sound Contractors:")
    for sample in samples:
        print(f"   - {sample['business_name']} ({sample['city']}, {sample['state']}) - Status: {sample['status_code']}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(test_active_contractors()) 