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
import time
import aiohttp
import openai
import re
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
            'clearbit_success': 0,
            'google_fallback': 0,
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
    
    async def get_pending_contractors(self, limit: int = None, reprocess_no_website: bool = False) -> List[Dict[str, Any]]:
        """Get contractors pending processing"""
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        if reprocess_no_website:
            # Include contractors that were processed but have no website
            where_clause = """
                WHERE (processing_status = 'pending' 
                    OR (processing_status = 'completed' AND website_url IS NULL))
            """
        else:
            where_clause = "WHERE processing_status = 'pending'"
        
        query = f"""
            SELECT id, uuid, business_name, city, state, phone_number, 
                   address1, contractor_license_type_code_desc, website_url
            FROM contractors 
            {where_clause}
            ORDER BY id
            {limit_clause}
        """
        
        result = await self.db_pool.fetch(query)
        return [dict(row) for row in result]
    
    async def search_free_enrichment(self, contractor: Dict[str, Any]) -> Optional[str]:
        """Search for contractor website using free methods before paid APIs"""
        try:
            # Build company name for search
            company_name = contractor['business_name'].strip()
            
            # Clean up common business suffixes that might confuse search
            clean_name = re.sub(r'\s+(LLC|INC|CORP|CO|LTD|COMPANY)\.?$', '', company_name, flags=re.IGNORECASE)
            
            logger.info(f"🔍 Trying free enrichment for: {clean_name}")
            
            # Step 1: Try Clearbit (when available)
            try:
                clearbit_url = "https://company.clearbit.com/v1/domains/find"
                params = {'name': clean_name}
                
                async with self.session.get(clearbit_url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        domain = data.get('domain')
                        if domain:
                            website_url = f"https://{domain}"
                            logger.info(f"✅ Clearbit found website: {website_url}")
                            return website_url
                    elif response.status == 401:
                        logger.info(f"🔒 Clearbit requires authentication - skipping")
                    elif response.status != 404:  # 404 is normal "not found"
                        logger.info(f"⚠️ Clearbit API status {response.status}")
            except Exception as e:
                logger.info(f"⚠️ Clearbit unavailable: {e}")
            
            # Step 2: Try common domain patterns (completely free)
            logger.info(f"🎯 Trying domain guessing for: {clean_name}")
            
            # Generate potential domains from company name
            # Remove special chars, convert to lowercase, replace spaces with hyphens/nothing
            domain_base = re.sub(r'[^\w\s]', '', clean_name.lower())
            domain_variations = [
                re.sub(r'\s+', '', domain_base),           # nospaces: "abccompany"
                re.sub(r'\s+', '-', domain_base),          # hyphens: "abc-company"  
                domain_base.split()[0] if ' ' in domain_base else domain_base,  # first word: "abc"
            ]
            
            # Common TLDs to try
            tlds = ['.com', '.net', '.org']
            
            for domain_part in domain_variations:
                if len(domain_part) >= 3:  # Only try reasonable domain names
                    for tld in tlds:
                        potential_domain = f"{domain_part}{tld}"
                        potential_url = f"https://{potential_domain}"
                        
                        try:
                            # Quick HEAD request to check if domain exists
                            async with self.session.head(potential_url, timeout=3) as response:
                                if response.status in [200, 301, 302]:  # Success or redirect
                                    logger.info(f"✅ Domain guess successful: {potential_url}")
                                    return potential_url
                        except:
                            continue  # Try next variation
                        
                        await asyncio.sleep(0.1)  # Small delay between attempts
            
            logger.info(f"❌ No free enrichment found for: {company_name}")
            return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Free enrichment error for {contractor['business_name']}: {e}")
            return None
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    async def search_contractor_online(self, contractor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Search for contractor information using Google Custom Search (fallback)"""
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
                'num': 10  # Increased from 5 to 10 for better coverage
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
    
    async def crawl_website_content(self, url: str, contractor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crawl website content for deeper analysis"""
        try:
            logger.info(f"🕷️ Crawling website: {url}")
            
            # Set reasonable timeout and headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            start_time = time.time()
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                crawl_duration = time.time() - start_time
                
                # Log crawl attempt
                await self.db_pool.execute("""
                    INSERT INTO website_crawls (contractor_id, url, crawl_status, response_code, crawl_duration_seconds, attempted_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, contractor['id'], url, 'success' if response.status == 200 else 'error', 
                response.status, crawl_duration, datetime.now())
                
                if response.status == 200:
                    content = await response.text()
                    content_length = len(content)
                    
                    # Update crawl record with content info
                    await self.db_pool.execute("""
                        UPDATE website_crawls SET content_length = $1, raw_content = $2 
                        WHERE contractor_id = $3 AND url = $4 AND attempted_at = (
                            SELECT MAX(attempted_at) FROM website_crawls WHERE contractor_id = $3 AND url = $4
                        )
                    """, content_length, content[:50000], contractor['id'], url)  # Limit stored content to 50k chars
                    
                    # Extract meaningful content using simple text processing
                    website_content = self.extract_website_content(content)
                    
                    logger.info(f"✅ Successfully crawled {url} ({content_length} chars)")
                    return website_content
                else:
                    logger.warning(f"❌ Failed to crawl {url}: HTTP {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout crawling {url}")
            await self.db_pool.execute("""
                INSERT INTO website_crawls (contractor_id, url, crawl_status, response_code, attempted_at)
                VALUES ($1, $2, 'timeout', 0, $3)
            """, contractor['id'], url, datetime.now())
            return None
        except Exception as e:
            logger.error(f"❌ Error crawling {url}: {e}")
            await self.db_pool.execute("""
                INSERT INTO website_crawls (contractor_id, url, crawl_status, response_code, attempted_at)
                VALUES ($1, $2, 'error', 0, $3)
            """, contractor['id'], url, datetime.now())
            return None
        
        # Rate limiting for crawling
        await asyncio.sleep(config.CRAWL_DELAY)
    
    def extract_website_content(self, html_content: str) -> Dict[str, Any]:
        """Extract meaningful content from HTML for AI analysis"""
        from bs4 import BeautifulSoup
        import re
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract key content sections
            content = {
                'title': '',
                'about_us': '',
                'services': '',
                'description': '',
                'full_text': '',
                'contact_info': '',
                'keywords': []
            }
            
            # Get page title
            if soup.title:
                content['title'] = soup.title.string.strip() if soup.title.string else ''
            
            # Look for meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content['description'] = meta_desc['content'].strip()
            
            # Extract text from key sections
            text_content = soup.get_text()
            content['full_text'] = ' '.join(text_content.split())[:5000]  # Limit to 5k chars
            
            # Look for specific sections
            about_sections = soup.find_all(['div', 'section', 'p'], 
                string=re.compile(r'about|who we are|our story|our company', re.IGNORECASE))
            for section in about_sections[:2]:  # Limit to first 2 matches
                parent = section.find_parent(['div', 'section', 'article'])
                if parent:
                    about_text = parent.get_text().strip()
                    content['about_us'] += about_text[:1000] + ' '  # Limit per section
            
            # Look for services sections
            service_sections = soup.find_all(['div', 'section', 'ul'], 
                string=re.compile(r'services|what we do|our services|specialties', re.IGNORECASE))
            for section in service_sections[:2]:
                parent = section.find_parent(['div', 'section', 'article'])
                if parent:
                    service_text = parent.get_text().strip()
                    content['services'] += service_text[:1000] + ' '
            
            # Extract contact information
            contact_patterns = [
                r'residential|homeowner|home|house|family',
                r'commercial|business|corporate|industrial|office',
                r'emergency|24/7|available',
                r'licensed|insured|bonded'
            ]
            
            for pattern in contact_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                content['keywords'].extend(matches[:5])  # Limit matches per pattern
            
            # Clean up content
            for key in ['about_us', 'services', 'contact_info']:
                content[key] = ' '.join(content[key].split())[:2000]  # Clean whitespace and limit
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting website content: {e}")
            return {
                'title': '',
                'about_us': '',
                'services': '',
                'description': '',
                'full_text': html_content[:1000] if html_content else '',
                'contact_info': '',
                'keywords': []
            }
    
    async def analyze_with_ai(self, contractor: Dict[str, Any], search_results: List[Dict], website_content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            
            # Add website content if available
            context['website_content'] = website_content if website_content else {}
            
            # AI analysis prompt
            prompt = f"""
Analyze this contractor business and provide categorization:

Business: {context['business_name']}
Location: {context['location']}
License Type: {context['license_type']}
Phone: {context['phone']}

Search Results:
{json.dumps(context['search_results'], indent=2)}

Website Content (if available):
{json.dumps(context['website_content'], indent=2) if context['website_content'] else 'No website content available'}

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

IMPORTANT: For "is_residential", be EVIDENCE-BASED with website content priority:
- IF website content is available, analyze "about_us", "services", and "full_text" sections for clear market indicators
- Mark "true" if website mentions: "homeowners", "residential services", "home repair", "house calls", "serving families", "your home"
- Mark "false" if website mentions: "commercial clients", "business services", "industrial", "corporate", "office buildings", "serving businesses"
- If website content is NOT available, use EXTREMELY CONSERVATIVE approach:
  - ONLY mark "true" if business name explicitly contains "Home", "Residential", "House"
  - ONLY mark "false" if business name explicitly contains "Commercial", "Industrial", "Corporate"
  - Otherwise mark as null (uncertain)
- PRIORITIZE website content over business name when both available
- Examples with website content: website says "serving homeowners since 1995" → residential, website says "commercial building solutions" → commercial
- Examples without website: "Smith HOME Repair" → residential, "Elite Plumbing" → null (uncertain)

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
    
    def is_local_contractor(self, contractor: Dict[str, Any]) -> bool:
        """Check if contractor is in local service area based on phone number and location"""
        # Define local Washington area codes
        local_area_codes = ['206', '253', '360', '425', '509', '564']  # 206/Seattle, 253/Tacoma, 360/Olympia, 425/Eastside, 509/Spokane, 564/overlay
        
        phone = contractor.get('phone_number', '')
        city = contractor.get('city', '').upper()
        state = contractor.get('state', '').upper()
        
        # Must be Washington state
        if state != 'WA':
            return False
            
        # Check if phone number has local area code
        if phone:
            # Extract area code from phone number like (425) 772-8264
            phone_clean = phone.strip()
            if phone_clean.startswith('(') and ')' in phone_clean:
                area_code = phone_clean[1:4]
                if area_code in local_area_codes:
                    return True
                    
        # Also check for specific local cities if no valid phone
        local_cities = [
            'SEATTLE', 'TACOMA', 'SPOKANE', 'VANCOUVER', 'BELLEVUE', 'KENT', 'EVERETT',
            'RENTON', 'YAKIMA', 'FEDERAL WAY', 'SPOKANE VALLEY', 'BELLINGHAM', 'KENNEWICK',
            'AUBURN', 'PASCO', 'MARYSVILLE', 'LAKEWOOD', 'REDMOND', 'SHORELINE', 'RICHLAND',
            'KIRKLAND', 'BURIEN', 'LACEY', 'OLYMPIA', 'EDMONDS', 'LYNNWOOD', 'BOTHELL',
            'PUYALLUP', 'BREMERTON', 'SAMMAMISH', 'GIG HARBOR', 'ISSAQUAH', 'TUMWATER',
            'MERCER ISLAND', 'MOSES LAKE', 'MUKILTEO', 'UNIVERSITY PLACE', 'WENATCHEE',
            'LONGVIEW', 'PULLMAN', 'DES MOINES'
        ]
        
        if city in local_cities:
            return True
            
        return False

    def validate_website_belongs_to_contractor(self, website_content: Dict[str, Any], contractor: Dict[str, Any]) -> bool:
        """Validate that the crawled website actually belongs to the contractor"""
        if not website_content:
            return False
            
        contractor_phone = contractor.get('phone_number', '').strip()
        contractor_city = contractor.get('city', '').upper().strip()
        contractor_state = contractor.get('state', '').upper().strip()
        
        # Extract contractor's area code for comparison
        contractor_area_code = None
        if contractor_phone and contractor_phone.startswith('(') and ')' in contractor_phone:
            contractor_area_code = contractor_phone[1:4]
        
        # Search website content for phone numbers
        website_text = website_content.get('full_text', '') + ' ' + website_content.get('contact_info', '')
        
        # Look for phone patterns in website
        import re
        phone_patterns = re.findall(r'\((\d{3})\)\s*\d{3}[-\s]*\d{4}', website_text)
        
        # Check if contractor's area code appears on website
        if contractor_area_code and contractor_area_code in phone_patterns:
            logger.info(f"✅ Website validation PASSED: Found matching area code {contractor_area_code}")
            return True
            
        # Look for city/location matches
        if contractor_city and contractor_city in website_text.upper():
            logger.info(f"✅ Website validation PASSED: Found matching city {contractor_city}")
            return True
            
        # Look for state mentions
        if contractor_state and (contractor_state in website_text.upper() or 'WASHINGTON' in website_text.upper()):
            logger.info(f"✅ Website validation PASSED: Found matching state reference")
            return True
            
        # Check for Washington-specific keywords
        wa_keywords = ['SEATTLE', 'TACOMA', 'SPOKANE', 'WASHINGTON STATE', 'PUGET SOUND', 'KING COUNTY', 'PIERCE COUNTY']
        for keyword in wa_keywords:
            if keyword in website_text.upper():
                logger.info(f"✅ Website validation PASSED: Found Washington keyword {keyword}")
                return True
        
        # If no matches found, website likely doesn't belong to this contractor
        logger.warning(f"❌ Website validation FAILED: No matching contact info found")
        logger.warning(f"   Contractor: {contractor_phone} in {contractor_city}, {contractor_state}")
        logger.warning(f"   Website area codes found: {phone_patterns}")
        
        return False

    def validate_website_belongs_to_contractor_strict(self, crawled_content: Dict[str, Any], contractor: Dict[str, Any]) -> bool:
        """STRICT validation that website belongs to contractor - requires exact matches"""
        website_text = crawled_content.get('full_text', '').upper()
        contractor_phone = contractor.get('phone_number', '')
        contractor_city = contractor.get('city', '').upper()
        contractor_state = contractor.get('state', 'WA').upper()
        
        logger.info(f"🔍 STRICT validation for: {contractor['business_name']}")
        
        # Extract all phone numbers from website content
        import re
        phone_patterns = re.findall(r'\(?(253|206|360|425|509)\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', website_text)
        
        if phone_patterns:
            # Check if ANY phone number has Washington area codes
            wa_area_codes = {'253', '206', '360', '425', '509'}
            website_area_codes = [match[0] for match in phone_patterns]
            
            if any(code in wa_area_codes for code in website_area_codes):
                logger.info(f"✅ STRICT validation PASSED: Found WA area code(s): {website_area_codes}")
                
                # Additional check: must mention contractor's city or nearby cities
                if contractor_city in website_text:
                    logger.info(f"✅ STRICT validation PASSED: Found matching city {contractor_city}")
                    return True
                
                # Check for Puget Sound area cities
                puget_sound_cities = ['SEATTLE', 'BELLEVUE', 'TACOMA', 'EVERETT', 'SPOKANE', 'KIRKLAND', 'REDMOND', 'BOTHELL', 'LYNNWOOD', 'RENTON', 'KENT', 'FEDERAL WAY', 'BURIEN']
                if any(city in website_text for city in puget_sound_cities):
                    found_cities = [city for city in puget_sound_cities if city in website_text]
                    logger.info(f"✅ STRICT validation PASSED: Found Puget Sound cities: {found_cities}")
                    return True
        
        # Check for Washington-specific service area mentions
        wa_service_indicators = [
            'WASHINGTON STATE', 'PUGET SOUND', 'GREATER SEATTLE', 'EASTSIDE', 'SERVING SEATTLE',
            'KING COUNTY', 'PIERCE COUNTY', 'SNOHOMISH COUNTY', 'THURSTON COUNTY'
        ]
        
        for indicator in wa_service_indicators:
            if indicator in website_text:
                logger.info(f"✅ STRICT validation PASSED: Found service area indicator: {indicator}")
                return True
        
        logger.warning(f"❌ STRICT validation FAILED: No clear Washington connection found")
        return False

    def validate_website_belongs_to_contractor_extra_strict(self, crawled_content: Dict[str, Any], contractor: Dict[str, Any]) -> bool:
        """EXTRA STRICT validation for domain-guessed results - requires multiple confirmations"""
        website_text = crawled_content.get('full_text', '').upper()
        contractor_phone = contractor.get('phone_number', '')
        contractor_city = contractor.get('city', '').upper()
        contractor_state = contractor.get('state', 'WA').upper()
        contractor_name = contractor.get('business_name', '').upper()
        
        logger.info(f"🔍 EXTRA STRICT validation for domain guess: {contractor['business_name']}")
        
        validation_points = 0
        required_points = 3  # Need at least 3 confirmation points
        
        # 1. Phone number area code match
        import re
        phone_patterns = re.findall(r'\(?(253|206|360|425|509)\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', website_text)
        
        if phone_patterns:
            wa_area_codes = {'253', '206', '360', '425', '509'}
            website_area_codes = [match[0] for match in phone_patterns]
            
            if any(code in wa_area_codes for code in website_area_codes):
                validation_points += 2  # Strong indicator
                logger.info(f"✅ EXTRA STRICT +2 points: WA area codes {website_area_codes}")
        
        # 2. Exact city match
        if contractor_city in website_text:
            validation_points += 2  # Strong indicator
            logger.info(f"✅ EXTRA STRICT +2 points: Exact city match {contractor_city}")
        
        # 3. Business name similarity check
        # Remove common suffixes and check if core name appears
        core_name = re.sub(r'\s+(LLC|INC|CORP|CO|LTD|COMPANY)\.?$', '', contractor_name)
        name_words = core_name.split()
        
        if len(name_words) >= 2:
            # Check if at least 2 words from business name appear on website
            matches = sum(1 for word in name_words if len(word) >= 3 and word in website_text)
            if matches >= 2:
                validation_points += 1
                logger.info(f"✅ EXTRA STRICT +1 point: Business name similarity ({matches} word matches)")
        
        # 4. Service area indicators
        puget_sound_cities = ['SEATTLE', 'BELLEVUE', 'TACOMA', 'EVERETT', 'SPOKANE', 'KIRKLAND', 'REDMOND', 'BOTHELL', 'LYNNWOOD']
        city_mentions = sum(1 for city in puget_sound_cities if city in website_text)
        
        if city_mentions >= 2:
            validation_points += 1
            logger.info(f"✅ EXTRA STRICT +1 point: Multiple WA cities mentioned ({city_mentions})")
        
        # 5. Washington state references
        wa_indicators = ['WASHINGTON STATE', 'PUGET SOUND', 'GREATER SEATTLE', 'KING COUNTY', 'PIERCE COUNTY']
        if any(indicator in website_text for indicator in wa_indicators):
            validation_points += 1
            logger.info(f"✅ EXTRA STRICT +1 point: Washington state indicators")
        
        # Final validation
        if validation_points >= required_points:
            logger.info(f"✅ EXTRA STRICT validation PASSED: {validation_points}/{required_points} points")
            return True
        else:
            logger.warning(f"❌ EXTRA STRICT validation FAILED: {validation_points}/{required_points} points (insufficient)")
            return False

    async def process_contractor(self, contractor: Dict[str, Any]):
        """Process a single contractor"""
        try:
            # Step 0: Validate location first
            if not self.is_local_contractor(contractor):
                logger.info(f"⏭️ Skipping non-local contractor: {contractor['business_name']} ({contractor.get('city', 'Unknown')}, {contractor.get('state', 'Unknown')}) - Phone: {contractor.get('phone_number', 'None')}")
                self.stats['failed'] += 1
                return
                
            logger.info(f"Processing: {contractor['business_name']} ({contractor['city']}, {contractor['state']})")
            
            # Step 1: Google Search FIRST (accuracy over cost for data quality)
            website_content = None
            validated_website_url = None
            search_results = []
            
            logger.info("🎯 Using Google Search FIRST for maximum accuracy...")
            logger.info("💸 Prioritizing data quality over cost savings...")
            self.stats['google_fallback'] += 1
            search_results = await self.search_contractor_online(contractor)
            
            if search_results:
                logger.info(f"🔍 Searching through {len(search_results)} Google results for valid website...")
                
                # Look for legitimate website URLs (filtered)
                for i, result in enumerate(search_results, 1):
                    url = result.get('link', '')
                    logger.info(f"   📄 Result {i}/{len(search_results)}: {url}")
                    
                    filtered_url = self.filter_website_url(url)
                    if filtered_url:  # This is a legitimate website
                        logger.info(f"🎯 Found legitimate website: {filtered_url}")
                        crawled_content = await self.crawl_website_content(filtered_url, contractor)
                        
                        # Validate that this website actually belongs to the contractor with STRICT validation
                        if crawled_content and self.validate_website_belongs_to_contractor_strict(crawled_content, contractor):
                            website_content = crawled_content
                            validated_website_url = filtered_url
                            logger.info(f"✅ Website validated with STRICT validation: {filtered_url}")
                            break
                        else:
                            logger.warning(f"❌ Website rejected - doesn't match contractor (STRICT): {filtered_url}")
                            logger.info(f"   🔄 Continuing to search remaining {len(search_results) - i} results...")
                    else:
                        logger.info(f"   ⏭️ Skipped (directory/listing): {url}")
                
                if not validated_website_url:
                    logger.warning(f"🚫 No valid website found after checking all {len(search_results)} Google results")
            else:
                logger.warning("🚫 No Google search results found")
            
            # Step 2: ONLY try free enrichment if Google Search completely failed
            if not validated_website_url:
                logger.info("🔄 Google Search found no valid websites, trying free enrichment as last resort...")
                
                free_website = await self.search_free_enrichment(contractor)
                if free_website:
                    # Filter and validate free enrichment result with EXTRA STRICT validation
                    filtered_url = self.filter_website_url(free_website)
                    if filtered_url:
                        logger.info(f"🎯 Free enrichment provided legitimate website: {filtered_url}")
                        crawled_content = await self.crawl_website_content(filtered_url, contractor)
                        
                        # EXTRA STRICT validation for domain guessed results
                        if crawled_content and self.validate_website_belongs_to_contractor_extra_strict(crawled_content, contractor):
                            website_content = crawled_content
                            validated_website_url = filtered_url
                            logger.info(f"✅ Free enrichment website validated with EXTRA STRICT validation: {filtered_url}")
                            logger.info("💰 Cost savings: Used free methods after Google Search failed!")
                            self.stats['clearbit_success'] += 1
                            # Create mock search result for consistency
                            search_results = [{'link': filtered_url, 'title': f"{contractor['business_name']} - Free Enrichment", 'snippet': 'Found via free enrichment (last resort)'}]
                        else:
                            logger.warning(f"❌ Free enrichment website rejected - doesn't match contractor (EXTRA STRICT): {filtered_url}")
                    else:
                        logger.info(f"⏭️ Free enrichment website skipped (directory/listing): {free_website}")
                
                if not validated_website_url:
                    logger.warning("🚫 Both Google Search and free enrichment failed to find valid website")
            
            # Step 3: AI analysis with website content (only if validated)
            analysis = await self.analyze_with_ai(contractor, search_results or [], website_content)
            
            # Step 4: Update database (use validated website URL or None)
            if website_content and validated_website_url:
                # Update analysis to use validated website URL
                analysis['website'] = validated_website_url
            else:
                # No valid website found
                analysis['website'] = None
                
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
        logger.info(f"💰 Cost: {self.stats['clearbit_success']} Clearbit (free), "
                   f"{self.stats['google_fallback']} Google (paid)")
    
    async def run(self, max_contractors: Optional[int] = None, reprocess_no_website: bool = False):
        """Main processing loop"""
        logger.info("🚀 Starting contractor processing...")
        
        try:
            await self.initialize()
            
            processed_count = 0
            
            while True:
                # Get next batch
                remaining = max_contractors - processed_count if max_contractors else None
                batch_size = min(config.BATCH_SIZE, remaining or config.BATCH_SIZE)
                
                contractors = await self.get_pending_contractors(batch_size, reprocess_no_website=reprocess_no_website)
                
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
            total_processed = self.stats['processed']
            clearbit_success_rate = (self.stats['clearbit_success'] / total_processed * 100) if total_processed > 0 else 0
            google_fallback_rate = (self.stats['google_fallback'] / total_processed * 100) if total_processed > 0 else 0
            
            logger.info(f"""
🎯 PROCESSING COMPLETE!
═══════════════════════
Total Processed: {self.stats['processed']}
Auto-approved: {self.stats['auto_approved']}
Manual Review: {self.stats['manual_review']}  
Failed: {self.stats['failed']}

💰 COST OPTIMIZATION:
Clearbit Success: {self.stats['clearbit_success']} ({clearbit_success_rate:.1f}%)
Google Fallback: {self.stats['google_fallback']} ({google_fallback_rate:.1f}%)

Processing Time: {elapsed:.1f} seconds
Average Rate: {self.stats['processed'] / elapsed if elapsed > 0 else 0:.2f} contractors/sec
""")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process contractor records')
    parser.add_argument('--max', type=int, help='Maximum number of contractors to process')
    parser.add_argument('--test', action='store_true', help='Process only 5 records for testing')
    parser.add_argument('--reprocess-no-website', action='store_true', help='Reprocess contractors that have no website')
    
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
    await processor.run(max_contractors, reprocess_no_website=args.reprocess_no_website)

if __name__ == "__main__":
    asyncio.run(main())