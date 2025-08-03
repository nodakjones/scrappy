#!/usr/bin/env python3
"""
Reset Processed Contractors
===========================

Clear out websites, confidence ratings, and categories for processed contractors
to start fresh with updated logic.

USAGE:
    python scripts/reset_processed_contractors.py --confirm
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def reset_processed_contractors(confirm: bool = False):
    """Reset processed contractors to start fresh"""
    
    print("🔄 RESET PROCESSED CONTRACTORS")
    print("=" * 50)
    print(f"📅 Reset at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not confirm:
        print("⚠️  WARNING: This will clear all processed data!")
        print("   - Website URLs will be cleared")
        print("   - Confidence scores will be reset")
        print("   - Categories will be cleared")
        print("   - Processing status will be set to 'pending'")
        print()
        print("   Use --confirm to proceed with the reset")
        return
    
    await db_pool.initialize()
    
    try:
        # Get count of processed contractors
        processed_count = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'completed'
        ''')
        
        print(f"📊 Found {processed_count['count']} processed contractors to reset")
        print()
        
        # Reset the processed contractors
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
                is_home_contractor = NULL,
                data_sources = NULL,
                review_status = NULL,
                last_processed = NULL,
                error_message = NULL,
                updated_at = NOW()
            WHERE processing_status = 'completed'
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
        
        puget_completed = await db_pool.fetchrow('''
            SELECT COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'completed' AND puget_sound = TRUE
        ''')
        
        print("🏔️ PUGET SOUND BREAKDOWN:")
        print(f"  Pending: {puget_pending['count']}")
        print(f"  Completed: {puget_completed['count']}")
        print()
        
        print("🎯 READY FOR FRESH PROCESSING!")
        print("   All processed contractors have been reset to 'pending' status")
        print("   You can now run processing with the updated logic")
        
    finally:
        await db_pool.close()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Reset Processed Contractors")
    parser.add_argument("--confirm", action="store_true", help="Confirm the reset operation")
    
    args = parser.parse_args()
    
    await reset_processed_contractors(args.confirm)

if __name__ == "__main__":
    asyncio.run(main()) 