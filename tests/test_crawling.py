#!/usr/bin/env python3
"""
Test script to check crawling content for 425 Handyman Services
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService

async def test_crawling():
    """Test crawling for 425 Handyman Services"""
    
    service = ContractorService()
    url = "https://www.425handymanservices.com/"
    
    print("🔍 TESTING CRAWLING FOR 425 HANDYMAN SERVICES")
    print("=" * 60)
    
    # Test single page crawling
    print("📄 Single Page Crawling:")
    single_content = await service._crawl_single_page(url)
    if single_content:
        print(f"   Length: {len(single_content)} characters")
        print(f"   Preview: {single_content[:500]}...")
        print(f"   Contains phone: {'(425)242-8631' in single_content}")
        print(f"   Contains King County: {'King County' in single_content}")
    else:
        print("   ❌ Failed to crawl single page")
    
    print("\n🌐 Comprehensive Crawling:")
    comprehensive_result = await service.crawl_website_comprehensive(url)
    if comprehensive_result:
        main_content = comprehensive_result.get('main_content', '')
        combined_content = comprehensive_result.get('combined_content', '')
        
        print(f"   Main content length: {len(main_content)} characters")
        print(f"   Combined content length: {len(combined_content)} characters")
        print(f"   Pages crawled: {comprehensive_result.get('pages_crawled', 0)}")
        print(f"   Nav links found: {comprehensive_result.get('nav_links_found', 0)}")
        
        print(f"\n   Main content contains phone: {'(425)242-8631' in main_content}")
        print(f"   Main content contains King County: {'King County' in main_content}")
        print(f"   Combined content contains phone: {'(425)242-8631' in combined_content}")
        print(f"   Combined content contains King County: {'King County' in combined_content}")
        
        print(f"\n   Main content preview: {main_content[:500]}...")
    else:
        print("   ❌ Failed to crawl comprehensively")
    
    # Test the 10K character limit
    if comprehensive_result:
        combined_content = comprehensive_result.get('combined_content', '')
        truncated_content = combined_content[:10000]
        
        print(f"\n📏 Content Truncation Test:")
        print(f"   Original length: {len(combined_content)} characters")
        print(f"   Truncated length: {len(truncated_content)} characters")
        print(f"   Truncated contains phone: {'(425)242-8631' in truncated_content}")
        print(f"   Truncated contains King County: {'King County' in truncated_content}")
        
        # Find where phone number appears in content
        phone_pos = combined_content.find('(425)242-8631')
        if phone_pos != -1:
            print(f"   Phone number position: {phone_pos} (within 10K: {'Yes' if phone_pos < 10000 else 'No'})")
        
        # Find where King County appears in content
        king_county_pos = combined_content.find('King County')
        if king_county_pos != -1:
            print(f"   King County position: {king_county_pos} (within 10K: {'Yes' if king_county_pos < 10000 else 'No'})")

if __name__ == "__main__":
    asyncio.run(test_crawling()) 