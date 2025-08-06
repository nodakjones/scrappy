#!/usr/bin/env python3
"""
Test script to check what content is being passed to validation during processing
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService
from src.database.models import Contractor
from src.database.connection import db_pool

async def test_validation_content():
    """Test what content is being passed to validation during processing"""
    
    # Initialize database connection
    await db_pool.initialize()
    
    # Get contractor data
    query = """
    SELECT * FROM contractors 
    WHERE business_name = '425 HANDYMAN SERVICES LLC'
    """
    row = await db_pool.fetchrow(query)
    
    if not row:
        print("❌ Contractor not found")
        return
    
    # Create contractor object
    contractor = Contractor(**dict(row))
    
    print("🔍 TESTING VALIDATION CONTENT FOR 425 HANDYMAN SERVICES LLC")
    print("=" * 60)
    
    # Simulate the content analysis process
    print("📄 Step 1: Getting crawled content...")
    
    # Initialize service
    service = ContractorService()
    
    # Get the crawled content (this is what happens during processing)
    crawled_data = await service.crawl_website_comprehensive(contractor.website_url)
    
    if crawled_data:
        content = crawled_data['combined_content']
        print(f"   Content length: {len(content)} characters")
        print(f"   Contains phone: {'(425)242-8631' in content}")
        print(f"   Contains King County: {'King County' in content}")
        print(f"   Content preview: {content[:500]}...")
        
        print("\n📊 Step 2: Running validation with this content...")
        
        # Create a mock logger context
        class MockLoggerCtx:
            def log_ai_call(self, *args, **kwargs):
                pass
            def log_validation(self, *args, **kwargs):
                pass
        
        logger_ctx = MockLoggerCtx()
        
        # Run validation with the actual content
        validation_results = await service._comprehensive_website_validation(contractor, content, logger_ctx)
        
        print("   Validation Results:")
        print(f"     Phone Match: {validation_results.get('phone_match', False)}")
        print(f"     Address Match: {validation_results.get('address_match', False)}")
        print(f"     Business Name Match: {validation_results.get('business_name_match', False)}")
        print(f"     License Match: {validation_results.get('license_match', False)}")
        print(f"     Principal Match: {validation_results.get('principal_name_match', False)}")
        print(f"     Domain Match Score: {validation_results.get('domain_match_score', 0.0)}")
        
        # Calculate confidence
        confidence = service._calculate_validation_confidence(validation_results)
        print(f"     Calculated Confidence: {confidence}")
        
    else:
        print("   ❌ Failed to get crawled content")

if __name__ == "__main__":
    asyncio.run(test_validation_content()) 