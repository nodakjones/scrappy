#!/usr/bin/env python3
"""
Show Recent Puget Sound Contractors
==================================

Display a table of recent Puget Sound contractors with their details.

USAGE:
    python scripts/show_puget_sound_contractors.py --limit 50
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from tabulate import tabulate

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def show_puget_sound_contractors(limit: int = 50):
    """Show recent Puget Sound contractors in a table"""
    
    print("🏔️ RECENT PUGET SOUND CONTRACTORS")
    print("=" * 60)
    print(f"📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    await db_pool.initialize()
    
    try:
        # Get recent Puget Sound contractors
        contractors = await db_pool.fetch('''
            SELECT 
                business_name,
                city,
                state,
                website_url,
                mailer_category,
                confidence_score,
                processing_status,
                review_status,
                created_at
            FROM contractors 
            WHERE puget_sound = TRUE 
            ORDER BY created_at DESC 
            LIMIT $1
        ''', limit)
        
        if not contractors:
            print("❌ No Puget Sound contractors found!")
            return
        
        print(f"📊 Found {len(contractors)} recent Puget Sound contractors")
        print()
        
        # Prepare table data
        table_data = []
        for contractor in contractors:
            # Clean up website URL for display
            website = contractor['website_url'] or "None"
            if website and len(website) > 50:
                website = website[:47] + "..."
            
            # Clean up business name for display
            business_name = contractor['business_name']
            if len(business_name) > 30:
                business_name = business_name[:27] + "..."
            
            # Get category
            category = contractor['mailer_category'] or "General Contractor"
            
            # Get confidence score
            confidence = contractor['confidence_score'] or 0.0
            
            # Get status
            status = contractor['processing_status'] or "unknown"
            
            table_data.append([
                business_name,
                f"{contractor['city']}, {contractor['state']}",
                website,
                category,
                f"{confidence:.2f}",
                status
            ])
        
        # Display table
        headers = ["Business Name", "Location", "Website", "Category", "Confidence", "Status"]
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 20, 50, 25, 10, 15]))
        
        # Show summary statistics
        print()
        print("📈 SUMMARY STATISTICS:")
        print("=" * 40)
        
        # Count by category
        categories = {}
        for contractor in contractors:
            category = contractor['mailer_category'] or "General Contractor"
            categories[category] = categories.get(category, 0) + 1
        
        print("📂 Category Distribution:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Count by confidence level
        high_conf = sum(1 for c in contractors if (c['confidence_score'] or 0) >= 0.8)
        med_conf = sum(1 for c in contractors if 0.6 <= (c['confidence_score'] or 0) < 0.8)
        low_conf = sum(1 for c in contractors if (c['confidence_score'] or 0) < 0.6)
        
        print(f"\n🎯 Confidence Distribution:")
        print(f"  High (≥0.8): {high_conf}")
        print(f"  Medium (0.6-0.79): {med_conf}")
        print(f"  Low (<0.6): {low_conf}")
        
        # Count by status
        statuses = {}
        for contractor in contractors:
            status = contractor['processing_status'] or "unknown"
            statuses[status] = statuses.get(status, 0) + 1
        
        print(f"\n🔄 Processing Status:")
        for status, count in sorted(statuses.items()):
            print(f"  {status}: {count}")
        
        # Count with websites
        with_websites = sum(1 for c in contractors if c['website_url'])
        print(f"\n🌐 Website Discovery:")
        print(f"  With websites: {with_websites}/{len(contractors)} ({with_websites/len(contractors)*100:.1f}%)")
        
    finally:
        await db_pool.close()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Show Recent Puget Sound Contractors")
    parser.add_argument("--limit", type=int, default=50, help="Number of contractors to show")
    
    args = parser.parse_args()
    
    await show_puget_sound_contractors(args.limit)

if __name__ == "__main__":
    asyncio.run(main()) 