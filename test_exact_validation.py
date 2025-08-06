#!/usr/bin/env python3
"""
Test script to debug validation with exact same content and logic
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def test_exact_validation():
    """Test validation with exact same content and logic as actual processing"""
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
    
    print("Testing validation with exact same content and logic")
    
    # Use the exact content from the logs
    squarespace_content = """3 Bridges Electric 0 Skip to Content Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY Open Menu Close Menu Home About Services CALL TODAY COMMERCIAL &amp; RESIDENTIALELECTRICAL DONE RIGHT Three Bridges Electric is a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of el"""
    
    # Test Squarespace website with exact content
    print(f"\nTesting Squarespace website with exact content:")
    contractor.website_url = 'https://panda-octahedron-3mz8.squarespace.com/'
    validation_results_squarespace = await service._comprehensive_website_validation(contractor, squarespace_content, None)
    validation_confidence_squarespace = service._calculate_validation_confidence(validation_results_squarespace)
    
    print(f"Squarespace validation confidence: {validation_confidence_squarespace}")
    print(f"Domain match score: {validation_results_squarespace.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results_squarespace.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results_squarespace.get('keyword_business_name_match', False)}")
    print(f"License match: {validation_results_squarespace.get('license_match', False)}")
    print(f"Phone match: {validation_results_squarespace.get('phone_match', False)}")
    print(f"Address match: {validation_results_squarespace.get('address_match', False)}")
    print(f"Principal match: {validation_results_squarespace.get('principal_name_match', False)}")
    print(f"Contractor keywords: {validation_results_squarespace.get('contractor_keywords', 0)}")
    
    # Test correct website with simulated content
    print(f"\nTesting correct website with simulated content:")
    contractor.website_url = 'https://3bridgeselectric.com/'
    correct_content = """3 Bridges Electric: Tacoma's Trusted Electrical Services. We are a full-service electrical contractor based in Tacoma, Washington, serving Pierce, Kitsap, Mason, Thurston, and south King Counties. We are a professional, family owned and operated business. We strive to provide high quality service for all types of electrical work."""
    
    validation_results_correct = await service._comprehensive_website_validation(contractor, correct_content, None)
    validation_confidence_correct = service._calculate_validation_confidence(validation_results_correct)
    
    print(f"Correct website validation confidence: {validation_confidence_correct}")
    print(f"Domain match score: {validation_results_correct.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results_correct.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results_correct.get('keyword_business_name_match', False)}")
    print(f"License match: {validation_results_correct.get('license_match', False)}")
    print(f"Phone match: {validation_results_correct.get('phone_match', False)}")
    print(f"Address match: {validation_results_correct.get('address_match', False)}")
    print(f"Principal match: {validation_results_correct.get('principal_name_match', False)}")
    print(f"Contractor keywords: {validation_results_correct.get('contractor_keywords', 0)}")
    
    # Compare with logs
    print(f"\nComparison with logs:")
    print(f"Logs show Squarespace confidence: 0.6")
    print(f"Our test shows Squarespace confidence: {validation_confidence_squarespace}")
    print(f"Logs show correct website confidence: 0.2")
    print(f"Our test shows correct website confidence: {validation_confidence_correct}")

if __name__ == "__main__":
    asyncio.run(test_exact_validation()) 