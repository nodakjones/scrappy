"""
Contractor processing service for enrichment pipeline
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database.connection import db_pool
from ..database.models import Contractor
from ..config import config

logger = logging.getLogger(__name__)


class ContractorService:
    """Service for processing contractor enrichment pipeline"""
    
    def __init__(self):
        self.batch_size = config.BATCH_SIZE
        
    async def get_pending_contractors(self, limit: int = None) -> List[Contractor]:
        """Get contractors with pending processing status"""
        query = """
        SELECT * FROM contractors 
        WHERE processing_status = 'pending' 
        ORDER BY created_at ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        rows = await db_pool.fetch(query)
        
        contractors = []
        for row in rows:
            contractor = Contractor.from_dict(dict(row))
            contractors.append(contractor)
            
        logger.info(f"Retrieved {len(contractors)} pending contractors")
        return contractors
    
    async def process_contractor(self, contractor: Contractor) -> Contractor:
        """Process a single contractor through the enrichment pipeline"""
        logger.info(f"Processing contractor: {contractor.business_name}")
        
        try:
            # Update status to processing
            await self.update_contractor_status(contractor.id, 'processing')
            
            # Simulate website discovery
            website_confidence = await self.mock_website_discovery(contractor)
            
            # Simulate content analysis
            classification_confidence = await self.mock_content_analysis(contractor)
            
            # Calculate overall confidence
            overall_confidence = (website_confidence + classification_confidence) / 2
            
            # Update contractor with results
            contractor.website_confidence = website_confidence
            contractor.classification_confidence = classification_confidence
            contractor.confidence_score = overall_confidence
            contractor.processing_status = 'completed' if overall_confidence >= config.AUTO_APPROVE_THRESHOLD else 'manual_review'
            contractor.is_home_contractor = overall_confidence > 0.5  # Simple logic
            contractor.mailer_category = self.assign_category(contractor)
            contractor.last_processed = datetime.utcnow()
            
            # Save results
            await self.update_contractor(contractor)
            
            logger.info(f"Completed processing {contractor.business_name} with confidence {overall_confidence:.2f}")
            return contractor
            
        except Exception as e:
            logger.error(f"Error processing contractor {contractor.business_name}: {e}")
            contractor.processing_status = 'error'
            contractor.error_message = str(e)
            await self.update_contractor(contractor)
            raise
    
    async def mock_website_discovery(self, contractor: Contractor) -> float:
        """Mock website discovery with safe character handling"""
        # Simulate API delay
        await asyncio.sleep(config.SEARCH_DELAY)
        
        # Mock logic based on data quality
        confidence = 0.5  # base confidence
        
        if contractor.phone_number:
            confidence += 0.2
        if contractor.city and contractor.state:
            confidence += 0.2  
        if contractor.business_name and len(contractor.business_name) > 5:
            confidence += 0.1
            
        # Add some randomization to simulate real results
        import random
        confidence += random.uniform(-0.1, 0.1)
        confidence = max(0.0, min(1.0, confidence))
        
        # Mock website URL with safe character handling
        if confidence > 0.6:
            # Clean business name for URL generation
            business_name = contractor.business_name.lower()
            # Remove/replace problematic characters
            business_name = business_name.replace('#', '').replace('@', '').replace('$', '')
            business_name = business_name.replace(' ', '').replace('&', 'and').replace('-', '')
            business_name = business_name.replace('.', '').replace(',', '').replace('!', '')
            # Keep only alphanumeric characters
            business_name_clean = ''.join(c for c in business_name if c.isalnum())
            
            contractor.website_url = f"https://www.{business_name_clean[:20]}.com"
            contractor.website_status = 'found'
        else:
            contractor.website_status = 'not_found'
            
        return confidence
    
    async def mock_content_analysis(self, contractor: Contractor) -> float:
        """Mock LLM content analysis with safe JSON handling"""
        # Simulate LLM API delay
        await asyncio.sleep(config.LLM_DELAY)
        
        # Mock analysis based on contractor type and business name
        confidence = 0.6  # base confidence
        
        business_name = contractor.business_name.lower()
        
        # Check for home contractor keywords
        home_keywords = ['plumbing', 'electrical', 'roofing', 'hvac', 'construction', 
                        'remodeling', 'handyman', 'contractor', 'painting', 'flooring']
        
        keyword_matches = sum(1 for keyword in home_keywords if keyword in business_name)
        confidence += keyword_matches * 0.05
        
        # Check license type
        if contractor.contractor_license_type_code_desc:
            license_desc = contractor.contractor_license_type_code_desc.lower()
            if any(keyword in license_desc for keyword in home_keywords):
                confidence += 0.1
        
        confidence = max(0.0, min(1.0, confidence))
        
        # Mock GPT analysis data with safe string handling
        business_name_safe = contractor.business_name.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        contractor.gpt4mini_analysis = {
            "is_home_contractor": confidence > 0.5,
            "confidence": confidence,
            "reasoning": f"Business name '{business_name_safe}' analysis suggests home contractor likelihood of {confidence:.2f}",
            "keywords_found": keyword_matches,
            "business_name": business_name_safe,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return confidence
    
    def _safe_json_dumps(self, data: dict, business_name: str = "") -> Optional[str]:
        """Safely serialize data to JSON with error handling"""
        if not data:
            return None
            
        try:
            # First attempt: standard JSON serialization
            return json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON serialization failed for {business_name}: {e}")
            
            try:
                # Second attempt: with ASCII encoding
                return json.dumps(data, ensure_ascii=True)
            except (TypeError, ValueError) as e2:
                logger.error(f"Safe JSON serialization also failed for {business_name}: {e2}")
                
                # Fallback: create a minimal safe JSON structure
                safe_data = {
                    "error": "JSON serialization failed",
                    "business_name": business_name.replace('"', '\\"')[:100],  # Truncate and escape
                    "original_error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                try:
                    return json.dumps(safe_data, ensure_ascii=True)
                except:
                    # Ultimate fallback
                    return '{"error": "Critical JSON serialization failure"}'
    
    def assign_category(self, contractor: Contractor) -> str:
        """Assign mailer category based on business analysis"""
        business_name = contractor.business_name.lower()
        
        # Simple categorization logic
        if 'plumb' in business_name:
            return 'Plumbing'
        elif 'electric' in business_name:
            return 'Electrical'
        elif 'roof' in business_name:
            return 'Roofing'
        elif 'hvac' in business_name or 'heating' in business_name:
            return 'HVAC'
        elif 'paint' in business_name:
            return 'Painting'
        elif 'floor' in business_name:
            return 'Flooring'
        elif 'handyman' in business_name:
            return 'Handyman'
        else:
            return 'General Contractor'
    
    async def update_contractor_status(self, contractor_id: int, status: str):
        """Update contractor processing status"""
        await db_pool.execute(
            "UPDATE contractors SET processing_status = $1, updated_at = $2 WHERE id = $3",
            status, datetime.utcnow(), contractor_id
        )
    
    async def update_contractor(self, contractor: Contractor):
        """Update contractor record with processing results"""
        update_query = """
        UPDATE contractors SET 
            processing_status = $1,
            confidence_score = $2,
            website_confidence = $3,
            classification_confidence = $4,
            is_home_contractor = $5,
            mailer_category = $6,
            website_url = $7,
            website_status = $8,
            gpt4mini_analysis = $9,
            last_processed = $10,
            error_message = $11,
            updated_at = $12
        WHERE id = $13
        """
        
        await db_pool.execute(
            update_query,
            contractor.processing_status,
            contractor.confidence_score,
            contractor.website_confidence,  
            contractor.classification_confidence,
            contractor.is_home_contractor,
            contractor.mailer_category,
            contractor.website_url,
            contractor.website_status,
            self._safe_json_dumps(contractor.gpt4mini_analysis, contractor.business_name),
            contractor.last_processed,
            contractor.error_message,
            datetime.utcnow(),
            contractor.id
        )
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats_query = """
        SELECT 
            processing_status,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence
        FROM contractors 
        GROUP BY processing_status
        """
        
        rows = await db_pool.fetch(stats_query)
        
        stats = {}
        for row in rows:
            stats[row['processing_status']] = {
                'count': row['count'],
                'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0
            }
        
        return stats
    
    async def process_batch(self, contractors: List[Contractor]) -> Dict[str, int]:
        """Process a batch of contractors"""
        logger.info(f"Processing batch of {len(contractors)} contractors")
        
        results = {
            'processed': 0,
            'completed': 0,
            'manual_review': 0,
            'errors': 0
        }
        
        # Process contractors with concurrency limits
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CRAWLS)
        
        async def process_with_semaphore(contractor):
            async with semaphore:
                try:
                    processed_contractor = await self.process_contractor(contractor)
                    results['processed'] += 1
                    
                    if processed_contractor.processing_status == 'completed':
                        results['completed'] += 1
                    elif processed_contractor.processing_status == 'manual_review':
                        results['manual_review'] += 1
                        
                    return processed_contractor
                except Exception as e:
                    logger.error(f"Failed to process contractor {contractor.id}: {e}")
                    results['errors'] += 1
                    return contractor
        
        # Process all contractors concurrently
        await asyncio.gather(*[process_with_semaphore(contractor) for contractor in contractors])
        
        logger.info(f"Batch processing completed: {results}")
        return results