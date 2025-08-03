#!/usr/bin/env python3
"""
Update Puget Sound contractors based on zip codes
================================================

This script updates the puget_sound column for all contractors based on their zip codes.
It uses the PUGET_SOUND_ZIP_CODES from the config to identify Puget Sound contractors.

USAGE:
    python scripts/update_puget_sound_contractors.py

FEATURES:
    - Updates all 150k+ contractors in batches
    - Shows progress and statistics
    - Handles missing/invalid zip codes gracefully
    - Creates summary report
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.config import PUGET_SOUND_ZIP_CODES

async def update_puget_sound_contractors():
    """Update all contractors with puget_sound flag based on zip codes"""
    
    print("🏔️ PUGET SOUND CONTRACTOR UPDATE")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize database connection
    await db_pool.initialize()
    
    try:
        # Get total contractor count
        total_contractors = await db_pool.fetchrow('SELECT COUNT(*) as count FROM contractors')
        total_count = total_contractors['count']
        
        print(f"📊 Total contractors to process: {total_count:,}")
        print(f"📍 Puget Sound zip codes: {len(PUGET_SOUND_ZIP_CODES)}")
        print()
        
        # Process in batches for efficiency
        batch_size = 1000
        processed = 0
        puget_sound_count = 0
        invalid_zip_count = 0
        
        # Get contractors in batches
        offset = 0
        
        while offset < total_count:
            # Get batch of contractors
            contractors = await db_pool.fetch('''
                SELECT id, zip, business_name, city, state 
                FROM contractors 
                ORDER BY id 
                LIMIT $1 OFFSET $2
            ''', batch_size, offset)
            
            if not contractors:
                break
                
            # Process batch
            updates = []
            for contractor in contractors:
                processed += 1
                
                # Extract zip code (handle various formats)
                zip_code = contractor['zip']
                if not zip_code:
                    invalid_zip_count += 1
                    continue
                
                # Clean zip code (remove spaces, take first 5 digits)
                zip_clean = str(zip_code).strip().split('-')[0][:5]
                
                # Check if it's a Puget Sound zip code
                is_puget_sound = int(zip_clean) in PUGET_SOUND_ZIP_CODES if zip_clean.isdigit() else False
                
                if is_puget_sound:
                    puget_sound_count += 1
                    updates.append(contractor['id'])
                
                # Show progress every 1000 contractors
                if processed % 1000 == 0:
                    print(f"  Processed: {processed:,}/{total_count:,} ({processed/total_count*100:.1f}%)")
                    print(f"  Puget Sound found: {puget_sound_count:,}")
                    print(f"  Invalid zips: {invalid_zip_count:,}")
                    print()
            
            # Update batch in database
            if updates:
                await db_pool.execute('''
                    UPDATE contractors 
                    SET puget_sound = TRUE 
                    WHERE id = ANY($1)
                ''', updates)
            
            offset += batch_size
        
        # Get final statistics
        final_stats = await db_pool.fetchrow('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN puget_sound = TRUE THEN 1 END) as puget_sound_count,
                COUNT(CASE WHEN puget_sound = FALSE THEN 1 END) as non_puget_sound_count,
                COUNT(CASE WHEN zip IS NULL OR zip = '' THEN 1 END) as no_zip_count
            FROM contractors
        ''')
        
        print("📊 FINAL RESULTS")
        print("=" * 50)
        print(f"✅ Total contractors processed: {final_stats['total']:,}")
        print(f"🏔️ Puget Sound contractors: {final_stats['puget_sound_count']:,}")
        print(f"🌍 Non-Puget Sound contractors: {final_stats['non_puget_sound_count']:,}")
        print(f"❓ No zip code: {final_stats['no_zip_count']:,}")
        print()
        
        # Calculate percentages
        total = final_stats['total']
        puget_percentage = (final_stats['puget_sound_count'] / total * 100) if total > 0 else 0
        print(f"📈 Puget Sound percentage: {puget_percentage:.1f}%")
        print()
        
        # Show some examples
        print("🏔️ SAMPLE PUGET SOUND CONTRACTORS:")
        sample_contractors = await db_pool.fetch('''
            SELECT business_name, city, state, zip 
            FROM contractors 
            WHERE puget_sound = TRUE 
            LIMIT 5
        ''')
        
        for contractor in sample_contractors:
            print(f"  • {contractor['business_name']} - {contractor['city']}, {contractor['state']} {contractor['zip']}")
        
        print()
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Puget Sound contractor update completed successfully!")
        
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(update_puget_sound_contractors()) 