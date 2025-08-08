#!/usr/bin/env python3
"""
Reset Zero Confidence Contractors
================================

Reset contractors that have websites but 0 confidence scores.
These are likely from previous batches where the HTTP status code bug
caused valid websites to be marked as crawl failures.

USAGE:
    python scripts/reset_zero_confidence_contractors.py --confirm
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def reset_zero_confidence_contractors(confirm: bool = False):
    """Reset contractors with websites but 0 confidence scores"""
    
    print("🔄 RESET ZERO CONFIDENCE CONTRACTORS")
    print("=" * 50)
    print(f"📅 Reset at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    await db_pool.initialize()
    
    try:
        # Get count of contractors with websites but 0 confidence
        target_count = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'completed'
            AND website_url IS NOT NULL
            AND website_url != ''
            AND (confidence_score = 0 OR confidence_score IS NULL)
        ''')
        
        print(f"📊 Found {target_count['count']} contractors with websites but 0 confidence")
        print()
        
        if target_count['count'] == 0:
            print("✅ No contractors found that need resetting!")
            return
        
        if not confirm:
            print("⚠️  WARNING: This will reset contractors with websites but 0 confidence!")
            print("   - Website URLs will be cleared")
            print("   - Confidence scores will be reset")
            print("   - Categories will be cleared")
            print("   - Processing status will be set to 'pending'")
            print()
            print(f"   Use --confirm to reset {target_count['count']} contractors")
            return
        
        # Reset the target contractors
        result = await db_pool.execute('''
            UPDATE contractors 
            SET 
                processing_status = 'pending',
                confidence_score = NULL,
                website_confidence = NULL,
                classification_confidence = NULL,
                website_url = NULL,
                website_status = NULL,
                mailer_category = NULL,
    
                data_sources = NULL,
                review_status = NULL,
                last_processed = NULL,
                error_message = NULL,
                updated_at = NOW()
            WHERE processing_status = 'completed'
            AND website_url IS NOT NULL
            AND website_url != ''
            AND (confidence_score = 0 OR confidence_score IS NULL)
        ''')
        
        print(f"✅ Reset {result} contractors successfully!")
        print()
        
        # Verify the reset
        pending_count = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'pending'
        ''')
        
        completed_count = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'completed'
        ''')
        
        print("📈 VERIFICATION:")
        print(f"  Pending contractors: {pending_count['count']}")
        print(f"  Completed contractors: {completed_count['count']}")
        print()
        
        # Show Puget Sound breakdown
        puget_pending = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'pending' AND puget_sound = TRUE
        ''')
        
        print("🌊 PUGET SOUND BREAKDOWN:")
        print(f"  Puget Sound pending: {puget_pending['count']}")
        print()
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        raise
    finally:
        await db_pool.close()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset contractors with websites but 0 confidence')
    parser.add_argument('--confirm', action='store_true', help='Confirm the reset operation')
    
    args = parser.parse_args()
    
    await reset_zero_confidence_contractors(args.confirm)

if __name__ == '__main__':
    asyncio.run(main()) 