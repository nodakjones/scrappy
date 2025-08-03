#!/usr/bin/env python3
"""
Extract and display all 100 test results in a clean table format.
"""

import asyncio
import sys
import os
from datetime import datetime
from tabulate import tabulate

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService

async def extract_all_results():
    """Extract all processed contractors and display in table format"""
    print("📊 EXTRACTING ALL PROCESSED RESULTS")
    print("=" * 60)
    
    # Initialize database and service
    await db_pool.initialize()
    service = ContractorService()
    
    try:
        # Get all contractors that have been processed (completed status)
        async with db_pool.pool.acquire() as conn:
            result = await conn.fetch('''
                SELECT business_name, website_url, mailer_category, confidence_score, 
                       city, state, review_status, is_home_contractor, processing_status
                FROM contractors 
                WHERE processing_status = 'completed' 
                ORDER BY last_processed DESC 
                LIMIT 100
            ''')
            
            # Convert to simple objects
            contractors = []
            for row in result:
                contractor = type('Contractor', (), {
                    'business_name': row[0],
                    'website_url': row[1],
                    'mailer_category': row[2],
                    'confidence_score': row[3],
                    'city': row[4],
                    'state': row[5],
                    'review_status': row[6],
                    'is_home_contractor': row[7],
                    'processing_status': row[8]
                })()
                contractors.append(contractor)
        
        if not contractors:
            print("❌ No contractors found!")
            return
        
        print(f"📋 Found {len(contractors)} contractors to analyze")
        print()
        
        # Extract results
        results = []
        for i, contractor in enumerate(contractors, 1):
            # Extract results
            website_url = contractor.website_url or "None"
            confidence = contractor.confidence_score or 0.0
            status = contractor.processing_status or "unknown"
            category = contractor.mailer_category or "None"
            is_home = "Yes" if contractor.is_home_contractor else "No"
            review_status = contractor.review_status or "unknown"
            
            results.append([
                contractor.business_name,
                website_url[:40] + "..." if len(website_url) > 40 else website_url,
                category,
                f"{confidence:.2f}",
                f"{contractor.city}, {contractor.state}",
                review_status,
                is_home
            ])
        
        # Display results table
        print(f"\n📊 ALL {len(results)} RESULTS")
        print("=" * 60)
        
        headers = ["Business Name", "Website", "Category", "Confidence", "Location", "Review Status", "Home Contractor"]
        table = tabulate(results, headers=headers, tablefmt="grid", maxcolwidths=[25, 30, 15, 10, 20, 12, 8])
        print(table)
        
        # Summary statistics
        print(f"\n📈 SUMMARY STATISTICS")
        print("=" * 40)
        
        # Count by category
        categories = {}
        for result in results:
            category = result[2]
            categories[category] = categories.get(category, 0) + 1
        
        print("Category Distribution:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Confidence distribution
        high_conf = sum(1 for r in results if float(r[3]) >= 0.8)
        med_conf = sum(1 for r in results if 0.6 <= float(r[3]) < 0.8)
        low_conf = sum(1 for r in results if float(r[3]) < 0.6)
        
        print(f"\nConfidence Distribution:")
        print(f"  High (≥0.8): {high_conf}")
        print(f"  Medium (0.6-0.79): {med_conf}")
        print(f"  Low (<0.6): {low_conf}")
        
        # Website discovery rate
        websites_found = sum(1 for r in results if r[1] != "None")
        print(f"\nWebsite Discovery Rate: {websites_found}/{len(results)} ({websites_found/len(results)*100:.1f}%)")
        
        # Review status distribution
        review_statuses = {}
        for result in results:
            status = result[5]
            review_statuses[status] = review_statuses.get(status, 0) + 1
        
        print(f"\nReview Status Distribution:")
        for status, count in sorted(review_statuses.items()):
            print(f"  {status}: {count}")
        
        # Home contractor rate
        home_contractors = sum(1 for r in results if r[6] == "Yes")
        print(f"\nHome Contractor Rate: {home_contractors}/{len(results)} ({home_contractors/len(results)*100:.1f}%)")
        
        print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(extract_all_results()) 