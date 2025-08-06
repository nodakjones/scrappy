#!/usr/bin/env python3
"""
Google API Quota Status Checker
===============================

Check current Google API quota usage and provide recommendations for processing.

USAGE:
    python scripts/check_quota_status.py

This script provides:
- Current quota usage statistics (from logs)
- Recommendations for batch sizes
- Quota reset timing
- Processing capacity estimates
"""

import asyncio
import sys
import os
import subprocess
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append('src')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import quota_tracker

def get_actual_quota_usage():
    """Get actual quota usage from processing logs"""
    try:
        # Check if we're running inside the container
        log_file = 'logs/processing.log'
        if not os.path.exists(log_file):
            # Try to run docker-compose command
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'app', 
                'grep', '-c', 'Google API Query:', 'logs/processing.log'
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                total_queries = int(result.stdout.strip())
            else:
                total_queries = 0
                
            # Count today's queries
            today = datetime.now().strftime('%Y-%m-%d')
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'app',
                'grep', f'{today}.*Google API Query:', 'logs/processing.log'
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                today_queries = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            else:
                today_queries = 0
        else:
            # Running inside container, use direct file access
            import subprocess as sp
            
            # Count total queries
            result = sp.run(['grep', '-c', 'Google API Query:', log_file], capture_output=True, text=True)
            total_queries = int(result.stdout.strip()) if result.returncode == 0 else 0
            
            # Count today's queries
            today = datetime.now().strftime('%Y-%m-%d')
            result = sp.run(['grep', f'{today}.*Google API Query:', log_file], capture_output=True, text=True)
            today_queries = len(result.stdout.strip().split('\n')) if result.stdout.strip() and result.returncode == 0 else 0
            
        return {
            'total_queries': total_queries,
            'today_queries': today_queries,
            'daily_limit': 10000
        }
    except Exception as e:
        print(f"Error getting quota usage: {e}")
        return {
            'total_queries': 0,
            'today_queries': 0,
            'daily_limit': 10000
        }

async def main():
    """Check and display quota status"""
    print("🔍 Google API Quota Status Checker")
    print("=" * 50)
    
    # Get actual usage from logs
    actual_usage = get_actual_quota_usage()
    
    # Get in-memory tracker status
    tracker_status = quota_tracker.get_quota_status()
    
    print(f"📊 Current Status (from logs):")
    print(f"   - Queries used today: {actual_usage['today_queries']:,}")
    print(f"   - Total queries (all time): {actual_usage['total_queries']:,}")
    print(f"   - Daily limit: {actual_usage['daily_limit']:,}")
    print(f"   - Remaining queries: {actual_usage['daily_limit'] - actual_usage['today_queries']:,}")
    print(f"   - Usage percentage: {actual_usage['today_queries'] / actual_usage['daily_limit'] * 100:.1f}%")
    
    print(f"\n📊 In-Memory Tracker Status:")
    print(f"   - Queries used today: {tracker_status['queries_today']:,}")
    print(f"   - Consecutive 429 errors: {tracker_status['consecutive_429_errors']}")
    print(f"   - Quota exceeded: {'Yes' if tracker_status['quota_exceeded'] else 'No'}")
    
    if tracker_status['last_429_time']:
        print(f"   - Last 429 error: {tracker_status['last_429_time']}")
    
    print()
    
    # Calculate processing capacity
    queries_per_contractor = 2  # Current configuration
    remaining_queries = actual_usage['daily_limit'] - actual_usage['today_queries']
    max_contractors = remaining_queries // queries_per_contractor
    
    print(f"🎯 Processing Capacity:")
    print(f"   - Queries per contractor: {queries_per_contractor}")
    print(f"   - Max contractors today: {max_contractors:,}")
    print(f"   - Recommended batch size: {min(5000, max_contractors):,}")
    
    # Recommendations
    print()
    print(f"💡 Recommendations:")
    
    if actual_usage['today_queries'] >= actual_usage['daily_limit']:
        print("   ❌ Daily quota exceeded - cannot process more contractors today")
        print("   ⏰ Wait until tomorrow to continue processing")
    elif remaining_queries < 1000:
        print("   ⚠️  Very low quota remaining - consider waiting until tomorrow")
        print(f"   📦 Maximum safe batch: {max_contractors:,} contractors")
    elif remaining_queries < 5000:
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
    if remaining_queries > 0 and max_contractors > 0:
        print()
        print(f"📈 Processing Timeline:")
        print(f"   - Daily capacity: {max_contractors:,} contractors")
        print(f"   - Puget Sound total: 83,879 contractors")
        print(f"   - Days to complete Puget Sound: {83879 // max_contractors + 1}")
    
    # Command suggestions
    print()
    print(f"🚀 Suggested Commands:")
    
    if actual_usage['today_queries'] >= actual_usage['daily_limit']:
        print("   # Wait until tomorrow, then run:")
        print("   docker-compose exec app python scripts/run_processing.py")
    elif remaining_queries < 1000:
        print("   # Use small batch:")
        print(f"   docker-compose exec app python scripts/run_processing.py --limit {max_contractors}")
    else:
        print("   # Safe to run full processing:")
        print("   docker-compose exec app python scripts/run_processing.py")

if __name__ == "__main__":
    asyncio.run(main()) 