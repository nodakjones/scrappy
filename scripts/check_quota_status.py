#!/usr/bin/env python3
"""
Google API Quota Status Checker
===============================

Check current Google API quota usage and provide recommendations for processing.

USAGE:
    python scripts/check_quota_status.py

This script provides:
- Current quota usage statistics
- Recommendations for batch sizes
- Quota reset timing
- Processing capacity estimates
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append('src')

from src.services.contractor_service import quota_tracker

async def main():
    """Check and display quota status"""
    print("🔍 Google API Quota Status Checker")
    print("=" * 50)
    
    # Get current quota status
    status = quota_tracker.get_quota_status()
    
    # Display current status
    print(f"📊 Current Status:")
    print(f"   - Queries used today: {status['queries_today']:,}")
    print(f"   - Daily limit: {status['daily_limit']:,}")
    print(f"   - Remaining queries: {status['remaining_queries']:,}")
    print(f"   - Usage percentage: {status['queries_today'] / status['daily_limit'] * 100:.1f}%")
    print(f"   - Consecutive 429 errors: {status['consecutive_429_errors']}")
    print(f"   - Quota exceeded: {'Yes' if status['quota_exceeded'] else 'No'}")
    
    if status['last_429_time']:
        print(f"   - Last 429 error: {status['last_429_time']}")
    
    print()
    
    # Calculate processing capacity
    queries_per_contractor = 2  # Current configuration
    max_contractors = status['remaining_queries'] // queries_per_contractor
    
    print(f"🎯 Processing Capacity:")
    print(f"   - Queries per contractor: {queries_per_contractor}")
    print(f"   - Max contractors today: {max_contractors:,}")
    print(f"   - Recommended batch size: {min(5000, max_contractors):,}")
    
    # Recommendations
    print()
    print(f"💡 Recommendations:")
    
    if status['quota_exceeded']:
        print("   ❌ Daily quota exceeded - cannot process more contractors today")
        print("   ⏰ Wait until tomorrow to continue processing")
    elif status['remaining_queries'] < 1000:
        print("   ⚠️  Very low quota remaining - consider waiting until tomorrow")
        print(f"   📦 Maximum safe batch: {max_contractors:,} contractors")
    elif status['remaining_queries'] < 5000:
        print("   ⚠️  Moderate quota remaining - use smaller batches")
        print(f"   📦 Recommended batch: {max_contractors:,} contractors")
    else:
        print("   ✅ Plenty of quota remaining")
        print(f"   📦 Safe to process: {max_contractors:,} contractors")
    
    # Quota reset timing
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    reset_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_reset = reset_time - now
    
    print()
    print(f"⏰ Quota Reset:")
    print(f"   - Next reset: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - Time until reset: {time_until_reset}")
    
    # Processing timeline
    if not status['quota_exceeded'] and max_contractors > 0:
        print()
        print(f"📈 Processing Timeline:")
        print(f"   - Daily capacity: {max_contractors:,} contractors")
        print(f"   - Puget Sound total: 83,879 contractors")
        print(f"   - Days to complete Puget Sound: {83879 // max_contractors + 1}")
    
    # Command suggestions
    print()
    print(f"🚀 Suggested Commands:")
    
    if status['quota_exceeded']:
        print("   # Wait until tomorrow, then run:")
        print("   docker-compose exec app python scripts/run_parallel_test.py")
    elif max_contractors >= 5000:
        print("   # Full daily batch:")
        print("   docker-compose exec app python scripts/run_parallel_test.py")
        print()
        print("   # Smaller test batch:")
        print("   docker-compose exec app python scripts/run_parallel_test.py --limit 1000")
    else:
        print(f"   # Reduced batch size ({max_contractors:,} contractors):")
        print(f"   docker-compose exec app python scripts/run_parallel_test.py --limit {max_contractors}")
    
    print()
    print("📋 Other useful commands:")
    print("   # Check processing status:")
    print("   docker-compose exec app python scripts/check_results.py")
    print()
    print("   # View recent processed contractors:")
    print("   docker-compose exec app python scripts/show_processed_puget_sound.py")
    print()
    print("   # Check for errors:")
    print("   docker-compose exec app python scripts/check_logs.py")

if __name__ == "__main__":
    asyncio.run(main()) 