#!/usr/bin/env python3
"""
Check Google API quota status
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import quota_tracker

async def check_quota():
    """Check Google API quota status"""
    
    print("🔍 Google API Quota Status")
    print("=" * 50)
    
    # Get current quota status
    status = quota_tracker.get_quota_status()
    
    print(f"📊 Current Status:")
    print(f"   - Queries used today: {status['queries_today']:,}")
    print(f"   - Daily limit: {status['daily_limit']:,}")
    print(f"   - Remaining queries: {status['remaining_queries']:,}")
    print(f"   - Usage percentage: {status['queries_today'] / status['daily_limit'] * 100:.1f}%")
    print(f"   - Consecutive 429 errors: {status['consecutive_429_errors']}")
    print(f"   - Quota exceeded: {'Yes' if status['quota_exceeded'] else 'No'}")
    
    if status['last_429_time']:
        print(f"   - Last 429 error: {status['last_429_time']}")
    
    # Calculate processing capacity
    queries_per_contractor = 2  # Current configuration
    max_contractors = status['remaining_queries'] // queries_per_contractor
    
    print(f"\n🎯 Processing Capacity:")
    print(f"   - Queries per contractor: {queries_per_contractor}")
    print(f"   - Max contractors today: {max_contractors:,}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if status['quota_exceeded']:
        print("   ❌ Daily quota exceeded - cannot process more contractors today")
    elif status['remaining_queries'] < 1000:
        print("   ⚠️  Very low quota remaining - consider waiting until tomorrow")
    elif status['remaining_queries'] < 5000:
        print("   ⚠️  Moderate quota remaining - use smaller batches")
    else:
        print("   ✅ Plenty of quota remaining")

if __name__ == "__main__":
    asyncio.run(check_quota()) 