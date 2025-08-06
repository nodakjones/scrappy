#!/usr/bin/env python3
"""
Check Failed Records Status
==========================

Check the status of failed records and determine if they can be reprocessed.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_failed_records():
    """Check the status of failed records"""
    await db_pool.initialize()
    
    print("🔍 FAILED RECORDS ANALYSIS")
    print("=" * 50)
    
    # Get failed records by error type
    failed_query = """
        SELECT processing_status, review_status, error_message, COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'failed' 
        GROUP BY processing_status, review_status, error_message
        ORDER BY count DESC
    """
    
    failed_records = await db_pool.fetch(failed_query)
    
    print(f"📊 Failed Records by Error Type:")
    total_failed = 0
    for record in failed_records:
        error_msg = record['error_message'] or 'Unknown error'
        count = record['count']
        total_failed += count
        print(f"   - {error_msg}: {count:,} records")
    
    print(f"\n📈 Total Failed Records: {total_failed:,}")
    
    # Check for any records with error messages (regardless of status)
    error_query = """
        SELECT processing_status, error_message, COUNT(*) as count 
        FROM contractors 
        WHERE error_message IS NOT NULL AND error_message != ''
        GROUP BY processing_status, error_message
        ORDER BY count DESC
    """
    
    error_records = await db_pool.fetch(error_query)
    
    print(f"\n🔍 Records with Error Messages:")
    total_with_errors = 0
    for record in error_records:
        error_msg = record['error_message']
        count = record['count']
        status = record['processing_status']
        total_with_errors += count
        print(f"   - {error_msg} (Status: {status}): {count:,} records")
    
    print(f"\n📈 Total Records with Errors: {total_with_errors:,}")
    
    # Check processing status distribution
    status_query = """
        SELECT processing_status, COUNT(*) as count 
        FROM contractors 
        GROUP BY processing_status
        ORDER BY count DESC
    """
    
    status_records = await db_pool.fetch(status_query)
    
    print(f"\n📊 Processing Status Distribution:")
    for record in status_records:
        status = record['processing_status']
        count = record['count']
        print(f"   - {status}: {count:,} records")
    
    # Check if failed records can be reprocessed
    print(f"\n🔄 Reprocessing Status:")
    
    # Count records that can be reprocessed (failed status)
    reprocessable_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'failed'
    """
    
    reprocessable = await db_pool.fetchrow(reprocessable_query)
    reprocessable_count = reprocessable['count']
    
    print(f"   - Records that can be reprocessed: {reprocessable_count:,}")
    
    if reprocessable_count > 0:
        print(f"   ✅ These records will be reprocessed in the next batch")
        print(f"   📝 They are marked as 'failed' and will be picked up as 'pending'")
    else:
        print(f"   ❌ No failed records found")
    
    # Check current pending records
    pending_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'pending'
    """
    
    pending = await db_pool.fetchrow(pending_query)
    pending_count = pending['count']
    
    print(f"\n📋 Current Pending Records: {pending_count:,}")
    
    # Check Puget Sound pending records
    puget_pending_query = """
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE processing_status = 'pending' AND puget_sound = TRUE
    """
    
    puget_pending = await db_pool.fetchrow(puget_pending_query)
    puget_pending_count = puget_pending['count']
    
    print(f"   - Puget Sound pending: {puget_pending_count:,}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if reprocessable_count > 0:
        print(f"   ✅ Failed records will be automatically reprocessed")
        print(f"   🚀 Run next batch: docker-compose exec app python scripts/run_parallel_test.py")
    else:
        print(f"   ℹ️  No failed records to reprocess")
    
    if puget_pending_count > 0:
        print(f"   📦 {puget_pending_count:,} Puget Sound contractors ready for processing")
    else:
        print(f"   ⚠️  No pending Puget Sound contractors found")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_failed_records()) 