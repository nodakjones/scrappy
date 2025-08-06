#!/usr/bin/env python3
"""
Test script to simulate actual processing and debug website selection
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def test_processing_simulation():
    """Simulate the actual processing to debug website selection"""
    service = ContractorService()
    
    # Create contractor object
    contractor = Contractor(
        id=61291,
        business_name='3 BRIDGES ELECTRIC',
        website_url=None,  # Start with no website
        contractor_license_number='3BRIDBE787LA',
        phone_number='(253) 590-8973',
        address1='1509 PROSPECT ST',
        primary_principal_name='HUFF, DAVID J',
        city='TACOMA',
        state='WA'
    )
    
    print("Simulating website discovery process")
    print(f"Business name: {contractor.business_name}")
    
    # Simulate the website discovery process
    best_result = None
    best_confidence = 0.0
    
    # Test correct website
    correct_url = 'https://3bridgeselectric.com/'
    correct_content = "3 Bridges Electric is a full-service electrical contractor based in Tacoma, Washington"
    
    print(f"\nTesting correct website: {correct_url}")
    
    # Simulate crawling and validation
    contractor.website_url = correct_url
    validation_results = await service._comprehensive_website_validation(contractor, correct_content, None)
    validation_confidence = service._calculate_validation_confidence(validation_results)
    
    print(f"Correct website validation confidence: {validation_confidence}")
    print(f"Domain match score: {validation_results.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results.get('keyword_business_name_match', False)}")
    
    if validation_confidence > best_confidence:
        best_result = {
            'url': correct_url,
            'content': correct_content,
            'confidence': validation_confidence
        }
        best_confidence = validation_confidence
        print(f"✅ Correct website selected with confidence: {validation_confidence}")
    
    # Test Squarespace website
    squarespace_url = 'https://panda-octahedron-3mz8.squarespace.com/'
    squarespace_content = "3 Bridges Electric is a full-service electrical contractor"
    
    print(f"\nTesting Squarespace website: {squarespace_url}")
    
    # Simulate crawling and validation
    contractor.website_url = squarespace_url
    validation_results_squarespace = await service._comprehensive_website_validation(contractor, squarespace_content, None)
    validation_confidence_squarespace = service._calculate_validation_confidence(validation_results_squarespace)
    
    print(f"Squarespace validation confidence: {validation_confidence_squarespace}")
    print(f"Domain match score: {validation_results_squarespace.get('domain_match_score', 0.0)}")
    print(f"Business name match: {validation_results_squarespace.get('business_name_match', False)}")
    print(f"Keyword business name match: {validation_results_squarespace.get('keyword_business_name_match', False)}")
    
    if validation_confidence_squarespace > best_confidence:
        best_result = {
            'url': squarespace_url,
            'content': squarespace_content,
            'confidence': validation_confidence_squarespace
        }
        best_confidence = validation_confidence_squarespace
        print(f"✅ Squarespace website selected with confidence: {validation_confidence_squarespace}")
    
    print(f"\nFinal result:")
    if best_result:
        print(f"Selected website: {best_result['url']}")
        print(f"Confidence: {best_result['confidence']}")
    else:
        print("No website selected")

if __name__ == "__main__":
    asyncio.run(test_processing_simulation()) 