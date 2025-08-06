#!/usr/bin/env python3
"""
Test Google Search Results
=========================

Test Google API search results for specific queries to debug validation issues.
"""

import asyncio
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_google_search_results():
    """Test Google API search results for specific queries"""
    service = ContractorService()
    
    print("🔍 GOOGLE API SEARCH RESULTS TEST")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "1ST CHOICE HOME SOLUTIONS LLC everett wa",
        "1ST CHOICE HOME SOLUTIONS LLC WA",
        "1st Choice Home Solutions LLC Everett",
        "1st Choice Home Solutions WA"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test Query {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Call Google API directly
            result = await service.search_google_api(query)
            
            if result and 'items' in result:
                print(f"✅ Found {len(result['items'])} results")
                
                for j, item in enumerate(result['items'], 1):
                    url = item.get('link', '')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    print(f"\n   Result {j}:")
                    print(f"   - URL: {url}")
                    print(f"   - Title: {title}")
                    print(f"   - Snippet: {snippet[:200]}...")
                    
                    # Test validation checks
                    is_valid_website = service._is_valid_website(url)
                    has_wa_location = service._has_wa_location_indicators(url, title, snippet)
                    
                    print(f"   - Valid website: {is_valid_website}")
                    print(f"   - WA location indicators: {has_wa_location}")
                    
                    if is_valid_website and has_wa_location:
                        print(f"   ✅ PASSES VALIDATION")
                    else:
                        print(f"   ❌ FAILS VALIDATION")
                        
            else:
                print(f"❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_google_search_results()) 