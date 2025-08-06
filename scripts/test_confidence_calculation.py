#!/usr/bin/env python3
"""
Test Confidence Calculation
==========================

Test the confidence calculation for specific search results to debug validation issues.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_confidence_calculation():
    """Test confidence calculation for specific search results"""
    service = ContractorService()
    
    print("🔍 CONFIDENCE CALCULATION TEST")
    print("=" * 50)
    
    # Test case: 1ST CHOICE HOME SOLUTIONS LLC
    business_name = "1ST CHOICE HOME SOLUTIONS LLC"
    city = "Everett"
    state = "WA"
    
    # Simulate the search result we know should work
    search_item = {
        'title': '1st Choice Home Solutions LLC | Everett, WA',
        'snippet': 'Get expert home renovations & remodeling from 1st Choice Home Solutions LLC. Call for a free quote today - (206) 539-1121!...',
        'link': 'https://www.1stchoicehomesolutionsllc.com/'
    }
    
    print(f"📋 Testing confidence calculation for:")
    print(f"   - Business: {business_name}")
    print(f"   - City: {city}")
    print(f"   - State: {state}")
    print(f"   - URL: {search_item['link']}")
    print(f"   - Title: {search_item['title']}")
    print(f"   - Snippet: {search_item['snippet'][:100]}...")
    print()
    
    # Test validation checks
    is_valid_website = service._is_valid_website(search_item['link'])
    has_wa_location = service._has_wa_location_indicators(search_item['link'], search_item['title'], search_item['snippet'])
    
    print(f"🔍 Validation Checks:")
    print(f"   - Valid website: {is_valid_website}")
    print(f"   - WA location indicators: {has_wa_location}")
    print()
    
    # Test confidence calculation
    confidence = service._calculate_search_confidence(search_item, business_name, city, state)
    
    print(f"📊 Confidence Calculation:")
    print(f"   - Final confidence: {confidence:.3f}")
    print()
    
    # Test simple name generation
    simple_name = service._generate_simple_business_name(business_name)
    print(f"🔍 Business Name Processing:")
    print(f"   - Original: '{business_name}'")
    print(f"   - Simple: '{simple_name}'")
    print()
    
    # Test domain analysis
    domain = search_item['link'].lower().replace('https://', '').replace('http://', '').split('/')[0]
    business_name_lower = business_name.lower()
    simple_name_lower = simple_name.lower()
    
    print(f"🔍 Domain Analysis:")
    print(f"   - Domain: {domain}")
    print(f"   - Business name in domain: {business_name_lower.replace(' ', '') in domain}")
    print(f"   - Simple name in domain: {simple_name_lower.replace(' ', '') in domain}")
    print(f"   - Partial match: {any(word in domain for word in business_name_lower.split())}")
    print()
    
    # Test title/snippet analysis
    title_lower = search_item['title'].lower()
    snippet_lower = search_item['snippet'].lower()
    
    print(f"🔍 Content Analysis:")
    print(f"   - Business name in title: {business_name_lower in title_lower}")
    print(f"   - Simple name in title: {simple_name_lower in title_lower}")
    print(f"   - Business name in snippet: {business_name_lower in snippet_lower}")
    print(f"   - Simple name in snippet: {simple_name_lower in snippet_lower}")
    print(f"   - City in title/snippet: {city.lower() in title_lower or city.lower() in snippet_lower}")
    print(f"   - State in title/snippet: {state.lower() in title_lower or state.lower() in snippet_lower}")
    print()
    
    # Test directory indicators
    directory_indicators = ['association', 'directory', 'listing', 'find', 'search', 'pros', 'contractors', 'bizprofile', 'bizapedia', 'yellowpages', 'whitepages', 'superpages', 'manta', 'zoominfo']
    has_directory_indicators = any(indicator in title_lower or indicator in snippet_lower for indicator in directory_indicators)
    print(f"🔍 Directory Check:")
    print(f"   - Has directory indicators: {has_directory_indicators}")
    print()
    
    # Test contractor keywords
    contractor_keywords = ['contractor', 'construction', 'plumbing', 'electrical', 'hvac', 'roofing', 'insulation', 'mold', 'attic']
    found_keywords = [keyword for keyword in contractor_keywords if keyword in title_lower or keyword in snippet_lower]
    print(f"🔍 Contractor Keywords:")
    print(f"   - Found keywords: {found_keywords}")
    print()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_confidence_calculation()) 