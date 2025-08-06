#!/usr/bin/env python3
"""
Test script to debug domain matching issue
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def test_domain_matching():
    """Test domain matching for 3 Bridges Electric"""
    service = ContractorService()
    
    # Create contractor object with correct website URL
    contractor = Contractor(
        id=61291,
        business_name='3 BRIDGES ELECTRIC',
        website_url='https://3bridgeselectric.com/',
        contractor_license_number='3BRIDBE787LA',
        phone_number='(253) 590-8973',
        address1='1509 PROSPECT ST',
        primary_principal_name='HUFF, DAVID J'
    )
    
    print("Testing domain matching for 3 Bridges Electric")
    print(f"Business name: {contractor.business_name}")
    print(f"Website URL: {contractor.website_url}")
    
    # Test domain matching directly
    domain_score = service._domain_business_name_matching(contractor.business_name, contractor.website_url)
    print(f"Direct domain match score: {domain_score}")
    
    # Test validation with content
    test_content = "3 Bridges Electric is a full-service electrical contractor"
    validation_results = await service._comprehensive_website_validation(contractor, test_content, None)
    
    print(f"Validation results domain match score: {validation_results.get('domain_match_score', 0.0)}")
    print(f"Validation confidence: {service._calculate_validation_confidence(validation_results)}")
    
    # Test with Squarespace URL
    contractor.website_url = 'https://panda-octahedron-3mz8.squarespace.com/'
    domain_score_squarespace = service._domain_business_name_matching(contractor.business_name, contractor.website_url)
    print(f"Squarespace domain match score: {domain_score_squarespace}")
    
    validation_results_squarespace = await service._comprehensive_website_validation(contractor, test_content, None)
    print(f"Squarespace validation domain match score: {validation_results_squarespace.get('domain_match_score', 0.0)}")
    print(f"Squarespace validation confidence: {service._calculate_validation_confidence(validation_results_squarespace)}")

if __name__ == "__main__":
    asyncio.run(test_domain_matching()) 