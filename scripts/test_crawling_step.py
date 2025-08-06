#!/usr/bin/env python3
"""
Test Crawling Step
==================

Test the crawling step for specific websites to debug validation issues.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_crawling_step():
    """Test crawling step for specific websites"""
    service = ContractorService()
    
    print("🔍 CRAWLING STEP TEST")
    print("=" * 50)
    
    # Test URLs that should work
    test_urls = [
        "https://www.1stchoicehomesolutionsllc.com/",
        "https://1stchoicehomesolutionsllc.com/",
        "https://www.1stchoicehomesolutionsllc.com/contact"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📋 Test URL {i}: {url}")
        print("-" * 40)
        
        try:
            # Test basic crawl
            print(f"🔄 Testing basic crawl...")
            basic_content = await service.crawl_website(url)
            if basic_content:
                print(f"✅ Basic crawl successful - {len(basic_content)} characters")
            else:
                print(f"❌ Basic crawl failed")
            
            # Test comprehensive crawl
            print(f"🔄 Testing comprehensive crawl...")
            comprehensive_data = await service.crawl_website_comprehensive(url)
            if comprehensive_data:
                print(f"✅ Comprehensive crawl successful:")
                print(f"   - Combined content: {len(comprehensive_data.get('combined_content', ''))} characters")
                print(f"   - Main content: {len(comprehensive_data.get('main_content', ''))} characters")
                print(f"   - Additional content: {len(comprehensive_data.get('additional_content', ''))} characters")
                print(f"   - Pages crawled: {comprehensive_data.get('pages_crawled', 0)}")
                print(f"   - Nav links found: {comprehensive_data.get('nav_links_found', 0)}")
                
                # Test if it has combined_content (required for processing)
                if comprehensive_data.get('combined_content'):
                    print(f"   ✅ Has combined_content - READY FOR PROCESSING")
                else:
                    print(f"   ❌ Missing combined_content - WILL FAIL PROCESSING")
            else:
                print(f"❌ Comprehensive crawl failed")
                
        except Exception as e:
            print(f"❌ Error during crawling: {e}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_crawling_step()) 