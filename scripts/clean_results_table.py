#!/usr/bin/env python3
"""
Display processed contractor results in a clean, readable table format.
"""

import asyncio
import sys
import os
from datetime import datetime
from tabulate import tabulate

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def display_clean_results():
    """Display processed contractor results in a clean table"""
    print("📊 PROCESSED CONTRACTOR RESULTS")
    print("=" * 60)
    
    # Initialize database
    await db_pool.initialize()
    
    try:
        # Get processed contractors
        async with db_pool.pool.acquire() as conn:
            result = await conn.fetch('''
                SELECT business_name, website_url, mailer_category, confidence_score, 
                       city, state, review_status, is_home_contractor
                FROM contractors 
                WHERE processing_status = 'completed' 
                ORDER BY confidence_score DESC, business_name
                LIMIT 100
            ''')
        
        if not result:
            print("❌ No processed contractors found!")
            return
        
        print(f"📋 Found {len(result)} processed contractors")
        print()
        
        # Prepare data for table
        table_data = []
        for row in result:
            business_name = row[0]
            website_url = row[1] or "None"
            category = row[2] or "None"
            confidence = row[3] or 0.0
            location = f"{row[4]}, {row[5]}" if row[4] and row[5] else "Unknown"
            review_status = row[6] or "unknown"
            is_home = "Yes" if row[7] else "No"
            
            # Truncate long values for better display
            business_name = business_name[:30] + "..." if len(business_name) > 30 else business_name
            website_url = website_url[:35] + "..." if len(website_url) > 35 else website_url
            category = category[:20] + "..." if len(category) > 20 else category
            
            table_data.append([
                business_name,
                website_url,
                category,
                f"{confidence:.2f}",
                location,
                review_status,
                is_home
            ])
        
        # Display table
        headers = ["Business Name", "Website", "Category", "Confidence", "Location", "Review Status", "Home Contractor"]
        table = tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 35, 20, 10, 20, 12, 8])
        print(table)
        
        # Summary statistics
        print(f"\n📈 SUMMARY STATISTICS")
        print("=" * 40)
        
        # Count by category
        categories = {}
        for row in result:
            category = row[2] or "None"
            categories[category] = categories.get(category, 0) + 1
        
        print("Category Distribution:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Confidence distribution
        high_conf = sum(1 for r in result if (r[3] or 0) >= 0.8)
        med_conf = sum(1 for r in result if 0.6 <= (r[3] or 0) < 0.8)
        low_conf = sum(1 for r in result if (r[3] or 0) < 0.6)
        
        print(f"\nConfidence Distribution:")
        print(f"  High (≥0.8): {high_conf}")
        print(f"  Medium (0.6-0.79): {med_conf}")
        print(f"  Low (<0.6): {low_conf}")
        
        # Website discovery rate
        websites_found = sum(1 for r in result if r[1] and r[1] != "None")
        print(f"\nWebsite Discovery Rate: {websites_found}/{len(result)} ({websites_found/len(result)*100:.1f}%)")
        
        # Review status distribution
        review_statuses = {}
        for row in result:
            status = row[6] or "unknown"
            review_statuses[status] = review_statuses.get(status, 0) + 1
        
        print(f"\nReview Status Distribution:")
        for status, count in sorted(review_statuses.items()):
            print(f"  {status}: {count}")
        
        # Home contractor rate
        home_contractors = sum(1 for r in result if r[7])
        print(f"\nHome Contractor Rate: {home_contractors}/{len(result)} ({home_contractors/len(result)*100:.1f}%)")
        
        print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(display_clean_results()) 