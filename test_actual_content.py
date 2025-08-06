#!/usr/bin/env python3
"""
Test script to debug validation with actual crawled content
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def test_actual_content():
    """Test validation with actual crawled content"""
    service = ContractorService()
    
    # Create contractor object
    contractor = Contractor(
        id=61291,
        business_name='3 BRIDGES ELECTRIC',
        website_url=None,
        contractor_license_number='3BRIDBE787LA',
        phone_number='(253) 590-8973',
        address1='1509 PROSPECT ST',
        primary_principal_name='HUFF, DAVID J',
        city='TACOMA',
        state='WA'
    )
    
    print("Testing validation with actual crawled content")
    
    # Test with the actual content from the logs
    # This is the content that was crawled from the Squarespace website
    squarespace_content = """3 Bridges Electric 0 Skip to Content Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY COMMERCIAL &amp; RESIDENTIALELECTRICAL DONE RIGHT Three Bridges Electric is a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of el"""
    
    # Test with content from the correct website (simulated)
    correct_content = """3 Bridges Electric: Tacoma's Trusted Electrical Services. We are a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of electrical work."""
    
    # Test Squarespace website
    print(f"\nTesting Squarespace website with actual content:")
    contractor.website_url = 'https://panda-octahedron-3mz8.squarespace.com/'
    validation_results_squarespace = await service._comprehensive_website_validation(contractor, squarespace_content, None)
    validation_confidence_squarespace = service._calculate_validation_confidence(validation_results_squarespace)
    
    print(f"Squarespace validation confidence: {validation_confidence_squarespace}")
    print(f"Domain match score: {validation_results_squarespace.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results_squarespace.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results_squarespace.get('keyword_business_name_match', False)}")
    
    # Test correct website
    print(f"\nTesting correct website with simulated content:")
    contractor.website_url = 'https://3bridgeselectric.com/'
    validation_results_correct = await service._comprehensive_website_validation(contractor, correct_content, None)
    validation_confidence_correct = service._calculate_validation_confidence(validation_results_correct)
    
    print(f"Correct website validation confidence: {validation_confidence_correct}")
    print(f"Domain match score: {validation_results_correct.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results_correct.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results_correct.get('keyword_business_name_match', False)}")
    
    # Compare results
    print(f"\nComparison:")
    print(f"Squarespace confidence: {validation_confidence_squarespace}")
    print(f"Correct website confidence: {validation_confidence_correct}")
    
    if validation_confidence_correct > validation_confidence_squarespace:
        print("✅ Correct website should be selected")
    else:
        print("❌ Squarespace website would be selected")

if __name__ == "__main__":
    asyncio.run(test_actual_content()) 