#!/usr/bin/env python3
"""
Reprocess A TEAM PAINTING specifically
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import db_pool
from src.database.models import Contractor
from src.services.contractor_service import ContractorService

async def reprocess_team_painting():
    """Reprocess A TEAM PAINTING specifically"""
    
    await db_pool.initialize()
    
    # Get the specific contractor
    query = "SELECT * FROM contractors WHERE id = 63065"
    row = await db_pool.fetchrow(query)
    
    if not row:
        print("❌ Contractor not found")
        return
    
    # Create contractor object
    contractor = Contractor(**dict(row))
    
    print("🔍 REPROCESSING A TEAM PAINTING")
    print("=" * 50)
    print(f"Business Name: {contractor.business_name}")
    print(f"ID: {contractor.id}")
    print(f"Current website: {contractor.website_url or 'None'}")
    print(f"Current confidence: {contractor.confidence_score or 0.0}")
    
    # Reset contractor to pending status
    contractor.processing_status = 'pending'
    contractor.website_url = None
    contractor.website_status = None
    contractor.confidence_score = None
    contractor.website_confidence = None
    contractor.classification_confidence = None
    contractor.mailer_category = None
    contractor.review_status = None
    contractor.error_message = None
    
    # Process contractor
    service = ContractorService()
    
    try:
        processed_contractor = await service.process_contractor(contractor)
        
        print(f"\n📊 RESULTS:")
        print(f"   - Website found: {processed_contractor.website_url or 'None'}")
        print(f"   - Website confidence: {processed_contractor.website_confidence or 0.0:.3f}")
        print(f"   - Classification confidence: {processed_contractor.classification_confidence or 0.0:.3f}")
        print(f"   - Overall confidence: {processed_contractor.confidence_score or 0.0:.3f}")
        print(f"   - Review status: {processed_contractor.review_status}")
        print(f"   - Processing status: {processed_contractor.processing_status}")
        
    except Exception as e:
        print(f"❌ Error processing contractor: {e}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(reprocess_team_painting()) 