#!/usr/bin/env python3
"""
Test the new strict validation on the problematic cases.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.contractor_service import ContractorService

async def test_strict_validation():
    """Test the new strict validation on problematic cases"""
    print("🧪 TESTING STRICT VALIDATION")
    print("=" * 60)
    
    service = ContractorService()
    
    # Test cases that should be rejected
    test_cases = [
        {
            "business_name": "509 HEATING & COOLING",
            "city": "YAKIMA",
            "state": "WA",
            "url": "https://www.thermallheating.com/service-areas/yakima",
            "title": "Thermal Heating & Cooling - HVAC Services",
            "snippet": "Professional HVAC services in Yakima area"
        },
        {
            "business_name": "509 SERVICES",
            "city": "COLBERT",
            "state": "WA",
            "url": "https://nevinfloorcompany.com/removing-hardwood-floors/colbert-washington/",
            "title": "Nevin Floor Company - Hardwood Floor Removal",
            "snippet": "Professional hardwood floor removal services in Colbert, Washington"
        },
        {
            "business_name": "57 Wood Floors",
            "city": "SEQUIM",
            "state": "WA",
            "url": "https://www.straitfloors.com/p",
            "title": "Strait Floors - Professional Flooring Services",
            "snippet": "Quality flooring installation and repair services"
        },
        {
            "business_name": "509 CUSTOM PAINTING & DRYWALL",
            "city": "SPOKANE",
            "state": "WA",
            "url": "https://brietspainting.com/about-us/best-painter-in-spokane-6491396",
            "title": "Briet Painting - Professional Painting Services",
            "snippet": "Best painter in Spokane area - professional painting services"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST CASE {i}: {case['business_name']}")
        print(f"{'='*60}")
        
        # Create mock search item
        search_item = {
            'title': case['title'],
            'snippet': case['snippet'],
            'link': case['url']
        }
        
        # Test the confidence calculation
        confidence = service._calculate_search_confidence(
            search_item, 
            case['business_name'], 
            case['city'], 
            case['state']
        )
        
        print(f"📋 Test Data:")
        print(f"  Business: {case['business_name']}")
        print(f"  Location: {case['city']}, {case['state']}")
        print(f"  URL: {case['url']}")
        print(f"  Title: {case['title']}")
        print(f"  Snippet: {case['snippet']}")
        
        print(f"\n🎯 Results:")
        print(f"  Confidence: {confidence:.3f}")
        print(f"  Would Accept: {'❌ NO' if confidence < 0.4 else '✅ YES'}")
        
        # Test geographic validation
        has_wa_location = service._has_wa_location_indicators(
            case['url'], case['title'], case['snippet']
        )
        print(f"  Has WA Location: {'✅ YES' if has_wa_location else '❌ NO'}")
        
        # Test domain validation
        is_valid_domain = service._is_valid_website(case['url'])
        print(f"  Valid Domain: {'✅ YES' if is_valid_domain else '❌ NO'}")
        
        print(f"\n📊 Analysis:")
        if confidence < 0.4:
            print(f"  ✅ CORRECTLY REJECTED - Confidence too low ({confidence:.3f})")
        else:
            print(f"  ❌ INCORRECTLY ACCEPTED - Should have been rejected")
    
    print(f"\n{'='*60}")
    print("🧪 STRICT VALIDATION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_strict_validation()) 