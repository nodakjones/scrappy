#!/usr/bin/env python3
"""
Test Search Query Generation
===========================

Test the search query generation for specific contractors to debug validation issues.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_search_query_generation():
    """Test search query generation for specific contractors"""
    service = ContractorService()
    
    print("🔍 SEARCH QUERY GENERATION TEST")
    print("=" * 50)
    
    # Test case: 1ST CHOICE HOME SOLUTIONS LLC
    business_name = "1ST CHOICE HOME SOLUTIONS LLC"
    city = "Everett"
    state = "WA"
    
    print(f"📋 Testing search query generation for:")
    print(f"   - Business: {business_name}")
    print(f"   - City: {city}")
    print(f"   - State: {state}")
    print()
    
    # Generate search queries
    queries = service._generate_search_queries(business_name, city, state)
    
    print(f"🔍 Generated Search Queries:")
    for i, query in enumerate(queries, 1):
        print(f"   {i}. '{query}'")
    print()
    
    # Test each query with Google API
    for i, query in enumerate(queries, 1):
        print(f"📋 Testing Query {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Call Google API
            result = await service.search_google_api(query)
            
            if result and 'items' in result:
                print(f"✅ Found {len(result['items'])} results")
                
                # Show first 3 results
                for j, item in enumerate(result['items'][:3], 1):
                    url = item.get('link', '')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    print(f"\n   Result {j}:")
                    print(f"   - URL: {url}")
                    print(f"   - Title: {title}")
                    print(f"   - Snippet: {snippet[:100]}...")
                    
                    # Test confidence calculation
                    confidence = service._calculate_search_confidence(item, business_name, city, state)
                    print(f"   - Confidence: {confidence:.3f}")
                    
                    # Test validation
                    is_valid = service._is_valid_website(url)
                    has_location = service._has_wa_location_indicators(url, title, snippet)
                    print(f"   - Valid website: {is_valid}")
                    print(f"   - WA location: {has_location}")
                    
                    if confidence > 0.1 and is_valid and has_location:
                        print(f"   ✅ PASSES ALL CHECKS")
                    else:
                        print(f"   ❌ FAILS CHECKS")
                        
            else:
                print(f"❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_search_query_generation()) 