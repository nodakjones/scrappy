#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.contractor_service import ContractorService

def test_domain_matching():
    """Test the domain matching function for 3 Bridges Electric"""
    service = ContractorService()
    
    business_name = "3 BRIDGES ELECTRIC"
    legitimate_url = "https://3bridgeselectric.com/"
    squarespace_url = "https://panda-octahedron-3mz8.squarespace.com/"
    
    print(f"Testing domain matching for: {business_name}")
    print(f"Legitimate URL: {legitimate_url}")
    print(f"Squarespace URL: {squarespace_url}")
    print()
    
    # Test legitimate domain
    legitimate_score = service._domain_business_name_matching(business_name, legitimate_url)
    print(f"Legitimate domain score: {legitimate_score}")
    
    # Test squarespace domain
    squarespace_score = service._domain_business_name_matching(business_name, squarespace_url)
    print(f"Squarespace domain score: {squarespace_score}")
    
    print()
    print("Expected results:")
    print("- Legitimate domain should get 0.20 (2 words: 'bridges' + 'electric')")
    print("- Squarespace domain should get 0.00 (no business name words)")

if __name__ == "__main__":
    test_domain_matching() 