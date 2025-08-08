#!/usr/bin/env python3
import asyncio
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.database.models import Contractor

async def test_specific_contractor(contractor_name=None):
    """Test processing of a specific contractor with detailed logging"""
    await db_pool.initialize()
    
    # Get a specific contractor for testing
    async with db_pool.pool.acquire() as conn:
        if contractor_name:
            # Search for contractor by name
            result = await conn.fetchrow('''
                SELECT * FROM contractors 
                WHERE business_name ILIKE $1
                LIMIT 1
            ''', f'%{contractor_name}%')
            
            if not result:
                print(f"No contractor found matching: {contractor_name}")
                return
        else:
            # Get a contractor that hasn't been processed yet
            result = await conn.fetchrow('''
                SELECT * FROM contractors 
                WHERE processing_status = 'pending' 
                LIMIT 1
            ''')
            
            if not result:
                print("No pending contractors found")
                return
        
        # Create contractor object
        contractor = Contractor(**dict(result))
        print(f"Testing contractor: {contractor.business_name}")
        print(f"Location: {contractor.city}, {contractor.state}")
        print(f"Principal: {contractor.primary_principal_name}")
        print(f"License: {contractor.contractor_license_number}")
        print("=" * 60)
        
        # Process the contractor
        service = ContractorService()
        try:
            processed_contractor = await service.process_contractor(contractor)
            
            print(f"\nRESULTS:")
            print(f"Website URL: {processed_contractor.website_url}")
            print(f"Website Confidence: {processed_contractor.website_confidence}")
            print(f"Classification Confidence: {processed_contractor.classification_confidence}")
            print(f"Overall Confidence: {processed_contractor.confidence_score}")
            print(f"Processing Status: {processed_contractor.processing_status}")
            print(f"Review Status: {processed_contractor.review_status}")
            print(f"Category: {processed_contractor.mailer_category}")
            print(f"Residential Focus: {processed_contractor.residential_focus}")
            
            # Show AI analysis results if available
            if processed_contractor.data_sources and 'ai_analysis' in processed_contractor.data_sources:
                ai_analysis = processed_contractor.data_sources['ai_analysis']
                print(f"\nAI Analysis Results:")
                print(f"  Category: {ai_analysis.get('category')}")
                print(f"  Confidence: {ai_analysis.get('confidence')}")
                print(f"  Residential Focus: {ai_analysis.get('residential_focus')}")
                print(f"  Services Offered: {ai_analysis.get('services_offered')}")
                print(f"  Business Legitimacy: {ai_analysis.get('business_legitimacy')}")
                print(f"  Reasoning: {ai_analysis.get('reasoning')}")
            
            # Show crawled content preview
            if processed_contractor.data_sources and 'crawled_content' in processed_contractor.data_sources:
                content = processed_contractor.data_sources['crawled_content']
                print(f"\nCrawled Content Preview (first 500 chars):")
                print(f"  {content[:500]}...")
            
        except Exception as e:
            print(f"Error processing contractor: {e}")
            import traceback
            traceback.print_exc()
        
        await service.close()
    
    await db_pool.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test processing of a specific contractor')
    parser.add_argument('--contractor', '-c', type=str, help='Contractor name to test (partial match)')
    args = parser.parse_args()
    
    asyncio.run(test_specific_contractor(args.contractor)) 