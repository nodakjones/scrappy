#!/usr/bin/env python3
"""
Export Records with Websites Found
=================================

Export all contractor records where websites have been discovered.
"""

import asyncio
import sys
import os
import csv
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def export_websites_found():
    """Export all records where websites have been found"""
    await db_pool.initialize()
    
    print("📤 EXPORTING RECORDS WITH WEBSITES FOUND")
    print("=" * 50)
    
    # Get all records with websites
    websites_query = """
        SELECT 
            id,
            business_name,
            city,
            state,
            zip,
            website_url,
            website_status,
            confidence_score,
            website_confidence,
            classification_confidence,
            mailer_category,
                            residential_focus,
            processing_status,
            review_status,
            puget_sound,
            created_at,
            updated_at
        FROM contractors 
        WHERE website_url IS NOT NULL 
        AND website_url != ''
        ORDER BY confidence_score DESC NULLS LAST, business_name
    """
    
    records = await db_pool.fetch(websites_query)
    
    print(f"📊 Found {len(records):,} records with websites")
    
    if not records:
        print("❌ No records with websites found")
        await db_pool.close()
        return
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"exports/websites_found_{timestamp}.csv"
    
    # Create exports directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'business_name', 'city', 'state', 'zip',
            'website_url', 'website_status', 'confidence_score',
            'website_confidence', 'classification_confidence',
            'mailer_category', 'residential_focus', 'processing_status',
            'review_status', 'puget_sound', 'created_at', 'updated_at'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow(dict(record))
    
    print(f"✅ Exported {len(records):,} records to: {filename}")
    
    # Show summary statistics
    print(f"\n📊 Export Summary:")
    
    # Count by review status
    approved = sum(1 for r in records if r['review_status'] == 'approved_download')
    pending_review = sum(1 for r in records if r['review_status'] == 'pending_review')
    rejected = sum(1 for r in records if r['review_status'] == 'rejected')
    
    print(f"   - Approved for download: {approved:,}")
    print(f"   - Pending review: {pending_review:,}")
    print(f"   - Rejected: {rejected:,}")
    
    # Count by confidence level
    high_conf = sum(1 for r in records if r['confidence_score'] and r['confidence_score'] >= 0.8)
    med_conf = sum(1 for r in records if r['confidence_score'] and 0.6 <= r['confidence_score'] < 0.8)
    low_conf = sum(1 for r in records if r['confidence_score'] and r['confidence_score'] < 0.6)
    
    print(f"\n🎯 Confidence Distribution:")
    print(f"   - High confidence (≥0.8): {high_conf:,}")
    print(f"   - Medium confidence (0.6-0.79): {med_conf:,}")
    print(f"   - Low confidence (<0.6): {low_conf:,}")
    
    # Count by region
    puget_sound = sum(1 for r in records if r['puget_sound'])
    other_regions = len(records) - puget_sound
    
    print(f"\n🏔️ Regional Distribution:")
    print(f"   - Puget Sound: {puget_sound:,}")
    print(f"   - Other regions: {other_regions:,}")
    
    # Top categories
    categories = {}
    for record in records:
        category = record['mailer_category'] or 'Unknown'
        categories[category] = categories.get(category, 0) + 1
    
    print(f"\n📂 Top Categories:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {category}: {count:,}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(export_websites_found()) 