#!/usr/bin/env python3
"""
Reprocess Specific Contractors
============================

Reprocess specific contractors that should have found websites but didn't.
"""

import asyncio
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.database.models import Contractor
from src.services.contractor_service import ContractorService, QuotaExceededError, quota_tracker

class SpecificContractorReprocessor:
    def __init__(self):
        self.service = ContractorService()
        
    async def initialize(self):
        """Initialize the reprocessor"""
        await db_pool.initialize()
        print("🔍 SPECIFIC CONTRACTOR REPROCESSING")
        print("=" * 50)
        
    async def find_contractors_by_name(self, business_names: List[str]) -> List[Contractor]:
        """Find contractors by business name"""
        contractors = []
        
        for business_name in business_names:
            query = """
                SELECT * FROM contractors 
                WHERE business_name ILIKE $1
                AND status_code = 'A'
                ORDER BY id
                LIMIT 1
            """
            
            rows = await db_pool.fetch(query, f"%{business_name}%")
            if rows:
                # Filter out fields that don't exist in Contractor model
                row_data = dict(rows[0])
                # Remove puget_sound field if it exists
                if 'puget_sound' in row_data:
                    del row_data['puget_sound']
                
                contractor = Contractor(**row_data)
                contractors.append(contractor)
                print(f"✅ Found: {contractor.business_name} (ID: {contractor.id})")
            else:
                print(f"❌ Not found: {business_name}")
        
        return contractors
    
    async def reprocess_contractor(self, contractor: Contractor) -> dict:
        """Reprocess a single contractor"""
        print(f"\n🔄 Reprocessing: {contractor.business_name}")
        print(f"   - Current website: {contractor.website_url or 'None'}")
        print(f"   - Current confidence: {contractor.confidence_score or 0.0}")
        
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
        try:
            from src.utils.logging_utils import contractor_logger
            
            # Use the full process_contractor method that includes 6-factor validation
            try:
                processed_contractor = await self.service.process_contractor(contractor)
                
                print(f"   - Website found: {processed_contractor.website_url or 'None'}")
                print(f"   - Website confidence: {processed_contractor.website_confidence or 0.0:.3f}")
                print(f"   - Classification confidence: {processed_contractor.classification_confidence or 0.0:.3f}")
                print(f"   - Overall confidence: {processed_contractor.confidence_score or 0.0:.3f}")
                print(f"   - Review status: {processed_contractor.review_status}")
                
                return {
                    'business_name': processed_contractor.business_name,
                    'website_url': processed_contractor.website_url,
                    'confidence_score': processed_contractor.confidence_score,
                    'review_status': processed_contractor.review_status,
                    'processing_status': processed_contractor.processing_status
                }
                
            except QuotaExceededError:
                print(f"   🛑 Quota exceeded - stopping processing")
                contractor.processing_status = 'failed'
                contractor.error_message = 'Daily Google API quota exceeded'
                await self.service.update_contractor(contractor)
                raise QuotaExceededError("Daily Google API quota exceeded")
                
            except Exception as e:
                print(f"   ❌ Processing failed: {e}")
                contractor.processing_status = 'failed'
                contractor.error_message = str(e)
                await self.service.update_contractor(contractor)
                
                return {
                    'business_name': contractor.business_name,
                    'website_url': contractor.website_url,
                    'confidence_score': contractor.confidence_score,
                    'review_status': contractor.review_status,
                    'processing_status': contractor.processing_status
                }
                
        except Exception as e:
            print(f"   ❌ Fatal error: {e}")
            return {
                'business_name': contractor.business_name,
                'website_url': None,
                'confidence_score': 0.0,
                'review_status': 'failed',
                'processing_status': 'failed'
            }
    
    async def reprocess_contractors(self, business_names: List[str]):
        """Reprocess multiple contractors"""
        await self.initialize()
        
        print(f"📋 Reprocessing {len(business_names)} contractors...")
        print()
        
        # Find contractors
        contractors = await self.find_contractors_by_name(business_names)
        
        if not contractors:
            print("❌ No contractors found to reprocess")
            await db_pool.close()
            return
        
        print(f"\n🔄 Starting reprocessing...")
        print()
        
        results = []
        for i, contractor in enumerate(contractors, 1):
            print(f"📊 Processing {i}/{len(contractors)}: {contractor.business_name}")
            
            try:
                result = await self.reprocess_contractor(contractor)
                results.append(result)
                
                # Check quota after each contractor
                if quota_tracker.is_quota_exceeded():
                    print(f"🛑 Daily quota exceeded - stopping reprocessing")
                    break
                    
            except QuotaExceededError:
                print(f"🛑 Daily quota exceeded - stopping reprocessing")
                break
            except Exception as e:
                print(f"❌ Error processing {contractor.business_name}: {e}")
                results.append({
                    'business_name': contractor.business_name,
                    'website_url': None,
                    'confidence_score': 0.0,
                    'review_status': 'failed',
                    'processing_status': 'failed'
                })
        
        # Print results summary
        print(f"\n📊 REPROCESSING RESULTS")
        print("=" * 50)
        
        websites_found = sum(1 for r in results if r['website_url'])
        high_confidence = sum(1 for r in results if r['confidence_score'] and r['confidence_score'] >= 0.8)
        medium_confidence = sum(1 for r in results if r['confidence_score'] and 0.6 <= r['confidence_score'] < 0.8)
        low_confidence = sum(1 for r in results if r['confidence_score'] and r['confidence_score'] < 0.6)
        
        print(f"📈 Summary:")
        print(f"   - Total processed: {len(results)}")
        print(f"   - Websites found: {websites_found}")
        print(f"   - High confidence (≥0.8): {high_confidence}")
        print(f"   - Medium confidence (0.6-0.79): {medium_confidence}")
        print(f"   - Low confidence (<0.6): {low_confidence}")
        
        print(f"\n📋 Detailed Results:")
        for result in results:
            status_icon = "✅" if result['website_url'] else "❌"
            confidence = f"{result['confidence_score']:.3f}" if result['confidence_score'] is not None else "0.000"
            print(f"   {status_icon} {result['business_name']}")
            print(f"      - Website: {result['website_url'] or 'None'}")
            print(f"      - Confidence: {confidence}")
            print(f"      - Status: {result['review_status']}")
            print()
        
        await db_pool.close()
        await self.service.close()

async def main():
    """Main function"""
    # List of contractors to reprocess
    business_names = [
        "3 BRIDGES ELECTRIC"
    ]
    
    reprocessor = SpecificContractorReprocessor()
    await reprocessor.reprocess_contractors(business_names)

if __name__ == "__main__":
    asyncio.run(main()) 