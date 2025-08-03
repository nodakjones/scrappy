#!/usr/bin/env python3
"""
Test a legitimate case to ensure the strict validation isn't too restrictive.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_legitimate_case():
    """Test a legitimate case to ensure we're not being too strict"""
    print("🧪 TESTING LEGITIMATE CASE")
    print("=" * 60)
    
    service = ContractorService()
    
    # Test a legitimate case that should be accepted
    legitimate_case = {
        "business_name": "5 Star Guttering",
        "city": "PASCO",
        "state": "WA",
        "url": "https://5starguttering.com/",
        "title": "5 Star Guttering - Professional Gutter Services",
        "snippet": "Professional gutter installation and repair services in Pasco, Washington"
    }
    
    print(f"🧪 TESTING LEGITIMATE CASE: {legitimate_case['business_name']}")
    print(f"{'='*60}")
    
    # Create mock search item
    search_item = {
        'title': legitimate_case['title'],
        'snippet': legitimate_case['snippet'],
        'link': legitimate_case['url']
    }
    
    # Test the confidence calculation
    confidence = service._calculate_search_confidence(
        search_item, 
        legitimate_case['business_name'], 
        legitimate_case['city'], 
        legitimate_case['state']
    )
    
    print(f"📋 Test Data:")
    print(f"  Business: {legitimate_case['business_name']}")
    print(f"  Location: {legitimate_case['city']}, {legitimate_case['state']}")
    print(f"  URL: {legitimate_case['url']}")
    print(f"  Title: {legitimate_case['title']}")
    print(f"  Snippet: {legitimate_case['snippet']}")
    
    print(f"\n🎯 Results:")
    print(f"  Confidence: {confidence:.3f}")
    print(f"  Would Accept: {'✅ YES' if confidence >= 0.4 else '❌ NO'}")
    
    # Test geographic validation
    has_wa_location = service._has_wa_location_indicators(
        legitimate_case['url'], legitimate_case['title'], legitimate_case['snippet']
    )
    print(f"  Has WA Location: {'✅ YES' if has_wa_location else '❌ NO'}")
    
    # Test domain validation
    is_valid_domain = service._is_valid_website(legitimate_case['url'])
    print(f"  Valid Domain: {'✅ YES' if is_valid_domain else '❌ NO'}")
    
    print(f"\n📊 Analysis:")
    if confidence >= 0.4:
        print(f"  ✅ CORRECTLY ACCEPTED - Good confidence ({confidence:.3f})")
    else:
        print(f"  ❌ INCORRECTLY REJECTED - Should have been accepted")
    
    print(f"\n{'='*60}")
    print("🧪 LEGITIMATE CASE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_legitimate_case()) 