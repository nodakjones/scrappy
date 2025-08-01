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

from src.config import config, EXCLUDED_DOMAINS
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

class ContractorLogger:
    """Direct logging for individual contractors - no buffering to prevent interleaving"""
    def __init__(self, contractor_id: str, contractor_name: str):
        self.contractor_id = contractor_id
        self.contractor_name = contractor_name
        
    def info(self, message: str):
        logger.info(message)
        
    def warning(self, message: str):
        logger.warning(message)
        
    def error(self, message: str):
        logger.error(message)
        
    def flush_to_main_logger(self):
        """No-op since we're logging directly now"""
        pass

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
    
    def is_excluded_website(self, url: str, website_content: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
        """Check if website should be excluded based on domain or industry association detection"""
        from urllib.parse import urlparse
        
        try:
            # Parse the URL to get the domain
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Exclude all government domains (.gov)
            if domain.endswith('.gov'):
                return True, f"Government domain: {domain}"
            
            # Exclude all educational domains (.edu)
            if domain.endswith('.edu'):
                return True, f"Educational domain: {domain}"
            
            # Check against excluded domains list
            if domain in EXCLUDED_DOMAINS:
                return True, f"Excluded domain: {domain}"
            
            # Check if website content indicates an industry association
            if website_content and website_content.get('is_industry_association', False):
                indicators = website_content.get('association_indicators', [])
                return True, f"Industry association detected: {indicators[:2]}"  # Show first 2 indicators
            
            return False, ""
            
        except Exception as e:
            logger.warning(f"Error checking excluded website {url}: {e}")
            return False, ""
    
    async def get_pending_contractors(self, limit: int = None, reprocess_no_website: bool = False) -> List[Dict[str, Any]]:
        """Get contractors pending processing (EXCLUDES expired/inactive contractors)"""
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        # Filter out expired and inactive contractors
        license_filter = """
            AND contractor_license_status NOT IN ('EXPIRED', 'RE-LICENSED', 'OUT OF BUSINESS', 'PASSED AWAY', 'REVOKED DUE DEPT ERR', 'INACTIVE', 'SUSPENDED')
            AND contractor_license_status IS NOT NULL
        """
        
        if reprocess_no_website:
            # Include contractors that were processed but have no website (and are active)
            where_clause = f"""
                WHERE (processing_status = 'pending' 
                    OR (processing_status = 'completed' AND website_url IS NULL))
                {license_filter}
            """
        else:
            where_clause = f"WHERE processing_status = 'pending' {license_filter}"
        
        # Add geographic filter to target Puget Sound area only (exclude Eastern WA)
        geographic_filter = """
            AND state = 'WA' 
            AND phone_number ~ '^\\((?:206|253|360|425|564)\\)'
        """
        
        query = f"""
            SELECT id, uuid, business_name, city, state, phone_number, 
                   address1, contractor_license_type_code_desc, contractor_license_status, website_url
            FROM contractors 
            {where_clause}
            {geographic_filter}
            ORDER BY id
            {limit_clause}
        """
        
        result = await self.db_pool.fetch(query)
        logger.info(f"🔍 Active contractors found: {len(result)} (filtered out expired/inactive)")
        return [dict(row) for row in result]
    
    async def search_free_enrichment(self, contractor: Dict[str, Any]) -> Optional[str]:
        """Search for contractor website using free methods before paid APIs"""
        try:
            # Build company name for search
            company_name = contractor['business_name'].strip()
            
            # Clean up common business suffixes that might confuse search
            clean_name = re.sub(r'\s+(LLC|INC|CORP|CO|LTD|COMPANY)\.?$', '', company_name, flags=re.IGNORECASE)
            
            logger.info(f"🔍 Trying free enrichment for: {clean_name}")
            
            # Step 1: Try Clearbit Autocomplete API (free, no auth required)
            try:
                clearbit_url = "https://autocomplete.clearbit.com/v1/companies/suggest"
                params = {'query': clean_name}
                
                async with self.session.get(clearbit_url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            domain = data[0].get('domain')
                            if domain:
                                website_url = f"https://{domain}"
                                logger.info(f"✅ Clearbit found website: {website_url}")
                                return website_url
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
            
            # Set comprehensive browser-like headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
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
                    
                    # Add raw HTML for phone number detection fallback
                    website_content['raw_html'] = content
                    
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
                'keywords': [],
                'is_industry_association': False,
                'association_indicators': []
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
            
            # INDUSTRY ASSOCIATION & UNION DETECTION
            # Check for industry association and labor union language patterns
            association_patterns = [
                # Generic association language
                r'supports?\s+professionals?\s+across',
                r'industry\s+association',
                r'trade\s+association',
                r'professional\s+association',
                r'contractors?\s+association',
                r'membership\s+organization',
                r'represents?\s+contractors?',
                r'serves?\s+the\s+\w+\s+industry',
                r'supports?\s+\w+\s+contractors?',
                
                # Specific association indicators
                r'plumbing.{0,50}heating.{0,50}cooling.{0,50}contractors?.{0,50}washington',
                r'electrical\s+contractors?\s+association',
                r'roofing\s+contractors?\s+association',
                r'building\s+contractors?\s+association',
                r'home\s+builders?\s+association',
                
                # Labor union patterns
                r'international\s+brotherhood',
                r'electrical\s+workers',
                r'local\s+\d+',  # Local 46, Local 123, etc.
                r'ibew',  # International Brotherhood of Electrical Workers
                r'united\s+association',
                r'plumbers?\s+and\s+pipefitters?',
                r'laborers?\s+international',
                r'operating\s+engineers?',
                r'carpenters?\s+union',
                r'ironworkers?\s+union',
                r'brotherhood\s+of',
                r'union\s+local',
                r'local\s+union',
                
                # Membership/collective language
                r'our\s+members?',
                r'member\s+contractors?',
                r'member\s+companies',
                r'certified\s+members?',
                r'member\s+directory',
                r'find\s+a\s+contractor',
                r'contractor\s+directory',
                
                # Training/education focus
                r'training\s+programs?',
                r'continuing\s+education',
                r'professional\s+development',
                r'certification\s+programs?',
                r'apprenticeship\s+programs?',
                r'journeyman\s+training',
                
                # Advocacy language
                r'advocates?\s+for',
                r'promoting\s+the\s+\w+\s+industry',
                r'advancing\s+the\s+profession',
                r'union\s+and\s+non.?union',
                r'both\s+union\s+and\s+non.?union',
                r'collective\s+bargaining',
                r'labor\s+relations'
            ]
            
            association_matches = []
            for pattern in association_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    association_matches.extend(matches)
            
            # Set association flag if multiple indicators found
            if len(association_matches) >= 2:  # Require at least 2 indicators
                content['is_industry_association'] = True
                content['association_indicators'] = association_matches[:5]  # Limit stored matches
            
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
                'keywords': [],
                'is_industry_association': False,
                'association_indicators': []
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

CRITICAL FIRST CHECK - INDUSTRY ASSOCIATION DETECTION:
If the website content shows "is_industry_association": true, or if you detect language indicating this is an industry association (not an individual contractor's business), immediately respond with:
{{
    "category": "Industry Association",
    "subcategory": "Trade Association",
    "confidence": 0.0,
    "website": null,
    "description": "Industry association website, not individual contractor",
    "services": [],
    "verified": false,
    "is_residential": null,
    "rejection_reason": "Industry association website detected"
}}

WEBSITE EXCLUSION INDICATORS TO WATCH FOR:
- **Government domains**: Any .gov website (never an individual contractor)
- **Educational domains**: Any .edu website (colleges, universities, schools)
- **Real estate sites**: Zillow, Redfin, Realtor.com, Trulia, etc. (property listings, not contractors)
- **Industry associations**: "supports professionals across", "industry association", "trade association"
- **Labor unions**: "International Brotherhood", "IBEW", "Local 46", "electrical workers", "united association"
- **Membership language**: "our members", "member contractors", "member directory"
- **Directory services**: "find a contractor", "contractor directory"
- **Collective language**: "both union and non-union contractors", "collective bargaining"
- **Training focus**: "apprenticeship programs", "journeyman training", "continuing education"
- **Examples**: 
  - "The Plumbing-Heating-Cooling Contractors of Washington supports professionals..."
  - "IBEW Local 46 represents electrical workers in the region"
  - "city.gov/licensing" or any government licensing site
  - "redfin.com/property-details" or real estate property listings

IF NOT AN ASSOCIATION, proceed with normal analysis:

Please provide a JSON response with:
1. "category" - primary business category - USE SPECIFIC CATEGORIES ONLY: Plumbing, HVAC, Electrical, Roofing, Handyman, Flooring, Painting, Landscaping, Windows & Doors, Auto Glass, Concrete, Fencing, Kitchen & Bath, etc. AVOID generic terms like "Construction"
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
- Use "Auto Glass" for windshield repair, auto glass replacement, mobile glass service
- Use "Windows & Doors" for residential window/door installation, NOT auto glass
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

    def _get_url_rejection_reason(self, website_url: Optional[str]) -> str:
        """Get detailed reason why a URL was rejected"""
        if not website_url:
            return "Empty/null URL"
        
        # Check against excluded domains first
        is_excluded, exclusion_reason = self.is_excluded_website(website_url)
        if is_excluded:
            return f"Excluded domain ({exclusion_reason})"
        
        # Convert to lowercase for case-insensitive matching
        url_lower = website_url.lower()
        
        # Directory and listing sites to filter out (backup to EXCLUDED_DOMAINS)
        directory_sites = [
            'yelp.com', 'bbb.org', 'better business bureau', 'angieslist.com', 'angi.com',
            'homeadvisor.com', 'thumbtack.com', 'porch.com', 'yellowpages.com', 'superpages.com',
            'manta.com', 'foursquare.com', 'facebook.com', 'linkedin.com', 'indeed.com',
            'glassdoor.com', 'google.com/maps', 'maps.google.com', 'google.com/search',
            'buildzoom.com', 'mapquest.com', 'bloomberg.com', 'instagram.com', 'twitter.com',
            'directory', 'listings', 'find_desc=', 'find_loc='
        ]
        
        # Check if URL contains any directory site patterns
        for directory_pattern in directory_sites:
            if directory_pattern in url_lower:
                return f"Directory/listing site ({directory_pattern})"
        
        # Additional checks for search result URLs
        search_patterns = ['search?', 'results?', 'find?']
        for pattern in search_patterns:
            if pattern in url_lower:
                return f"Search result URL ({pattern})"
        
        return "Unknown rejection reason"

    def filter_website_url(self, website_url: Optional[str]) -> Optional[str]:
        """Filter out directory, listing websites, excluded domains, and industry associations"""
        if not website_url:
            return None
        
        # Check against excluded domains first
        is_excluded, exclusion_reason = self.is_excluded_website(website_url)
        if is_excluded:
            return None
        
        # Convert to lowercase for case-insensitive matching
        url_lower = website_url.lower()
        
        # Directory and listing sites to filter out (backup to EXCLUDED_DOMAINS)
        directory_sites = [
            'yelp.com', 'bbb.org', 'better business bureau', 'angieslist.com', 'angi.com',
            'homeadvisor.com', 'thumbtack.com', 'porch.com', 'yellowpages.com', 'superpages.com',
            'manta.com', 'foursquare.com', 'facebook.com', 'linkedin.com', 'indeed.com',
            'glassdoor.com', 'google.com/maps', 'maps.google.com', 'google.com/search',
            'buildzoom.com', 'mapquest.com', 'bloomberg.com', 'instagram.com', 'twitter.com',
            'directory', 'listings', 'find_desc=', 'find_loc='
        ]
        
        # Check if URL contains any directory site patterns
        for directory_pattern in directory_sites:
            if directory_pattern in url_lower:
                return None
        
        # Additional checks for search result URLs
        if any(pattern in url_lower for pattern in ['search?', 'results?', 'find?']):
            return None
            
        return website_url
    
    async def update_contractor_results(self, contractor: Dict[str, Any], analysis: Dict[str, Any], search_results: List[Dict], website_content: Dict[str, Any] = None):
        """Update contractor with processing results"""
        try:
            # Get AI classification confidence
            ai_confidence = analysis.get('confidence', 0.0)
            
            # Get website confidence if available
            website_confidence = 0.0
            if website_content and 'website_confidence' in website_content:
                website_confidence = website_content['website_confidence']
            
            # Calculate combined confidence score
            # If we have a website, weight it 60% website + 40% AI classification
            # If no website, use 100% AI classification
            if website_confidence > 0:
                confidence = (website_confidence * 0.6) + (ai_confidence * 0.4)
                logger.info(f"📊 Combined Confidence: Website({website_confidence:.2f}) × 0.6 + AI({ai_confidence:.2f}) × 0.4 = {confidence:.2f}")
            else:
                confidence = ai_confidence
                logger.info(f"📊 AI-Only Confidence: {confidence:.2f} (no validated website)")
            
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
                    website_confidence = $4,
                    classification_confidence = $5,
                    mailer_category = $6,
                    website_url = $7,
                    business_description = $8,
                    services_offered = $9,
                    service_categories = $10,
                    last_processed = $11,
                    is_home_contractor = $12
                WHERE id = $13
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
                website_confidence if website_confidence > 0 else None,
                ai_confidence,
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
        # Define Puget Sound area codes (excluding Eastern WA)
        local_area_codes = ['206', '253', '360', '425', '564']  # 206/Seattle, 253/Tacoma, 360/Olympia, 425/Eastside, 564/overlay
        
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
        """ULTRA STRICT validation - requires business name, contractor services, AND location match"""
        website_text = crawled_content.get('full_text', '').upper()
        contractor_phone = contractor.get('phone_number', '')
        contractor_city = contractor.get('city', '').upper()
        contractor_state = contractor.get('state', 'WA').upper()
        contractor_name = contractor.get('business_name', '').upper()
        
        logger.info(f"🔍 ULTRA STRICT validation for: {contractor['business_name']}")
        
        # STEP 1: Business Name Verification (CRITICAL)
        business_name_match = self.verify_business_name_match(website_text, contractor_name)
        if not business_name_match:
            logger.warning(f"❌ ULTRA STRICT validation FAILED: No business name match found")
            return False
        
        # STEP 2: Contractor Service Verification (CRITICAL)  
        contractor_service_match = self.verify_contractor_services(website_text)
        if not contractor_service_match:
            logger.warning(f"❌ ULTRA STRICT validation FAILED: No contractor services found")
            return False
            
        # STEP 3: Location Verification (CRITICAL)
        raw_html = crawled_content.get('raw_html', '')
        location_match = self.verify_wa_location(website_text, contractor_city, raw_html)
        if not location_match:
            logger.warning(f"❌ ULTRA STRICT validation FAILED: No Washington location match")
            return False
        
        logger.info(f"✅ ULTRA STRICT validation PASSED: All requirements met!")
        return True
    
    def verify_business_name_match(self, website_text: str, contractor_name: str) -> bool:
        """Verify that business name or close derivative appears on website"""
        import re
        
        # Extract key words from business name (remove common suffixes)
        clean_name = re.sub(r'\s+(LLC|INC|CORP|CO|LTD|COMPANY)\s*$', '', contractor_name)
        name_words = clean_name.split()
        
        # Must match at least 2 significant words (ignore numbers and common words)
        significant_words = [word for word in name_words if len(word) > 2 and word not in ['THE', 'AND', 'OR']]
        
        if len(significant_words) < 2:
            # For single word companies, need exact match
            return clean_name in website_text
        
        # Check if at least 2 significant words appear on the website
        matches = sum(1 for word in significant_words if word in website_text)
        match_ratio = matches / len(significant_words)
        
        if match_ratio >= 0.6:  # At least 60% of significant words must match
            logger.info(f"✅ Business name match: {matches}/{len(significant_words)} words matched")
            return True
        
        logger.warning(f"❌ Business name mismatch: Only {matches}/{len(significant_words)} words matched")
        return False
    
    def verify_contractor_services(self, website_text: str) -> bool:
        """Verify website shows residential contractor services"""
        contractor_keywords = [
            # Construction services
            'CONSTRUCTION', 'CONTRACTOR', 'BUILDING', 'REMODELING', 'RENOVATION', 'REPAIR',
            # Specific trades
            'PLUMBING', 'ELECTRICAL', 'HVAC', 'ROOFING', 'FLOORING', 'TILE', 'CONCRETE',
            'PAINTING', 'DRYWALL', 'CARPENTRY', 'LANDSCAPING', 'FENCING', 'SIDING', 
            'WINDOWS', 'DOORS', 'KITCHEN', 'BATHROOM', 'BASEMENT', 'DECK', 'PATIO',
            # Service indicators  
            'HOME IMPROVEMENT', 'RESIDENTIAL', 'INSTALLATION', 'REPLACEMENT', 'MAINTENANCE',
            'HANDYMAN', 'GENERAL CONTRACTOR', 'SPECIALTY CONTRACTOR', 'LICENSED', 'INSURED',
            # Glass/Auto specific
            'GLASS REPAIR', 'WINDSHIELD', 'AUTO GLASS', 'GLASS REPLACEMENT', 'MOBILE GLASS'
        ]
        
        matches = sum(1 for keyword in contractor_keywords if keyword in website_text)
        
        if matches >= 2:  # Must find at least 2 contractor-related keywords
            logger.info(f"✅ Contractor services verified: Found {matches} service keywords")
            return True
        
        logger.warning(f"❌ No contractor services found: Only {matches} service keywords")
        return False
    
    def verify_wa_location(self, website_text: str, contractor_city: str, raw_html: str = None) -> bool:
        """Verify Washington state location indicators"""
        import re
        
        # Try both extracted text and raw HTML for phone number detection
        search_texts = [website_text]
        if raw_html:
            search_texts.append(raw_html)
        
        found_wa_phones = []
        
        for text_source in search_texts:
            # Extract all potential phone number patterns (with any formatting, including HTML entities)
            # Look for 3-3-4 digit patterns with flexible separators (spaces, dashes, dots, HTML entities, etc.)
            phone_candidates = re.findall(r'(?:^|[^\d])(\d{3})[^\d]{1,10}?(\d{3})[^\d]{1,10}?(\d{4})(?=[^\d]|$)', text_source)
            
            # Convert to 10-digit strings for easier processing
            digit_sequences = [''.join(match) for match in phone_candidates]
            
            # Washington area codes we care about
            wa_area_codes = {'253', '206', '360', '425', '509', '564'}  # Added 564 (new WA area code)
            
            for sequence in digit_sequences:
                # Check if it starts with a WA area code
                if len(sequence) >= 10:
                    area_code = sequence[:3]
                    if area_code in wa_area_codes:
                        # Format as readable phone number for logging
                        formatted_phone = f"({area_code}) {sequence[3:6]}-{sequence[6:10]}"
                        if formatted_phone not in found_wa_phones:  # Avoid duplicates
                            found_wa_phones.append(formatted_phone)
        
        logger.info(f"🔍 Found {len(found_wa_phones)} WA phone numbers across all sources")
        
        if found_wa_phones:
                logger.info(f"✅ WA location verified: Found phone number(s): {found_wa_phones}")
                
                # Additional check: must mention contractor's city or nearby cities (case-insensitive)
                if contractor_city.upper() in website_text.upper():
                    logger.info(f"✅ City match verified: {contractor_city}")
                    return True
                
                # Check for Puget Sound area cities (case-insensitive)
                puget_sound_cities = ['SEATTLE', 'BELLEVUE', 'TACOMA', 'EVERETT', 'SPOKANE', 'KIRKLAND', 'REDMOND', 'BOTHELL', 'LYNNWOOD', 'RENTON', 'KENT', 'FEDERAL WAY', 'BURIEN']
                if any(city in website_text.upper() for city in puget_sound_cities):
                    found_cities = [city for city in puget_sound_cities if city in website_text.upper()]
                    logger.info(f"✅ WA cities verified: {found_cities}")
                    return True
        
        # Check for Washington-specific service area mentions (case-insensitive)
        wa_service_indicators = [
            'WASHINGTON STATE', 'PUGET SOUND', 'GREATER SEATTLE', 'EASTSIDE', 'SERVING SEATTLE',
            'KING COUNTY', 'PIERCE COUNTY', 'SNOHOMISH COUNTY', 'THURSTON COUNTY'
        ]
        
        for indicator in wa_service_indicators:
            if indicator in website_text.upper():
                logger.info(f"✅ WA service area verified: {indicator}")
                return True
        
        logger.warning(f"❌ No WA location indicators found")
        return False

    def calculate_website_confidence_score(self, crawled_content: Dict[str, Any], contractor: Dict[str, Any]) -> float:
        """Calculate comprehensive 5-factor confidence score for website matching"""
        website_text = crawled_content.get('full_text', '').upper()
        contractor_name = contractor.get('business_name', '').upper()
        contractor_number = str(contractor.get('contractor_license_number', '')).upper()  # Contractor license number
        contractor_phone = contractor.get('phone_number', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        contractor_address = contractor.get('address1', '').upper()
        
        confidence_factors = []
        
        # Factor 1: Contractor Name Match (0.25 points)
        name_score = self.score_name_match(website_text, contractor_name)
        confidence_factors.append(('Name Match', name_score, 0.25))
        
        # Factor 2: Contractor Number Match (0.25 points)  
        number_score = self.score_contractor_number_match(website_text, contractor_number)
        confidence_factors.append(('License Number Match', number_score, 0.25))
        
        # Factor 3: Phone Number Match (0.25 points)
        phone_score = self.score_phone_match(website_text, contractor_phone)
        confidence_factors.append(('Phone Match', phone_score, 0.25))
        
        # Factor 4: Principal Name Match (0.25 points) - Not available in current data
        principal_score = 0.0  # TODO: Add when principal name data available
        confidence_factors.append(('Principal Match', principal_score, 0.25))
        
        # Factor 5: Address Match (0.25 points)
        address_score = self.score_address_match(website_text, contractor_address)
        confidence_factors.append(('Address Match', address_score, 0.25))

        # Calculate base confidence from 5 factors
        base_confidence = sum(score * weight for _, score, weight in confidence_factors)
        
        # Apply geographical validation penalty
        geographic_penalty = self.calculate_geographic_penalty(website_text, contractor)
        confidence_factors.append(('Geographic Validation', geographic_penalty, 1.0))
        
        # Calculate total confidence and cap at 1.0
        total_confidence = base_confidence + geographic_penalty
        total_confidence = min(total_confidence, 1.0)
        
        # Log confidence breakdown
        logger.info(f"🎯 Website Confidence Breakdown for {contractor['business_name']}:")
        for factor_name, score, weight in confidence_factors:
            if factor_name == 'Geographic Validation':
                if score < 0:
                    logger.info(f"   {factor_name}: PENALTY {score:.2f} (no WA area code or local address found)")
                else:
                    logger.info(f"   {factor_name}: PASS {score:.2f} (WA area code or local address found)")
            else:
                contribution = score * weight
                logger.info(f"   {factor_name}: {score:.1f}/1.0 × {weight} = {contribution:.2f}")
        
        raw_total = base_confidence + geographic_penalty
        if raw_total > 1.0:
            logger.info(f"   📊 Raw Total: {raw_total:.2f}/1.0 (capped at 1.0)")
            logger.info(f"   📊 Final Confidence: {total_confidence:.2f}/1.0")
        else:
            logger.info(f"   📊 Total Confidence: {total_confidence:.2f}/1.0")
        
        return total_confidence
    
    def score_name_match(self, website_text: str, contractor_name: str) -> float:
        """Score business name match (0.0 to 1.0)"""
        if not contractor_name:
            return 0.0
            
        # Clean contractor name (remove LLC, INC, etc.)
        import re
        clean_name = re.sub(r'\s+(LLC|INC|CORP|CO|LTD|COMPANY)\s*$', '', contractor_name)
        name_parts = clean_name.split()
        
        # Check for exact business name match
        if clean_name in website_text:
            return 1.0
            
        # Check for partial matches
        significant_words = [word for word in name_parts if len(word) > 2 and word not in ['THE', 'AND', 'OR', 'OF']]
        if len(significant_words) == 0:
            return 0.0
            
        matches = sum(1 for word in significant_words if word in website_text)
        match_ratio = matches / len(significant_words)
        
        # High standards for name matching
        if match_ratio >= 0.8:
            return 1.0
        elif match_ratio >= 0.6:
            return 0.6
        elif match_ratio >= 0.4:
            return 0.3
        else:
            return 0.0
    
    def score_contractor_number_match(self, website_text: str, contractor_number: str) -> float:
        """Score contractor license number match (0.0 to 1.0)"""
        if not contractor_number or len(contractor_number) < 6:
            return 0.0
            
        # Look for exact contractor number match
        if contractor_number in website_text:
            return 1.0
            
        # Look for license number patterns (common formats)
        import re
        license_patterns = [
            contractor_number.replace('*', ''),  # Remove asterisks
            contractor_number[:8],  # First 8 characters
            contractor_number[-8:],  # Last 8 characters
        ]
        
        for pattern in license_patterns:
            if len(pattern) >= 6 and pattern in website_text:
                return 1.0
                
        return 0.0
    
    def score_phone_match(self, website_text: str, contractor_phone: str) -> float:
        """Score phone number match (0.0 to 1.0)"""
        if not contractor_phone or len(contractor_phone) < 10:
            return 0.0
            
        # Clean phone number
        clean_phone = ''.join(char for char in contractor_phone if char.isdigit())
        if len(clean_phone) != 10:
            return 0.0
            
        # Check various phone formats
        phone_formats = [
            clean_phone,  # 2065551234
            f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}",  # (206) 555-1234
            f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}",  # 206-555-1234
            f"{clean_phone[:3]}.{clean_phone[3:6]}.{clean_phone[6:]}",  # 206.555.1234
            f"{clean_phone[:3]} {clean_phone[3:6]} {clean_phone[6:]}",  # 206 555 1234
        ]
        
        for phone_format in phone_formats:
            if phone_format in website_text:
                return 1.0
                
        return 0.0
    
    def score_address_match(self, website_text: str, contractor_address: str) -> float:
        """Score address match (0.0 to 1.0)"""
        if not contractor_address:
            return 0.0
            
        # Extract address components
        import re
        
        # Look for street number
        street_number_match = re.search(r'^(\d+)', contractor_address.strip())
        if street_number_match:
            street_number = street_number_match.group(1)
            if street_number in website_text:
                return 1.0
                
        # Look for street name (remove numbers and common words)
        street_parts = contractor_address.split()
        street_words = [word for word in street_parts if not word.isdigit() and len(word) > 3 and word not in ['ST', 'AVE', 'RD', 'BLVD', 'LN', 'WAY', 'PL', 'CT']]
        
        if street_words:
            matches = sum(1 for word in street_words if word in website_text)
            if matches > 0:
                return matches / len(street_words)
                
        return 0.0
    
    def calculate_geographic_penalty(self, website_text: str, contractor: Dict[str, Any]) -> float:
        """Calculate geographical validation penalty (-0.20 if no local indicators found)"""
        
        # Washington area codes (Puget Sound region focus - excluding 509 eastern WA)
        wa_area_codes = ['206', '253', '360', '425']
        
        # Check for Washington area codes in various formats
        import re
        area_code_found = False
        for area_code in wa_area_codes:
            # Check multiple phone number formats
            patterns = [
                f'\\({area_code}\\)',      # (206)
                f'{area_code}-',           # 206-
                f'{area_code}\\.', 	       # 206.
                f' {area_code} ',          # space 206 space
                f'{area_code}\\d{{7}}',    # 2065551234 (10-digit)
            ]
            
            for pattern in patterns:
                if re.search(pattern, website_text):
                    area_code_found = True
                    break
            
            if area_code_found:
                break
        
        # Check for Washington cities and local references (Puget Sound region focus)
        washington_indicators = [
            'WASHINGTON', 'WA ', ' WA,', ' WA.', 'WASHINGTON STATE',
            'SEATTLE', 'TACOMA', 'BELLEVUE', 'EVERETT', 'KENT', 'RENTON',
            'FEDERAL WAY', 'KIRKLAND', 'BELLINGHAM', 'KENNEWICK', 'AUBURN',
            'MARYSVILLE', 'LAKEWOOD', 'REDMOND', 'SHORELINE', 'RICHLAND', 'OLYMPIA',
            'LACEY', 'EDMONDS', 'BURIEN', 'BOTHELL', 'LYNNWOOD', 'LONGVIEW',
            'WENATCHEE', 'MOUNT VERNON', 'CENTRALIA', 'ANACORTES', 'UNIVERSITY PLACE', 
            'MUKILTEO', 'TUKWILA', 'BREMERTON', 'CHEHALIS', 'PORT ORCHARD',
            'MAPLE VALLEY', 'OAK HARBOR', 'FERNDALE', 'MOUNTLAKE TERRACE',
            'PUGET SOUND', 'KING COUNTY', 'PIERCE COUNTY', 'SNOHOMISH COUNTY',
            'SERVING SEATTLE', 'SERVING TACOMA', 'SERVING BELLEVUE',
            'SEATTLE AREA', 'TACOMA AREA', 'GREATER SEATTLE',
            'PACIFIC NORTHWEST', 'PNW ', 'NORTHWESTERN', 'WA LICENSE'
        ]
        
        local_reference_found = False
        for indicator in washington_indicators:
            if indicator in website_text:
                local_reference_found = True
                break
        
        # Apply penalty if NEITHER area codes NOR local references found
        if not area_code_found and not local_reference_found:
            return -0.20  # Geographic penalty
        else:
            return 0.0   # No penalty

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
        # Create contractor-specific logger
        contractor_logger = ContractorLogger(
            str(contractor.get('id', 'Unknown')), 
            contractor['business_name']
        )
        
        try:
            # Clear separator for new contractor - log immediately to show progress
            logger.info("=" * 80)
            logger.info(f"🏢 PROCESSING CONTRACTOR #{contractor.get('id', 'Unknown')}")
            logger.info(f"📋 Business: {contractor['business_name']}")
            logger.info(f"📍 Location: {contractor.get('city', 'Unknown')}, {contractor.get('state', 'Unknown')}")
            logger.info(f"📞 Phone: {contractor.get('phone_number', 'None')}")
            logger.info(f"🏗️  License: {contractor.get('contractor_license_type_code_desc', 'Unknown')}")
            logger.info("=" * 80)
            
            # Step 0: Validate location first
            if not self.is_local_contractor(contractor):
                contractor_logger.info(f"⏭️ SKIPPING: Non-local contractor (outside Puget Sound area)")
                contractor_logger.info("=" * 80)
                self.stats['failed'] += 1
                return
            
            # Step 1: Google Search FIRST (accuracy over cost for data quality)
            website_content = None
            validated_website_url = None
            search_results = []
            
            contractor_logger.info("🎯 Using Google Search FIRST for maximum accuracy...")
            contractor_logger.info("💸 Prioritizing data quality over cost savings...")
            self.stats['google_fallback'] += 1
            search_results = await self.search_contractor_online(contractor)
            
            if search_results:
                contractor_logger.info(f"🔍 Searching through {len(search_results)} Google results for valid website...")
                
                # Look for legitimate website URLs (filtered)
                for i, result in enumerate(search_results, 1):
                    url = result.get('link', '')
                    contractor_logger.info(f"   📄 Result {i}/{len(search_results)}: {url}")
                    
                    filtered_url = self.filter_website_url(url)
                    if filtered_url:  # This is a legitimate website
                        contractor_logger.info(f"   ✅ ACCEPTED: Legitimate website URL")
                        contractor_logger.info(f"   🕷️ Crawling website: {filtered_url}")
                        crawled_content = await self.crawl_website_content(filtered_url, contractor)
                        
                        # FIRST: Check for industry association before any validation
                        if crawled_content:
                            is_excluded, exclusion_reason = self.is_excluded_website(filtered_url, crawled_content)
                            if is_excluded:
                                contractor_logger.warning(f"   🚫 REJECTED: {exclusion_reason}")
                                contractor_logger.info(f"   🔄 Continuing to search remaining {len(search_results) - i} results...")
                                continue
                        else:
                            contractor_logger.warning(f"   ❌ REJECTED: Failed to crawl website content")
                            contractor_logger.info(f"   🔄 Continuing to search remaining {len(search_results) - i} results...")
                            continue
                        
                        # Validate that this website actually belongs to the contractor with STRICT validation
                        contractor_logger.info(f"   🔍 Validating website belongs to contractor...")
                        if self.validate_website_belongs_to_contractor_strict(crawled_content, contractor):
                            # Calculate comprehensive 5-factor confidence score
                            website_confidence = self.calculate_website_confidence_score(crawled_content, contractor)
                            
                            # Only accept websites with confidence >= 0.4 (at least 2 of 4 practical factors must match at 0.25 each)
                            if website_confidence >= 0.4:
                                website_content = crawled_content
                                validated_website_url = filtered_url
                                # Store the website confidence for later use
                                website_content['website_confidence'] = website_confidence
                                contractor_logger.info(f"   ✅ WEBSITE VALIDATED: Confidence {website_confidence:.2f} - USING THIS WEBSITE")
                                break
                            else:
                                contractor_logger.warning(f"   ❌ REJECTED: Website confidence too low ({website_confidence:.2f} < 0.4)")
                                contractor_logger.info(f"   🔄 Continuing to search remaining {len(search_results) - i} results...")
                        else:
                            contractor_logger.warning(f"   ❌ REJECTED: Website doesn't match contractor (failed validation)")
                            contractor_logger.info(f"   🔄 Continuing to search remaining {len(search_results) - i} results...")
                    else:
                        # Log why this URL was filtered out
                        rejection_reason = self._get_url_rejection_reason(url)
                        contractor_logger.info(f"   ⏭️ SKIPPED: {rejection_reason}")
                
                if not validated_website_url:
                    contractor_logger.warning(f"🚫 SEARCH COMPLETE: No valid website found after checking all {len(search_results)} Google results")
                else:
                    contractor_logger.info(f"🎯 SEARCH COMPLETE: Found and validated website: {validated_website_url}")
            else:
                contractor_logger.warning("🚫 No Google search results found")
            
            # Step 2: ONLY try free enrichment if Google Search completely failed
            if not validated_website_url:
                contractor_logger.info("🔄 Google Search found no valid websites, trying free enrichment as last resort...")
                
                free_website = await self.search_free_enrichment(contractor)
                if free_website:
                    # Filter and validate free enrichment result with EXTRA STRICT validation
                    filtered_url = self.filter_website_url(free_website)
                    if filtered_url:
                        contractor_logger.info(f"🎯 Free enrichment provided legitimate website: {filtered_url}")
                        crawled_content = await self.crawl_website_content(filtered_url, contractor)
                        
                        # FIRST: Check for industry association before validation
                        if crawled_content:
                            is_excluded, exclusion_reason = self.is_excluded_website(filtered_url, crawled_content)
                            if is_excluded:
                                contractor_logger.warning(f"🚫 Free enrichment website excluded: {exclusion_reason} - {filtered_url}")
                                contractor_logger.warning("🚫 Both Google Search and free enrichment failed to find valid website")
                                contractor_logger.info("❌ No validated website found - skipping AI evaluation as requested")
                                contractor_logger.info("✅ CONTRACTOR PROCESSING COMPLETE")
                                contractor_logger.info("=" * 80)
                                return
                        
                        # EXTRA STRICT validation for domain guessed results
                        if crawled_content and self.validate_website_belongs_to_contractor_extra_strict(crawled_content, contractor):
                            website_content = crawled_content
                            validated_website_url = filtered_url
                            contractor_logger.info(f"✅ Free enrichment website validated with EXTRA STRICT validation: {filtered_url}")
                            contractor_logger.info("💰 Cost savings: Used free methods after Google Search failed!")
                            self.stats['clearbit_success'] += 1
                            # Create mock search result for consistency
                            search_results = [{'link': filtered_url, 'title': f"{contractor['business_name']} - Free Enrichment", 'snippet': 'Found via free enrichment (last resort)'}]
                        else:
                            contractor_logger.warning(f"❌ Free enrichment website rejected - doesn't match contractor (EXTRA STRICT): {filtered_url}")
                    else:
                        contractor_logger.info(f"⏭️ Free enrichment website skipped (directory/listing): {free_website}")
                
                if not validated_website_url:
                    contractor_logger.warning("🚫 Both Google Search and free enrichment failed to find valid website")
            
            # Step 3: AI analysis ONLY if we have a validated website
            if validated_website_url and website_content:
                contractor_logger.info("✅ Found validated website - proceeding with AI analysis")
                analysis = await self.analyze_with_ai(contractor, search_results or [], website_content)
                # Update analysis to use validated website URL
                analysis['website'] = validated_website_url
                await self.update_contractor_results(contractor, analysis, search_results or [], website_content)
            else:
                # No valid website found - skip AI evaluation as requested
                contractor_logger.info("❌ No validated website found - skipping AI evaluation as requested")
                analysis = {
                    'category': 'Unknown',
                    'confidence': 0.0,
                    'verified': False,
                    'is_residential': None,
                    'website': None,
                    'description': 'No validated website found - could not categorize',
                    'services': [],
                    'skipped_reason': 'No website found'
                }
                await self.update_contractor_results(contractor, analysis, search_results or [], None)
            
            # Completion separator
            contractor_logger.info("✅ CONTRACTOR PROCESSING COMPLETE")
            contractor_logger.info("=" * 80)
            
        except Exception as e:
            contractor_logger.error(f"❌ ERROR processing contractor {contractor['business_name']}: {e}")
            contractor_logger.info("=" * 80)
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
        
        # Print batch completion summary
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
        
        logger.info("🎯" + "=" * 78)
        logger.info(f"📊 BATCH COMPLETE - Progress Summary:")
        logger.info(f"   • Total processed: {self.stats['processed']}")
        logger.info(f"   • Auto-approved: {self.stats['auto_approved']}")
        logger.info(f"   • Manual review: {self.stats['manual_review']}")
        logger.info(f"   • Failed/Skipped: {self.stats['failed']}")
        logger.info(f"   • Processing rate: {rate:.2f} contractors/sec")
        logger.info(f"💰 API Usage: {self.stats['clearbit_success']} Clearbit (free), {self.stats['google_fallback']} Google (paid)")
        logger.info("🎯" + "=" * 78)
    
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