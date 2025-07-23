#!/usr/bin/env python3
"""
Main processing script for contractor enrichment system
Processes contractors using Google Search and OpenAI APIs
"""
import asyncio
import sys
import os
import logging
import json
import aiohttp
import openai
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from src.database.connection import DatabasePool

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContractorProcessor:
    """Main contractor processing class"""
    
    def __init__(self):
        self.db_pool = DatabasePool()
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.session = None
        
        # Processing statistics
        self.stats = {
            'processed': 0,
            'auto_approved': 0,
            'manual_review': 0,
            'failed': 0,
            'start_time': None
        }
    
    async def initialize(self):
        """Initialize the processor"""
        logger.info("Initializing Contractor Processor...")
        await self.db_pool.initialize()
        self.session = aiohttp.ClientSession()
        self.stats['start_time'] = datetime.now()
        logger.info("✅ Processor initialized successfully")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        await self.db_pool.close()
        logger.info("✅ Processor cleanup completed")
    
    async def get_pending_contractors(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get contractors pending processing"""
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        query = f"""
            SELECT id, uuid, business_name, city, state, phone_number, 
                   address1, contractor_license_type_code_desc
            FROM contractors 
            WHERE processing_status = 'pending'
            ORDER BY id
            {limit_clause}
        """
        
        result = await self.db_pool.fetch(query)
        return [dict(row) for row in result]
    
    async def search_contractor_online(self, contractor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Search for contractor information using Google Custom Search"""
        try:
            # Build search query
            query_parts = [contractor['business_name']]
            if contractor.get('city'):
                query_parts.append(contractor['city'])
            if contractor.get('state'):
                query_parts.append(contractor['state'])
            
            search_query = " ".join(query_parts)
            
            # Google Custom Search API call
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_search_engine_id,
                'q': search_query,
                'num': 5
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                elif response.status == 429:
                    logger.warning("Google API rate limit reached, waiting...")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.warning(f"Google search failed for {contractor['business_name']}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Search error for {contractor['business_name']}: {e}")
            return None
        
        # Rate limiting
        await asyncio.sleep(config.SEARCH_DELAY)
    
    async def analyze_with_ai(self, contractor: Dict[str, Any], search_results: List[Dict]) -> Dict[str, Any]:
        """Analyze contractor using OpenAI"""
        try:
            # Prepare context for AI analysis
            context = {
                'business_name': contractor['business_name'],
                'location': f"{contractor.get('city', '')}, {contractor.get('state', '')}",
                'license_type': contractor.get('contractor_license_type_code_desc', ''),
                'phone': contractor.get('phone_number', ''),
                'search_results': []
            }
            
            # Add search results context
            if search_results:
                for result in search_results[:3]:  # Limit to top 3 results
                    context['search_results'].append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'link': result.get('link', '')
                    })
            
            # AI analysis prompt
            prompt = f"""
Analyze this contractor business and provide categorization:

Business: {context['business_name']}
Location: {context['location']}
License Type: {context['license_type']}
Phone: {context['phone']}

Search Results:
{json.dumps(context['search_results'], indent=2)}

Please provide a JSON response with:
1. "category" - primary business category - USE SPECIFIC CATEGORIES ONLY: Plumbing, HVAC, Electrical, Roofing, Handyman, Flooring, Painting, Landscaping, Windows & Doors, Concrete, Fencing, Kitchen & Bath, etc. AVOID generic terms like "Construction"
2. "subcategory" - specific service type
3. "confidence" - confidence score 0-1 (1 = very confident)
4. "website" - business website if found
5. "description" - brief business description
6. "services" - array of main services offered
7. "verified" - true if search results confirm this is a real business
8. "is_residential" - true if this contractor primarily serves residential customers (homeowners), false if primarily commercial/industrial

IMPORTANT: For "category", be SPECIFIC:
- Use "Handyman" for general repair services
- Use "Roofing" for roofing contractors
- Use "Plumbing" for plumbing services
- Use "Electrical" for electrical work
- Use "HVAC" for heating/cooling
- Use "Painting" for painting services
- Use "Flooring" for flooring installation
- Use "Landscaping" for outdoor work
- DO NOT use generic "Construction" - be more specific

IMPORTANT: For "is_residential", be EXTREMELY CONSERVATIVE:
- ONLY mark "true" if business name explicitly contains "Home", "Residential", "House" OR website/search results explicitly mention "homeowners", "residential customers", "house calls"
- ONLY mark "false" if business name explicitly contains "Commercial", "Industrial", "Corporate" OR website/search results explicitly mention "commercial clients", "industrial services", "office buildings"
- If there's ANY uncertainty, missing website, or generic business name (like "Elite Plumbing", "ABC Construction"), mark as null
- Do NOT assume trade type indicates residential vs commercial - many plumbers, electricians, HVAC serve BOTH markets
- REQUIRE explicit evidence in name or web content - business type alone is insufficient
- Examples requiring EXPLICIT evidence: "Smith HOME Repair" (has "home"), "RESIDENTIAL HVAC Services" (has "residential"), "COMMERCIAL Construction Corp" (has "commercial")
- Examples that should be null: "Elite Plumbing" (could serve either), "ABC Construction" (unclear), "Best HVAC Services" (no market specified)

Respond with valid JSON only.
"""

            response = self.openai_client.chat.completions.create(
                model=config.GPT4_MINI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.OPENAI_MAX_TOKENS,
                temperature=config.OPENAI_TEMPERATURE
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                if ai_response.startswith('```json'):
                    ai_response = ai_response.replace('```json', '').replace('```', '').strip()
                elif ai_response.startswith('```'):
                    ai_response = ai_response.replace('```', '').strip()
                
                analysis = json.loads(ai_response)
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from AI for {contractor['business_name']}: {ai_response}")
                return {
                    'category': 'Unknown',
                    'confidence': 0.3,
                    'verified': False,
                    'is_residential': None,  # Don't guess - mark as unknown when uncertain
                    'error': 'Invalid AI response format'
                }
                
        except Exception as e:
            logger.error(f"AI analysis error for {contractor['business_name']}: {e}")
            return {
                'category': 'Unknown',
                'confidence': 0.1,
                'verified': False,
                'is_residential': None,  # Don't guess - mark as unknown when error occurs
                'error': str(e)
            }
        
        # Rate limiting
        await asyncio.sleep(config.LLM_DELAY)

    def filter_website_url(self, website_url: Optional[str]) -> Optional[str]:
        """Filter out directory and listing websites, return None if it's a directory site"""
        if not website_url:
            return None
        
        # Convert to lowercase for case-insensitive matching
        url_lower = website_url.lower()
        
        # Directory and listing sites to filter out
        directory_sites = [
            'yelp.com',
            'bbb.org',
            'better business bureau',
            'angieslist.com',
            'angi.com',
            'homeadvisor.com',
            'thumbtack.com',
            'porch.com',
            'yellowpages.com',
            'superpages.com',
            'manta.com',
            'foursquare.com',
            'facebook.com',
            'linkedin.com',
            'indeed.com',
            'glassdoor.com',
            'google.com/maps',
            'maps.google.com',
            'google.com/search',
            'zillow.com',        # Real estate listings
            'buildzoom.com',     # Contractor directory
            'mapquest.com',      # Map/directory service
            'bloomberg.com',     # Business directory
            'instagram.com',     # Social media
            'twitter.com',       # Social media
            'directory',
            'listings',
            'find_desc=',  # Google search URLs
            'find_loc=',   # Google search URLs
        ]
        
        # Check if URL contains any directory site patterns
        for directory_pattern in directory_sites:
            if directory_pattern in url_lower:
                return None
        
        # Additional checks for search result URLs
        if any(pattern in url_lower for pattern in ['search?', 'results?', 'find?']):
            return None
            
        return website_url
    
    async def update_contractor_results(self, contractor: Dict[str, Any], analysis: Dict[str, Any], search_results: List[Dict]):
        """Update contractor with processing results"""
        try:
            confidence = analysis.get('confidence', 0.0)
            
            # Determine processing status
            if confidence >= config.AUTO_APPROVE_THRESHOLD:
                processing_status = 'completed'
                review_status = 'approved_download'
            elif confidence >= config.MANUAL_REVIEW_THRESHOLD:
                processing_status = 'completed'
                review_status = 'pending_review'
            else:
                processing_status = 'completed'
                review_status = 'rejected'
            
            # Log search results
            if search_results:
                await self.db_pool.execute("""
                    INSERT INTO website_searches (contractor_id, search_query, search_results, search_method, results_found, success, attempted_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, contractor['id'], 
                f"{contractor['business_name']} {contractor.get('city', '')} {contractor.get('state', '')}", 
                json.dumps(search_results), 'google', len(search_results), True, datetime.now())
            
            # Update contractor record
            update_query = """
                UPDATE contractors SET
                    processing_status = $1,
                    review_status = $2,
                    confidence_score = $3,
                    mailer_category = $4,
                    website_url = $5,
                    business_description = $6,
                    services_offered = $7,
                    service_categories = $8,
                    last_processed = $9,
                    is_home_contractor = $10
                WHERE id = $11
            """
            
            # Prepare service categories array
            service_categories = [analysis.get('category', 'Unknown')]
            if analysis.get('subcategory'):
                service_categories.append(analysis.get('subcategory'))
            
            # Filter website URL to exclude directories and listings
            raw_website = analysis.get('website')
            filtered_website = self.filter_website_url(raw_website)
            
            # Get residential status - be conservative, don't guess
            is_residential = analysis.get('is_residential')  # None if uncertain, True/False if confident
            
            await self.db_pool.execute(
                update_query,
                processing_status,
                review_status,
                confidence,
                analysis.get('category'),
                filtered_website,
                analysis.get('description'),
                analysis.get('services', []),
                service_categories,
                datetime.now(),
                is_residential,  # is_home_contractor - can be None (unknown), True (residential), False (commercial)
                contractor['id']
            )
            
            # Update statistics
            self.stats['processed'] += 1
            if review_status == 'approved_download':
                self.stats['auto_approved'] += 1
            elif review_status == 'pending_review':
                self.stats['manual_review'] += 1
            else:
                self.stats['failed'] += 1
                
            logger.info(f"✅ Processed {contractor['business_name']} - {analysis.get('category', 'Unknown')} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating contractor {contractor['business_name']}: {e}")
    
    async def process_contractor(self, contractor: Dict[str, Any]):
        """Process a single contractor"""
        try:
            logger.info(f"Processing: {contractor['business_name']} ({contractor['city']}, {contractor['state']})")
            
            # Step 1: Search online
            search_results = await self.search_contractor_online(contractor)
            
            # Step 2: AI analysis
            analysis = await self.analyze_with_ai(contractor, search_results or [])
            
            # Step 3: Update database
            await self.update_contractor_results(contractor, analysis, search_results or [])
            
        except Exception as e:
            logger.error(f"Error processing contractor {contractor['business_name']}: {e}")
            self.stats['failed'] += 1
    
    async def process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of contractors"""
        logger.info(f"🔄 Processing batch of {len(batch)} contractors...")
        
        # Process contractors with concurrency control
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CRAWLS)
        
        async def process_with_semaphore(contractor):
            async with semaphore:
                await self.process_contractor(contractor)
        
        tasks = [process_with_semaphore(contractor) for contractor in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Print progress
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
        
        logger.info(f"📊 Progress: {self.stats['processed']} processed, "
                   f"{self.stats['auto_approved']} auto-approved, "
                   f"{self.stats['manual_review']} manual review, "
                   f"{self.stats['failed']} failed "
                   f"({rate:.2f} contractors/sec)")
    
    async def run(self, max_contractors: Optional[int] = None):
        """Main processing loop"""
        logger.info("🚀 Starting contractor processing...")
        
        try:
            await self.initialize()
            
            processed_count = 0
            
            while True:
                # Get next batch
                remaining = max_contractors - processed_count if max_contractors else None
                batch_size = min(config.BATCH_SIZE, remaining or config.BATCH_SIZE)
                
                contractors = await self.get_pending_contractors(batch_size)
                
                if not contractors:
                    logger.info("✅ No more contractors to process")
                    break
                
                # Process batch
                await self.process_batch(contractors)
                processed_count += len(contractors)
                
                # Check if we've reached the limit
                if max_contractors and processed_count >= max_contractors:
                    logger.info(f"✅ Reached processing limit of {max_contractors} contractors")
                    break
                
                # Brief pause between batches
                await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("⚠️ Processing interrupted by user")
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
        finally:
            await self.cleanup()
            
            # Final statistics
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            logger.info(f"""
🎯 PROCESSING COMPLETE!
═══════════════════════
Total Processed: {self.stats['processed']}
Auto-approved: {self.stats['auto_approved']}
Manual Review: {self.stats['manual_review']}  
Failed: {self.stats['failed']}
Processing Time: {elapsed:.1f} seconds
Average Rate: {self.stats['processed'] / elapsed if elapsed > 0 else 0:.2f} contractors/sec
""")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process contractor records')
    parser.add_argument('--max', type=int, help='Maximum number of contractors to process')
    parser.add_argument('--test', action='store_true', help='Process only 5 records for testing')
    
    args = parser.parse_args()
    
    max_contractors = None
    if args.test:
        max_contractors = 5
        logger.info("🧪 TEST MODE: Processing only 5 contractors")
    elif args.max:
        max_contractors = args.max
        logger.info(f"🎯 LIMITED MODE: Processing {max_contractors} contractors")
    else:
        logger.info("♾️ FULL MODE: Processing all pending contractors")
    
    processor = ContractorProcessor()
    await processor.run(max_contractors)

if __name__ == "__main__":
    asyncio.run(main())