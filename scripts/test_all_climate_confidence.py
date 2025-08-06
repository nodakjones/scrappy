#!/usr/bin/env python3
"""
Test ALL CLIMATE Confidence Calculation
======================================

Test the confidence calculation for ALL CLIMATE HEATING & A/C specifically.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_all_climate_confidence():
    """Test confidence calculation for ALL CLIMATE HEATING & A/C"""
    service = ContractorService()
    
    print("🔍 ALL CLIMATE CONFIDENCE CALCULATION TEST")
    print("=" * 50)
    
    # Test case
    business_name = "ALL CLIMATE HEATING & A/C"
    city = "Everett"
    state = "WA"
    
    # The actual search result we found
    search_item = {
        'title': 'All Climate Heating & Air Conditioning: HVAC Installation, Air...',
        'snippet': 'All Climate Heating & Air Conditioning offers expert HVAC services in Redmond, Mountlake Terrace, Kirkland...',
        'link': 'https://www.allclimate.net/'
    }
    
    print(f"📋 Test Case:")
    print(f"   - Business: {business_name}")
    print(f"   - City: {city}")
    print(f"   - State: {state}")
    print(f"   - URL: {search_item['link']}")
    print(f"   - Title: {search_item['title']}")
    print(f"   - Snippet: {search_item['snippet'][:100]}...")
    print()
    
    # Test simple name generation
    simple_name = service._generate_simple_business_name(business_name)
    print(f"🔍 Business Name Processing:")
    print(f"   - Original: '{business_name}'")
    print(f"   - Simple: '{simple_name}'")
    print()
    
    # Test confidence calculation
    confidence = service._calculate_search_confidence(search_item, business_name, city, state)
    print(f"📊 Confidence Calculation:")
    print(f"   - Final confidence: {confidence:.3f}")
    print()
    
    # Test validation checks
    is_valid_website = service._is_valid_website(search_item['link'])
    has_wa_location = service._has_wa_location_indicators(search_item['link'], search_item['title'], search_item['snippet'])
    
    print(f"🔍 Validation Checks:")
    print(f"   - Valid website: {is_valid_website}")
    print(f"   - WA location indicators: {has_wa_location}")
    print()
    
    # Test content analysis
    title_lower = search_item['title'].lower()
    snippet_lower = search_item['snippet'].lower()
    business_name_lower = business_name.lower()
    simple_name_lower = simple_name.lower()
    
    print(f"🔍 Content Analysis:")
    print(f"   - Business name in title: {business_name_lower in title_lower}")
    print(f"   - Simple name in title: {simple_name_lower in title_lower}")
    print(f"   - Business name in snippet: {business_name_lower in snippet_lower}")
    print(f"   - Simple name in snippet: {simple_name_lower in snippet_lower}")
    print()
    
    # Test domain analysis
    domain = search_item['link'].lower().replace('https://', '').replace('http://', '').split('/')[0]
    print(f"🔍 Domain Analysis:")
    print(f"   - Domain: {domain}")
    print(f"   - Business name in domain: {business_name_lower.replace(' ', '') in domain}")
    print(f"   - Simple name in domain: {simple_name_lower.replace(' ', '') in domain}")
    print(f"   - Partial match: {any(word in domain for word in business_name_lower.split())}")
    print()
    
    # Test location analysis
    city_lower = city.lower()
    state_lower = state.lower()
    print(f"🔍 Location Analysis:")
    print(f"   - City in title/snippet: {city_lower in title_lower or city_lower in snippet_lower}")
    print(f"   - State in title/snippet: {state_lower in title_lower or state_lower in snippet_lower}")
    print()
    
    # Test alternative business names
    alternative_names = [
        "ALL CLIMATE HEATING & AIR CONDITIONING",
        "ALL CLIMATE HEATING AND AIR CONDITIONING", 
        "ALL CLIMATE HEATING & A/C",
        "ALL CLIMATE HEATING AND A/C",
        "ALL CLIMATE HEATING",
        "ALL CLIMATE"
    ]
    
    print(f"🔍 Alternative Business Name Testing:")
    for alt_name in alternative_names:
        alt_confidence = service._calculate_search_confidence(search_item, alt_name, city, state)
        print(f"   - '{alt_name}': {alt_confidence:.3f}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_all_climate_confidence()) 