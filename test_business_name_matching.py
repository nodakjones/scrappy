#!/usr/bin/env python3
"""
Test script to debug business name matching logic
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def test_business_name_matching():
    """Test business name matching logic"""
    service = ContractorService()
    
    business_name = '3 BRIDGES ELECTRIC'
    
    # Test with the actual content from the logs
    squarespace_content = """3 Bridges Electric 0 Skip to Content Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY COMMERCIAL &amp; RESIDENTIALELECTRICAL DONE RIGHT Three Bridges Electric is a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of el"""
    
    correct_content = """3 Bridges Electric: Tacoma's Trusted Electrical Services. We are a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of electrical work."""
    
    print("Testing business name matching logic")
    print(f"Business name: {business_name}")
    
    # Test Squarespace content
    print(f"\nTesting Squarespace content:")
    business_name_match_squarespace = service._advanced_business_name_matching(business_name, squarespace_content)
    keyword_match_squarespace = service._keyword_business_name_matching(business_name, squarespace_content)
    
    print(f"Business name match: {business_name_match_squarespace}")
    print(f"Keyword business name match: {keyword_match_squarespace}")
    
    # Test correct content
    print(f"\nTesting correct content:")
    business_name_match_correct = service._advanced_business_name_matching(business_name, correct_content)
    keyword_match_correct = service._keyword_business_name_matching(business_name, correct_content)
    
    print(f"Business name match: {business_name_match_correct}")
    print(f"Keyword business name match: {keyword_match_correct}")
    
    # Test domain matching
    print(f"\nTesting domain matching:")
    domain_match_correct = service._domain_business_name_matching(business_name, 'https://3bridgeselectric.com/')
    domain_match_squarespace = service._domain_business_name_matching(business_name, 'https://panda-octahedron-3mz8.squarespace.com/')
    
    print(f"Correct domain match: {domain_match_correct}")
    print(f"Squarespace domain match: {domain_match_squarespace}")

if __name__ == "__main__":
    asyncio.run(test_business_name_matching()) 