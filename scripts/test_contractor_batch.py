#!/usr/bin/env python3
"""
Test script to process 10 pending contractors and display results with city information.
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

async def test_batch_with_city(limit=10):
    """Process pending contractors and display results with city info"""
    print("🚀 Starting batch test with city information...")
    print("=" * 60)
    
    # Initialize database and service
    await db_pool.initialize()
    service = ContractorService()
    
    try:
        # Get pending contractors
        contractors = await service.get_pending_contractors(limit=limit)
        
        if not contractors:
            print("❌ No pending contractors found!")
            return
        
        print(f"📋 Found {len(contractors)} pending contractors to process")
        print()
        
        # Process each contractor
        results = []
        for i, contractor in enumerate(contractors, 1):
            print(f"Processing {i}/{len(contractors)}: {contractor.business_name} ({contractor.city}, {contractor.state})")
            
            # Process the contractor
            processed_contractor = await service.process_contractor(contractor)
            
            # Extract results
            website_url = processed_contractor.website_url or "None"
            confidence = processed_contractor.confidence_score or 0.0
            status = processed_contractor.processing_status or "unknown"
            category = processed_contractor.mailer_category or "None"
            is_home = "Yes" if processed_contractor.is_home_contractor else "No"
            
            results.append([
                processed_contractor.business_name,
                website_url[:50] + "..." if len(website_url) > 50 else website_url,
                category,
                f"{confidence:.2f}",
                f"{processed_contractor.city}, {processed_contractor.state}",
                processed_contractor.review_status or "unknown",
                "Yes" if processed_contractor.is_home_contractor else "No"
            ])
            
            print(f"   ✅ Completed: {category} | Confidence: {confidence:.2f} | Website: {website_url}")
        
        # Display results table
        print("\n" + "=" * 60)
        print("📊 BATCH TEST RESULTS")
        print("=" * 60)
        
        headers = ["Business Name", "Website", "Category", "Overall Confidence", "City", "Review Status", "Home Contractor"]
        table = tabulate(results, headers=headers, tablefmt="grid", maxcolwidths=[25, 30, 15, 10, 20, 12, 8])
        print(table)
        
        # Summary statistics
        print("\n📈 SUMMARY STATISTICS")
        print("=" * 40)
        
        # Count by category
        categories = {}
        for result in results:
            category = result[2]
            categories[category] = categories.get(category, 0) + 1
        
        print("Category Distribution:")
        for category, count in sorted(categories.items()):
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
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    finally:
        await service.close()
        await db_pool.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test contractor batch processing')
    parser.add_argument('--limit', type=int, default=10, help='Number of contractors to process (default: 10)')
    
    args = parser.parse_args()
    asyncio.run(test_batch_with_city(args.limit)) 