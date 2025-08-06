#!/usr/bin/env python3
"""
Check Status Codes
=================

Check the distribution of status codes in the contractors table.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_status_codes():
    """Check the distribution of status codes"""
    await db_pool.initialize()
    
    print("🔍 CONTRACTOR STATUS CODE DISTRIBUTION")
    print("=" * 50)
    
    # Get status code distribution
    status_query = """
        SELECT status_code, COUNT(*) as count 
        FROM contractors 
        GROUP BY status_code 
        ORDER BY count DESC
    """
    
    status_codes = await db_pool.fetch(status_query)
    
    print(f"📊 Status Code Distribution:")
    total = 0
    for status in status_codes:
        code = status['status_code'] or 'NULL'
        count = status['count']
        total += count
        print(f"   - {code}: {count:,}")
    
    print(f"\n📈 Total Records: {total:,}")
    
    # Check how many are ACTIVE
    active_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE status_code = 'ACTIVE'
    """
    
    active_count = await db_pool.fetchrow(active_query)
    active_total = active_count['count']
    
    print(f"\n✅ ACTIVE Records: {active_total:,}")
    print(f"📊 Percentage: {active_total / total * 100:.1f}%")
    
    # Check pending ACTIVE records
    pending_active_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE status_code = 'ACTIVE' AND processing_status = 'pending'
    """
    
    pending_active = await db_pool.fetchrow(pending_active_query)
    pending_active_count = pending_active['count']
    
    print(f"\n⏳ Pending ACTIVE Records: {pending_active_count:,}")
    
    # Check Puget Sound ACTIVE records
    puget_active_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE status_code = 'ACTIVE' AND puget_sound = TRUE
    """
    
    puget_active = await db_pool.fetchrow(puget_active_query)
    puget_active_count = puget_active['count']
    
    print(f"🏔️ Puget Sound ACTIVE Records: {puget_active_count:,}")
    
    # Check what status codes mean by looking at some examples
    print(f"\n🔍 Status Code Examples:")
    for status in status_codes[:5]:  # Show top 5 status codes
        code = status['status_code']
        if code:
            # Get a sample record for each status code
            sample_query = """
                SELECT business_name, contractor_license_status, status_code 
                FROM contractors 
                WHERE status_code = $1 
                LIMIT 1
            """
            sample = await db_pool.fetchrow(sample_query, code)
            if sample:
                print(f"   - {code}: {sample['business_name']} (License: {sample['contractor_license_status']})")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_status_codes()) 