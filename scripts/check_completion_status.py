#!/usr/bin/env python3
"""
Check Actual Completion Status
=============================

Check what records are actually completed vs just marked as completed.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def check_completion_status():
    """Check actual completion status"""
    await db_pool.initialize()
    
    print("🔍 ACTUAL COMPLETION STATUS ANALYSIS")
    print("=" * 50)
    
    # Check completed records with review status
    completed_with_review_query = """
        SELECT 
            COUNT(*) as total_completed,
            COUNT(CASE WHEN review_status = 'approved_download' THEN 1 END) as approved,
            COUNT(CASE WHEN review_status = 'pending_review' THEN 1 END) as pending_review,
            COUNT(CASE WHEN review_status = 'rejected' THEN 1 END) as rejected,
            COUNT(CASE WHEN review_status IS NULL THEN 1 END) as no_review_status
        FROM contractors 
        WHERE processing_status = 'completed'
    """
    
    completed_data = await db_pool.fetchrow(completed_with_review_query)
    
    print(f"📊 Completed Records Analysis:")
    print(f"   - Total marked as completed: {completed_data['total_completed']:,}")
    print(f"   - With approved_download status: {completed_data['approved']:,}")
    print(f"   - With pending_review status: {completed_data['pending_review']:,}")
    print(f"   - With rejected status: {completed_data['rejected']:,}")
    print(f"   - With NO review status: {completed_data['no_review_status']:,}")
    
    # Check for completed records with actual data
    completed_with_data_query = """
        SELECT 
            COUNT(*) as total_completed,
            COUNT(CASE WHEN website_url IS NOT NULL AND website_url != '' THEN 1 END) as with_websites,
            COUNT(CASE WHEN confidence_score IS NOT NULL AND confidence_score > 0 THEN 1 END) as with_confidence,
            COUNT(CASE WHEN mailer_category IS NOT NULL AND mailer_category != '' THEN 1 END) as with_categories,
            COUNT(CASE WHEN website_confidence IS NOT NULL THEN 1 END) as with_website_confidence,
            COUNT(CASE WHEN classification_confidence IS NOT NULL THEN 1 END) as with_classification_confidence
        FROM contractors 
        WHERE processing_status = 'completed'
    """
    
    completed_with_data = await db_pool.fetchrow(completed_with_data_query)
    
    print(f"\n📊 Completed Records with Data:")
    print(f"   - With websites: {completed_with_data['with_websites']:,}")
    print(f"   - With confidence scores: {completed_with_data['with_confidence']:,}")
    print(f"   - With categories: {completed_with_data['with_categories']:,}")
    print(f"   - With website confidence: {completed_with_data['with_website_confidence']:,}")
    print(f"   - With classification confidence: {completed_with_data['with_classification_confidence']:,}")
    
    # Check for records that might be falsely marked as completed
    falsely_completed_query = """
        SELECT COUNT(*) as count
        FROM contractors 
        WHERE processing_status = 'completed' 
        AND (website_url IS NULL OR website_url = '')
        AND (confidence_score IS NULL OR confidence_score = 0)
        AND (mailer_category IS NULL OR mailer_category = '')
    """
    
    falsely_completed = await db_pool.fetchrow(falsely_completed_query)
    
    print(f"\n⚠️  Potentially Falsely Completed:")
    print(f"   - Records marked completed but with no data: {falsely_completed['count']:,}")
    
    # Check recent processing activity
    recent_activity_query = """
        SELECT 
            processing_status,
            review_status,
            COUNT(*) as count
        FROM contractors 
        WHERE updated_at >= NOW() - INTERVAL '7 days'
        GROUP BY processing_status, review_status
        ORDER BY processing_status, review_status
    """
    
    recent_activity = await db_pool.fetch(recent_activity_query)
    
    print(f"\n📅 Recent Activity (Last 7 Days):")
    for record in recent_activity:
        status = record['processing_status']
        review = record['review_status'] or 'None'
        count = record['count']
        print(f"   - {status} / {review}: {count:,}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_completion_status()) 