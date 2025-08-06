#!/usr/bin/env python3
"""
Debug script to test search confidence calculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService

def debug_search_confidence():
    """Debug search confidence calculation"""
    
    service = ContractorService()
    
    # Test with the correct contractor
    business_name = "A PLUS HANDYMAN"
    city = "SEATTLE"
    state = "WA"
    
    print("🔍 DEBUGGING SEARCH CONFIDENCE CALCULATION")
    print("=" * 60)
    print(f"Business Name: {business_name}")
    print(f"City: {city}")
    print(f"State: {state}")
    
    # Test simple name generation
    simple_name = service._generate_simple_business_name(business_name)
    print(f"\n📋 Simple Name: '{simple_name}'")
    
    # Test with a mock search result that might be returned by Google
    mock_search_result = {
        'title': 'A Plus Handyman Services - Seattle, WA | Home Repairs',
        'snippet': 'A Plus Handyman Services in Seattle, WA. Professional home repair and maintenance services. Call us today for reliable handyman work.',
        'link': 'https://www.aplushandyman.com/'
    }
    
    print(f"\n🔍 Mock Search Result:")
    print(f"  Title: '{mock_search_result['title']}'")
    print(f"  Snippet: '{mock_search_result['snippet']}'")
    print(f"  URL: '{mock_search_result['link']}'")
    
    # Calculate confidence
    confidence = service._calculate_search_confidence(mock_search_result, business_name, city, state)
    
    print(f"\n📊 Confidence Calculation:")
    print(f"  Final Confidence: {confidence}")
    
    # Test individual components
    title = mock_search_result['title'].lower()
    snippet = mock_search_result['snippet'].lower()
    url = mock_search_result['link'].lower()
    
    business_name_lower = business_name.lower()
    simple_name_lower = simple_name.lower()
    
    print(f"\n🔍 Individual Tests:")
    print(f"  Business name in title: '{business_name_lower}' in '{title}' = {business_name_lower in title}")
    print(f"  Simple name in title: '{simple_name_lower}' in '{title}' = {simple_name_lower in title}")
    print(f"  Business name in snippet: '{business_name_lower}' in '{snippet}' = {business_name_lower in snippet}")
    print(f"  Simple name in snippet: '{simple_name_lower}' in '{snippet}' = {simple_name_lower in snippet}")
    print(f"  Business name in URL: '{business_name_lower}' in '{url}' = {business_name_lower in url}")
    print(f"  Simple name in URL: '{simple_name_lower}' in '{url}' = {simple_name_lower in url}")
    
    # Test location matching
    city_lower = city.lower()
    state_lower = state.lower()
    
    print(f"\n📍 Location Tests:")
    print(f"  City in title: '{city_lower}' in '{title}' = {city_lower in title}")
    print(f"  State in title: '{state_lower}' in '{title}' = {state_lower in title}")
    print(f"  City in snippet: '{city_lower}' in '{snippet}' = {city_lower in snippet}")
    print(f"  State in snippet: '{state_lower}' in '{snippet}' = {state_lower in snippet}")
    
    # Test WA location indicators
    wa_indicators = service._has_wa_location_indicators(url, title, snippet)
    print(f"  WA location indicators: {wa_indicators}")
    
    # Test domain validation
    is_valid = service._is_valid_website(url)
    print(f"  Valid website: {is_valid}")
    
    # Test with a different mock result that might be more realistic
    print(f"\n🔍 Testing with different mock result:")
    mock_search_result2 = {
        'title': 'Handyman Services Seattle | A Plus Handyman',
        'snippet': 'Professional handyman services in Seattle. A Plus Handyman provides quality home repairs and maintenance.',
        'link': 'https://www.aplushandymanseattle.com/'
    }
    
    print(f"  Title: '{mock_search_result2['title']}'")
    print(f"  Snippet: '{mock_search_result2['snippet']}'")
    print(f"  URL: '{mock_search_result2['link']}'")
    
    confidence2 = service._calculate_search_confidence(mock_search_result2, business_name, city, state)
    print(f"  Confidence: {confidence2}")

if __name__ == "__main__":
    debug_search_confidence() 