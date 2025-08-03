#!/usr/bin/env python3
"""
Check review status assignment for high confidence contractors
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_review_status():
    """Check review status assignment"""
    await db_pool.initialize()
    
        # Check high confidence contractors without review status
    high_confidence_null = await db_pool.fetchrow('''
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE confidence_score >= 0.8 AND review_status IS NULL
    ''')
    
    # Check all high confidence contractors
    high_confidence_total = await db_pool.fetchrow('''
        SELECT COUNT(*) as count 
        FROM contractors 
        WHERE confidence_score >= 0.8
    ''')
    
    # Check review status distribution for high confidence
    review_distribution = await db_pool.fetch('''
        SELECT review_status, COUNT(*) as count 
        FROM contractors 
        WHERE confidence_score >= 0.8 
        GROUP BY review_status
    ''')
    
    print("🔍 REVIEW STATUS ANALYSIS")
    print("=" * 50)
    print(f"📅 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 HIGH CONFIDENCE CONTRACTORS (≥0.8):")
    print(f"  Total High Confidence: {high_confidence_total['count']}")
    print(f"  ❌ No Review Status: {high_confidence_null['count']}")
    print()
    
    print("📋 REVIEW STATUS DISTRIBUTION (High Confidence Only):")
    for row in review_distribution:
        status = row['review_status'] or 'NULL'
        count = row['count']
        print(f"  {status}: {count}")
    
    print()
    
    if high_confidence_null['count'] > 0:
        print("🚨 ISSUE FOUND:")
        print(f"  {high_confidence_null['count']} high confidence contractors have no review status!")
        print("  These contractors were processed before the review_status fix.")
        print("  They need to be reprocessed to get proper review status.")
    else:
        print("✅ All high confidence contractors have proper review status!")
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_review_status()) 