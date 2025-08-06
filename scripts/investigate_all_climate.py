#!/usr/bin/env python3
"""
Investigate ALL CLIMATE HEATING & A/C
====================================

Comprehensive investigation of ALL CLIMATE HEATING & A/C to understand why no website was found.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def investigate_all_climate():
    """Investigate ALL CLIMATE HEATING & A/C specifically"""
    service = ContractorService()
    
    print("🔍 ALL CLIMATE HEATING & A/C INVESTIGATION")
    print("=" * 50)
    
    # Contractor details
    business_name = "ALL CLIMATE HEATING & A/C"
    city = "Everett"  # Assuming based on Puget Sound
    state = "WA"
    
    print(f"📋 Contractor Details:")
    print(f"   - Business: {business_name}")
    print(f"   - City: {city}")
    print(f"   - State: {state}")
    print()
    
    # Test 1: Search query generation
    print(f"🔍 Test 1: Search Query Generation")
    print("-" * 30)
    queries = service._generate_search_queries(business_name, city, state)
    for i, query in enumerate(queries, 1):
        print(f"   {i}. '{query}'")
    print()
    
    # Test 2: Simple name generation
    print(f"🔍 Test 2: Business Name Processing")
    print("-" * 30)
    simple_name = service._generate_simple_business_name(business_name)
    print(f"   - Original: '{business_name}'")
    print(f"   - Simple: '{simple_name}'")
    print()
    
    # Test 3: Clearbit API
    print(f"🔍 Test 3: Clearbit API")
    print("-" * 30)
    try:
        clearbit_domain = await service.try_clearbit_enrichment(business_name)
        if clearbit_domain:
            print(f"   ✅ Clearbit found: {clearbit_domain}")
            url = f"https://{clearbit_domain}"
            is_valid = service._is_valid_website(url)
            print(f"   - Valid website: {is_valid}")
            
            if is_valid:
                print(f"   - Full URL: {url}")
                # Test crawling
                crawled_data = await service.crawl_website_comprehensive(url)
                if crawled_data and crawled_data.get('combined_content'):
                    print(f"   ✅ Crawl successful - {len(crawled_data['combined_content'])} characters")
                    
                    # Test validation
                    content_lower = crawled_data['combined_content'].lower()
                    business_name_lower = business_name.lower()
                    simple_name_lower = simple_name.lower()
                    
                    print(f"   - Business name in content: {business_name_lower in content_lower}")
                    print(f"   - Simple name in content: {simple_name_lower in content_lower}")
                    print(f"   - City in content: {city.lower() in content_lower}")
                    print(f"   - State in content: {state.lower() in content_lower}")
                else:
                    print(f"   ❌ Crawl failed")
            else:
                print(f"   ❌ Domain is not a valid website")
        else:
            print(f"   ❌ Clearbit API returned no domain")
    except Exception as e:
        print(f"   ❌ Clearbit API error: {e}")
    print()
    
    # Test 4: Google API for each query
    print(f"🔍 Test 4: Google API Results")
    print("-" * 30)
    
    for i, query in enumerate(queries, 1):
        print(f"   📋 Query {i}: '{query}'")
        try:
            result = await service.search_google_api(query)
            
            if result and 'items' in result:
                print(f"   ✅ Found {len(result['items'])} results")
                
                # Show first 5 results
                for j, item in enumerate(result['items'][:5], 1):
                    url = item.get('link', '')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    print(f"      Result {j}:")
                    print(f"      - URL: {url}")
                    print(f"      - Title: {title}")
                    print(f"      - Snippet: {snippet[:100]}...")
                    
                    # Test confidence and validation
                    confidence = service._calculate_search_confidence(item, business_name, city, state)
                    is_valid = service._is_valid_website(url)
                    has_location = service._has_wa_location_indicators(url, title, snippet)
                    
                    print(f"      - Confidence: {confidence:.3f}")
                    print(f"      - Valid website: {is_valid}")
                    print(f"      - WA location: {has_location}")
                    
                    if confidence > 0.1 and is_valid and has_location:
                        print(f"      ✅ PASSES ALL CHECKS")
                    else:
                        print(f"      ❌ FAILS CHECKS")
                    print()
            else:
                print(f"   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    # Test 5: Manual search suggestions
    print(f"🔍 Test 5: Manual Search Suggestions")
    print("-" * 30)
    manual_queries = [
        "ALL CLIMATE HEATING Everett WA",
        "All Climate Heating & Air Conditioning Everett",
        "All Climate Heating Everett",
        "All Climate HVAC Everett WA",
        "All Climate Heating and Air Conditioning",
        "All Climate Heating & AC Everett"
    ]
    
    for i, query in enumerate(manual_queries, 1):
        print(f"   📋 Manual Query {i}: '{query}'")
        try:
            result = await service.search_google_api(query)
            
            if result and 'items' in result:
                print(f"   ✅ Found {len(result['items'])} results")
                
                # Show first 3 results
                for j, item in enumerate(result['items'][:3], 1):
                    url = item.get('link', '')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    print(f"      Result {j}:")
                    print(f"      - URL: {url}")
                    print(f"      - Title: {title}")
                    print(f"      - Snippet: {snippet[:100]}...")
                    
                    # Test confidence and validation
                    confidence = service._calculate_search_confidence(item, business_name, city, state)
                    is_valid = service._is_valid_website(url)
                    has_location = service._has_wa_location_indicators(url, title, snippet)
                    
                    print(f"      - Confidence: {confidence:.3f}")
                    print(f"      - Valid website: {is_valid}")
                    print(f"      - WA location: {has_location}")
                    
                    if confidence > 0.1 and is_valid and has_location:
                        print(f"      ✅ PASSES ALL CHECKS")
                    else:
                        print(f"      ❌ FAILS CHECKS")
                    print()
            else:
                print(f"   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(investigate_all_climate()) 