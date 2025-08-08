#!/usr/bin/env python3
"""
Check current processing results in the database
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_processing_results():
    """Check current processing results"""
    await db_pool.initialize()
    
    try:
        # Get overall statistics
        stats = await db_pool.fetchrow('''
            SELECT 
                COUNT(*) as total_contractors,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN processing_status = 'processing' THEN 1 END) as processing,
                COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as errors
            FROM contractors
        ''')
        
        # Get review status breakdown
        review_stats = await db_pool.fetchrow('''
            SELECT 
                COUNT(CASE WHEN review_status = 'approved_download' THEN 1 END) as approved,
                COUNT(CASE WHEN review_status = 'pending_review' THEN 1 END) as pending_review,
                COUNT(CASE WHEN review_status = 'rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN review_status IS NULL THEN 1 END) as not_reviewed
            FROM contractors 
            WHERE processing_status = 'completed'
        ''')
        
        # Get confidence score distribution
        confidence_stats = await db_pool.fetchrow('''
            SELECT 
                COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence,
                COUNT(CASE WHEN confidence_score >= 0.6 AND confidence_score < 0.8 THEN 1 END) as medium_confidence,
                COUNT(CASE WHEN confidence_score < 0.6 AND confidence_score > 0 THEN 1 END) as low_confidence,
                COUNT(CASE WHEN confidence_score = 0 OR confidence_score IS NULL THEN 1 END) as no_confidence,
                AVG(confidence_score) as avg_confidence
            FROM contractors 
            WHERE processing_status = 'completed'
        ''')
        
        # Get website discovery stats
        website_stats = await db_pool.fetchrow('''
            SELECT 
                COUNT(CASE WHEN website_url IS NOT NULL AND website_url != '' THEN 1 END) as websites_found,
                COUNT(CASE WHEN website_url IS NULL OR website_url = '' THEN 1 END) as no_websites,
                COUNT(*) as total_processed
            FROM contractors 
            WHERE processing_status = 'completed'
        ''')
        
        # Get category distribution
        category_stats = await db_pool.fetch('''
            SELECT 
                mailer_category,
                COUNT(*) as count
            FROM contractors 
            WHERE processing_status = 'completed' 
                AND mailer_category IS NOT NULL 
                AND mailer_category != 'None'
            GROUP BY mailer_category 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        
        # Get home contractor stats
        home_stats = await db_pool.fetchrow('''
            SELECT 
                        COUNT(CASE WHEN residential_focus = true THEN 1 END) as residential_contractors,
        COUNT(CASE WHEN residential_focus = false THEN 1 END) as commercial_contractors,
        COUNT(CASE WHEN residential_focus IS NULL THEN 1 END) as unknown
            FROM contractors 
            WHERE processing_status = 'completed'
                ''')
        
        print("📊 CONTRACTOR PROCESSING RESULTS")
        print("=" * 50)
        print(f"📅 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Overall processing status
        print("🔄 PROCESSING STATUS:")
        print(f"  Total Contractors: {stats['total_contractors']:,}")
        print(f"  ✅ Completed: {stats['completed']:,}")
        print(f"  ⏳ Pending: {stats['pending']:,}")
        print(f"  🔄 Processing: {stats['processing']:,}")
        print(f"  ❌ Errors: {stats['errors']:,}")
        print()
        
        # Review status breakdown
        if stats['completed'] > 0:
            print("📋 REVIEW STATUS (Completed Only):")
            print(f"  ✅ Approved for Download: {review_stats['approved']:,}")
            print(f"  ⚠️ Pending Review: {review_stats['pending_review']:,}")
            print(f"  ❌ Rejected: {review_stats['rejected']:,}")
            print(f"  ❓ Not Reviewed: {review_stats['not_reviewed']:,}")
            print()
            
            # Confidence distribution
            print("🎯 CONFIDENCE DISTRIBUTION:")
            print(f"  🟢 High (≥0.8): {confidence_stats['high_confidence']:,}")
            print(f"  🟡 Medium (0.6-0.79): {confidence_stats['medium_confidence']:,}")
            print(f"  🔴 Low (<0.6): {confidence_stats['low_confidence']:,}")
            print(f"  ⚫ No Confidence: {confidence_stats['no_confidence']:,}")
            print(f"  📊 Average Confidence: {confidence_stats['avg_confidence']:.3f}")
            print()
            
            # Website discovery
            print("🌐 WEBSITE DISCOVERY:")
            print(f"  ✅ Websites Found: {website_stats['websites_found']:,}")
            print(f"  ❌ No Websites: {website_stats['no_websites']:,}")
            print(f"  📊 Discovery Rate: {website_stats['websites_found']/website_stats['total_processed']*100:.1f}%")
            print()
            
            # Residential contractor stats
            print("🏠 RESIDENTIAL CONTRACTOR IDENTIFICATION:")
            print(f"  ✅ Residential Contractors: {home_stats['residential_contractors']:,}")
            print(f"  🏢 Commercial Contractors: {home_stats['commercial_contractors']:,}")
            print(f"  ❓ Unknown: {home_stats['unknown']:,}")
            print()
            
            # Top categories
            print("📂 TOP CATEGORIES:")
            for row in category_stats:
                print(f"  {row['mailer_category']}: {row['count']:,}")
            print()
            
            # Downloadable results summary
            total_downloadable = review_stats['approved'] + review_stats['pending_review']
            print("💾 DOWNLOADABLE RESULTS:")
            print(f"  ✅ Auto-Approved: {review_stats['approved']:,}")
            print(f"  ⚠️ Pending Review: {review_stats['pending_review']:,}")
            print(f"  📦 TOTAL DOWNLOADABLE: {total_downloadable:,}")
            print()
            
            if total_downloadable > 0:
                print("🚀 READY FOR EXPORT!")
                print(f"  You have {total_downloadable:,} contractors ready for download")
                print("  Run: docker-compose exec app python scripts/export_contractors.py")
            else:
                print("⏳ NO RESULTS READY YET")
                print("  Continue processing to generate downloadable results")
        else:
            print("⏳ NO COMPLETED PROCESSING YET")
            print("  Start processing to generate results")
    
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_processing_results()) 