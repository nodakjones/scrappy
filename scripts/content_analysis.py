#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.database.models import Contractor

async def debug_content_length(contractor_name):
    """Debug content length for a specific contractor"""
    await db_pool.initialize()
    
    # Get the contractor
    async with db_pool.pool.acquire() as conn:
        result = await conn.fetchrow('''
            SELECT * FROM contractors 
            WHERE business_name ILIKE $1
            LIMIT 1
        ''', f'%{contractor_name}%')
        
        if not result:
            print(f"No contractor found matching: {contractor_name}")
            return
        
        contractor = Contractor(**dict(result))
        print(f"Analyzing content for: {contractor.business_name}")
        print(f"Website URL: {contractor.website_url}")
        print("=" * 60)
        
        # Get the comprehensive crawl data
        service = ContractorService()
        try:
            if contractor.website_url:
                crawled_data = await service.crawl_website_comprehensive(contractor.website_url)
                
                if crawled_data:
                    print(f"📊 CRAWL STATISTICS:")
                    print(f"  Pages Crawled: {crawled_data['pages_crawled']}")
                    print(f"  Navigation Links Found: {crawled_data['nav_links_found']}")
                    print(f"  Main Content Length: {len(crawled_data['main_content'])} characters")
                    print(f"  Additional Content Length: {len(crawled_data['additional_content'])} characters")
                    print(f"  Combined Content Length: {len(crawled_data['combined_content'])} characters")
                    
                    print(f"\n📄 CONTENT BREAKDOWN:")
                    print(f"  Main Content (first 200 chars):")
                    print(f"    '{crawled_data['main_content'][:200]}...'")
                    
                    if crawled_data['additional_content']:
                        print(f"  Additional Pages: {len(crawled_data['additional_content'])}")
                        for i, content in enumerate(crawled_data['additional_content'][:3]):  # Show first 3
                            print(f"    Page {i+1}: {len(content)} characters")
                            print(f"      Preview: '{content[:100]}...'")
                    else:
                        print(f"  Additional Pages: None found")
                    
                    print(f"\n🎯 AI ANALYSIS CONTENT:")
                    print(f"  Content sent to AI: {len(crawled_data['combined_content'][:10000])} characters")
                    print(f"  Estimated tokens: {len(crawled_data['combined_content'][:10000]) // 4}")
                    print(f"  Estimated cost: ${(len(crawled_data['combined_content'][:10000]) // 4) * 0.0000005:.4f}")
                    
                else:
                    print("❌ No crawl data available")
            else:
                print("❌ No website URL available")
                
        except Exception as e:
            print(f"Error analyzing content: {e}")
            import traceback
            traceback.print_exc()
        
        await service.close()
    
    await db_pool.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Debug content length for a contractor')
    parser.add_argument('--contractor', '-c', type=str, default='425 CONSTRUCTION', help='Contractor name to analyze')
    args = parser.parse_args()
    
    asyncio.run(debug_content_length(args.contractor)) 