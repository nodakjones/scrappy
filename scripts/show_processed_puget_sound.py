#!/usr/bin/env python3
"""
Show Processed Puget Sound Contractors
"""

import asyncio
import sys
import os
from tabulate import tabulate

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def show_processed_puget_sound():
    """Show processed Puget Sound contractors"""
    
    await db_pool.initialize()
    
    try:
        # Get processed Puget Sound contractors
        contractors = await db_pool.fetch('''
            SELECT 
                business_name,
                city,
                state,
                website_url,
                mailer_category,
                confidence_score,
                website_confidence,
                classification_confidence
            FROM contractors 
            WHERE puget_sound = TRUE 
            AND processing_status = 'completed'
            ORDER BY last_processed DESC 
            LIMIT 20
        ''')
        
        print("🏔️ PROCESSED PUGET SOUND CONTRACTORS")
        print("=" * 60)
        print(f"📊 Found {len(contractors)} processed contractors")
        print()
        
        if not contractors:
            print("❌ No processed Puget Sound contractors found!")
            return
        
        # Prepare table data
        table_data = []
        for contractor in contractors:
            # Clean up business name
            business_name = contractor['business_name']
            if len(business_name) > 25:
                business_name = business_name[:22] + "..."
            
            # Clean up website URL
            website = contractor['website_url'] or "None"
            if website and len(website) > 40:
                website = website[:37] + "..."
            
            # Get category
            category = contractor['mailer_category'] or "General Contractor"
            if len(category) > 20:
                category = category[:17] + "..."
            
            # Get confidence scores
            overall_confidence = contractor['confidence_score'] or 0.0
            website_confidence = contractor['website_confidence'] or 0.0
            classification_confidence = contractor['classification_confidence'] or 0.0
            
            table_data.append([
                business_name,
                f"{contractor['city']}, {contractor['state']}",
                website,
                category,
                f"{overall_confidence:.2f}",
                f"{website_confidence:.2f}",
                f"{classification_confidence:.2f}"
            ])
        
        # Display table
        headers = ["Business Name", "Location", "Website", "Category", "Overall", "Website", "AI Class"]
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[25, 15, 40, 20, 8, 8, 8]))
        
        # Show summary
        print()
        print("📈 SUMMARY:")
        print("=" * 30)
        
        # Count by category
        categories = {}
        for contractor in contractors:
            category = contractor['mailer_category'] or "General Contractor"
            categories[category] = categories.get(category, 0) + 1
        
        print("📂 Categories:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Count with websites
        with_websites = sum(1 for c in contractors if c['website_url'])
        print(f"\n🌐 Website Discovery:")
        print(f"  With websites: {with_websites}/{len(contractors)} ({with_websites/len(contractors)*100:.1f}%)")
        
        # Count high confidence
        high_conf = sum(1 for c in contractors if (c['confidence_score'] or 0) >= 0.8)
        print(f"\n🎯 High Confidence (≥0.8): {high_conf}/{len(contractors)} ({high_conf/len(contractors)*100:.1f}%)")
        
        # Average confidence scores
        avg_overall = sum(c['confidence_score'] or 0 for c in contractors) / len(contractors)
        avg_website = sum(c['website_confidence'] or 0 for c in contractors) / len(contractors)
        avg_classification = sum(c['classification_confidence'] or 0 for c in contractors) / len(contractors)
        
        print(f"\n📊 Average Confidence Scores:")
        print(f"  Overall: {avg_overall:.2f}")
        print(f"  Website Discovery: {avg_website:.2f}")
        print(f"  AI Classification: {avg_classification:.2f}")
        
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(show_processed_puget_sound()) 