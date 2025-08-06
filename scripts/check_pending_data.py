#!/usr/bin/env python3
"""
Check Pending Records for Partial Data
=====================================

Check if pending records have any partial data from previous processing attempts.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_pending_data():
    """Check if pending records have partial data"""
    await db_pool.initialize()
    
    print("🔍 PENDING RECORDS DATA ANALYSIS")
    print("=" * 50)
    
    # Check for pending records with partial data
    partial_data_query = """
        SELECT 
            COUNT(*) as total_pending,
            COUNT(CASE WHEN website_url IS NOT NULL AND website_url != '' THEN 1 END) as with_websites,
            COUNT(CASE WHEN confidence_score IS NOT NULL AND confidence_score > 0 THEN 1 END) as with_confidence,
            COUNT(CASE WHEN mailer_category IS NOT NULL AND mailer_category != '' THEN 1 END) as with_categories,
            COUNT(CASE WHEN website_confidence IS NOT NULL THEN 1 END) as with_website_confidence,
            COUNT(CASE WHEN classification_confidence IS NOT NULL THEN 1 END) as with_classification_confidence
        FROM contractors 
        WHERE processing_status = 'pending'
    """
    
    partial_data = await db_pool.fetchrow(partial_data_query)
    
    print(f"📊 Pending Records Analysis:")
    print(f"   - Total pending: {partial_data['total_pending']:,}")
    print(f"   - With websites: {partial_data['with_websites']:,}")
    print(f"   - With confidence scores: {partial_data['with_confidence']:,}")
    print(f"   - With categories: {partial_data['with_categories']:,}")
    print(f"   - With website confidence: {partial_data['with_website_confidence']:,}")
    print(f"   - With classification confidence: {partial_data['with_classification_confidence']:,}")
    
    # Check if any pending records have partial data
    has_partial_data = any([
        partial_data['with_websites'] > 0,
        partial_data['with_confidence'] > 0,
        partial_data['with_categories'] > 0,
        partial_data['with_website_confidence'] > 0,
        partial_data['with_classification_confidence'] > 0
    ])
    
    print(f"\n💡 Analysis:")
    if has_partial_data:
        print(f"   ⚠️  Some pending records have partial data from previous processing")
        print(f"   🔄 These records will be reprocessed with fresh data")
        print(f"   📝 Previous partial results will be overwritten")
    else:
        print(f"   ✅ All pending records are clean (no partial data)")
        print(f"   🚀 Ready for fresh processing")
    
    # Check Puget Sound specific data
    puget_partial_query = """
        SELECT 
            COUNT(*) as total_puget_pending,
            COUNT(CASE WHEN website_url IS NOT NULL AND website_url != '' THEN 1 END) as puget_with_websites,
            COUNT(CASE WHEN confidence_score IS NOT NULL AND confidence_score > 0 THEN 1 END) as puget_with_confidence
        FROM contractors 
        WHERE processing_status = 'pending' AND puget_sound = TRUE
    """
    
    puget_partial = await db_pool.fetchrow(puget_partial_query)
    
    print(f"\n🏔️ Puget Sound Pending Records:")
    print(f"   - Total Puget Sound pending: {puget_partial['total_puget_pending']:,}")
    print(f"   - With websites: {puget_partial['puget_with_websites']:,}")
    print(f"   - With confidence scores: {puget_partial['puget_with_confidence']:,}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_pending_data()) 