#!/usr/bin/env python3
"""
Test Clearbit API
=================

Test the Clearbit API for specific contractors to debug validation issues.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_clearbit_api():
    """Test Clearbit API for specific contractors"""
    service = ContractorService()
    
    print("🔍 CLEARBIT API TEST")
    print("=" * 50)
    
    # Test case: 1ST CHOICE HOME SOLUTIONS LLC
    business_name = "1ST CHOICE HOME SOLUTIONS LLC"
    
    print(f"📋 Testing Clearbit API for:")
    print(f"   - Business: {business_name}")
    print()
    
    # Test simple name generation
    simple_name = service._generate_simple_business_name(business_name)
    print(f"🔍 Business Name Variations:")
    print(f"   - Original: '{business_name}'")
    print(f"   - Simple: '{simple_name}'")
    print()
    
    # Test Clearbit API
    print(f"🔄 Testing Clearbit API...")
    try:
        domain = await service.try_clearbit_enrichment(business_name)
        if domain:
            print(f"✅ Clearbit found domain: {domain}")
            
            # Test if this domain is valid
            url = f"https://{domain}"
            is_valid = service._is_valid_website(url)
            print(f"   - Valid website: {is_valid}")
            
            if is_valid:
                print(f"   - Full URL: {url}")
                
                # Test crawling this domain
                print(f"🔄 Testing crawl of Clearbit domain...")
                crawled_data = await service.crawl_website_comprehensive(url)
                if crawled_data and crawled_data.get('combined_content'):
                    print(f"✅ Crawl successful - {len(crawled_data['combined_content'])} characters")
                    print(f"   - Pages crawled: {crawled_data.get('pages_crawled', 0)}")
                    print(f"   - Nav links found: {crawled_data.get('nav_links_found', 0)}")
                else:
                    print(f"❌ Crawl failed")
            else:
                print(f"❌ Domain is not a valid website")
        else:
            print(f"❌ Clearbit API returned no domain")
            
    except Exception as e:
        print(f"❌ Clearbit API error: {e}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_clearbit_api()) 