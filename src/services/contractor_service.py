"""
Contractor processing service with improved website discovery
"""
import asyncio
import logging
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re

from ..database.connection import db_pool
from ..database.models import Contractor
from ..config import config, is_valid_website_domain, is_local_business_validation
from ..utils.logging_utils import contractor_logger

logger = logging.getLogger(__name__)


class ContractorService:
    """Service with real website discovery using Clearbit API and Google Search API"""
    
    def __init__(self):
        self.batch_size = config.BATCH_SIZE
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def try_clearbit_enrichment(self, business_name: str) -> Optional[str]:
        """Try to find company domain using Clearbit API with multiple name variations"""
        try:
            session = await self._get_session()
            
            # Generate business name variations for Clearbit
            business_name_variations = self._generate_business_name_variations(business_name)
            
            # Try each variation
            for name_variation in business_name_variations:
                # Clean business name for search - keep special characters for better matching
                clean_name = name_variation.strip()
                
                # Properly URL encode the query parameter
                from urllib.parse import quote
                encoded_query = quote(clean_name)
                
                # Clearbit API endpoint
                url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={encoded_query}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            # Get the first (most relevant) result
                            company = data[0]
                            domain = company.get('domain')
                            
                            if domain:
                                return domain
                        
                    elif response.status != 404:  # 404 is expected for no results
                        logger.warning(f"Clearbit API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Clearbit API error for {business_name}: {e}")
            
        return None
    
    async def search_google_local_pack(self, business_name: str, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Search Google Local Pack using Custom Search API with local business focus"""
        try:
            # Check if Google API key is configured
            google_api_key = getattr(config, 'GOOGLE_API_KEY', None)
            google_cse_id = getattr(config, 'GOOGLE_CSE_ID', None)
            
            if not google_api_key or not google_cse_id:
                return None
            
            session = await self._get_session()
            
            # Query specifically for local business results
            query = f'"{business_name}" {city} {state} local business'
            
            # Google Custom Search API endpoint with local business focus
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': google_cse_id,
                'q': query,
                'num': 5  # Fewer results for local pack
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'items' in data and len(data['items']) > 0:
                        # Look for local business type results
                        for item in data['items']:
                            website_url = item.get('link')
                            
                            if website_url and self._is_valid_website(website_url):
                                confidence = self._calculate_search_confidence(
                                    item, business_name, city, state
                                )
                                
                                if confidence >= 0.7:  # Good threshold for local pack
                                    return {
                                        'url': website_url,
                                        'source': 'google_local_pack',
                                        'confidence': confidence,
                                        'title': item.get('title', ''),
                                        'snippet': item.get('snippet', '')
                                    }
                    
                elif response.status == 429:
                    logger.warning(f"Google Local Pack search returned status 429")
                else:
                    logger.warning(f"Google Local Pack search returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Google Local Pack search error for {business_name}: {e}")
            
        return None
    
    async def search_google_api(self, business_name: str, city: str, state: str, logger_ctx=None) -> Optional[Dict[str, Any]]:
        """Search using Google Custom Search API with multiple query strategies"""
        try:
            # Check if Google API key is configured
            google_api_key = getattr(config, 'GOOGLE_API_KEY', None)
            google_cse_id = getattr(config, 'GOOGLE_CSE_ID', None)
            
            if not google_api_key or not google_cse_id:
                return None
            
            session = await self._get_session()
            
            # Generate business name variations
            business_name_variations = self._generate_business_name_variations(business_name)
            
            # Multiple query strategies in order of preference (without quotes for broader matching)
            query_strategies = []
            for name_variation in business_name_variations:
                query_strategies.extend([
                    f'{name_variation} {city} {state}',
                    f'{name_variation} {state} contractor'
                ])
            
            for query in query_strategies:
                # Google Custom Search API endpoint
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': google_api_key,
                    'cx': google_cse_id,
                    'q': query,
                    'num': 10  # Get 10 results
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'items' in data and len(data['items']) > 0:
                            # Collect all results for logging
                            all_search_results = []
                            
                            # Process all results to find the best match
                            for i, item in enumerate(data['items'], 1):
                                website_url = item.get('link')
                                title = item.get('title', '')
                                snippet = item.get('snippet', '')
                                
                                # Calculate confidence and domain validity
                                confidence = 0.0
                                domain_valid = "NO"
                                domain_reason = "No URL found"
                                
                                if website_url and self._is_valid_website(website_url):
                                    # Calculate confidence based on match quality
                                    confidence = self._calculate_search_confidence(
                                        item, business_name, city, state
                                    )
                                    domain_valid = "YES"
                                    domain_reason = f"Confidence: {confidence:.3f} | Threshold: 0.7"
                                    
                                    if confidence >= 0.7:  # Only return high-confidence matches
                                        # Log consolidated results for this query before returning
                                        if logger_ctx:
                                            logger_ctx.log_search_results([{
                                                'title': f'Google Search: "{query}"',
                                                'url': f'Status: {response.status} | Items: {len(data["items"])} | Response Keys: {list(data.keys())}',
                                                'snippet': f'Found {len(all_search_results)} results with analysis. High confidence match found: {website_url} (confidence: {confidence:.3f})'
                                            }])
                                        
                                        return {
                                            'url': website_url,
                                            'source': 'google_api',
                                            'confidence': confidence,
                                            'title': item.get('title', ''),
                                            'snippet': item.get('snippet', ''),
                                            'query_used': query
                                        }
                                elif website_url:
                                    domain_reason = "Excluded domain or invalid URL"
                                
                                # Add consolidated search result with analysis
                                all_search_results.append({
                                    'title': f'Result #{i}',
                                    'url': website_url or 'N/A',
                                    'snippet': f'Title: {title[:100]}... | Domain valid: {domain_valid} | {domain_reason}'
                                })
                            
                            # Log consolidated results for this query
                            if logger_ctx:
                                logger_ctx.log_search_results([{
                                    'title': f'Google Search: "{query}"',
                                    'url': f'Status: {response.status} | Items: {len(data["items"])} | Response Keys: {list(data.keys())}',
                                    'snippet': f'Found {len(all_search_results)} results. No high confidence matches found.'
                                }])
                        else:
                            # No items in response
                            if logger_ctx:
                                logger_ctx.log_search_results([{
                                    'title': f'Google Search: "{query}"',
                                    'url': f'Status: {response.status} | Items: 0 | Response Keys: {list(data.keys())}',
                                    'snippet': 'No search results found.'
                                }])
                    
                    elif response.status == 429:
                        logger.warning(f"Google API rate limited (429) for query: {query}")
                        # Add delay and continue to next query strategy
                        await asyncio.sleep(2)
                        continue
                    else:
                        logger.warning(f"Google API returned status {response.status} for query: {query}")
                        continue
                
                # Add delay between queries to avoid rate limiting
                await asyncio.sleep(1)
            
            return None
                    
        except Exception as e:
            logger.error(f"Google API search error for {business_name}: {e}")
            return None
    
    def _generate_business_name_variations(self, business_name: str) -> List[str]:
        """Generate variations of business name by removing common business designations"""
        variations = [business_name]  # Start with original name
        
        # Common business designations to remove (but keep CONSTRUCTION, ELECTRIC, etc.)
        designations = [
            ' INC', ' LLC', ' CORP', ' CORPORATION', ' CO', ' COMPANY',
            ' LP', ' LLP', ' LPA', ' PA', ' PLLC', ' PC', ' PLLC',
            ' LTD', ' LIMITED', ' GROUP', ' ENTERPRISES', ' ENTERPRISE',
            ' SERVICES', ' SERVICE', ' BUILDING'
            # Removed ' CONTRACTING', ' CONTRACTORS', ' CONTRACTOR' to preserve CONSTRUCTION
        ]
        
        # Remove each designation and add to variations
        for designation in designations:
            if designation in business_name.upper():
                variation = business_name.upper().replace(designation, '').strip()
                if variation and variation not in [v.upper() for v in variations]:
                    variations.append(variation)
        
        # Also try with just the first few words (common pattern)
        words = business_name.split()
        if len(words) > 2:
            # Try first 2-3 words
            for i in range(2, min(4, len(words) + 1)):
                variation = ' '.join(words[:i])
                if variation not in variations:
                    variations.append(variation)
        
        return variations
    
    def _calculate_search_confidence(self, search_item: Dict[str, Any], business_name: str, city: str, state: str) -> float:
        """Calculate confidence score for a search result"""
        title = search_item.get('title', '').lower()
        snippet = search_item.get('snippet', '').lower()
        url = search_item.get('link', '').lower()
        
        business_name_lower = business_name.lower()
        city_lower = city.lower()
        state_lower = state.lower()
        
        confidence = 0.0
        
        # Business name match (highest weight)
        if business_name_lower in title:
            confidence += 0.4
        elif business_name_lower in snippet:
            confidence += 0.3
        elif business_name_lower in url:
            confidence += 0.2
        
        # Location match
        if city_lower in title or city_lower in snippet:
            confidence += 0.2
        if state_lower in title or state_lower in snippet:
            confidence += 0.1
        
        # Domain quality check
        if self._is_valid_website(url):
            confidence += 0.1
        
        # Contractor-related keywords
        contractor_keywords = ['contractor', 'construction', 'plumbing', 'electrical', 'hvac', 'roofing']
        for keyword in contractor_keywords:
            if keyword in title or keyword in snippet:
                confidence += 0.1
                break
        
        return min(confidence, 0.95)  # Cap at 0.95
    
    async def search_google_knowledge_panel(self, business_name: str, city: str, state: str) -> Optional[Dict[str, Any]]:
        """Search Google Knowledge Panel using Custom Search API with specific parameters"""
        try:
            # Check if Google API key is configured
            google_api_key = getattr(config, 'GOOGLE_API_KEY', None)
            google_cse_id = getattr(config, 'GOOGLE_CSE_ID', None)
            
            if not google_api_key or not google_cse_id:
                return None
            
            session = await self._get_session()
            
            # Query specifically for knowledge panel type results
            query = f'"{business_name}" {city} {state}'
            
            # Google Custom Search API endpoint with knowledge panel focus
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': google_cse_id,
                'q': query,
                'num': 5  # Fewer results for knowledge panel
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'items' in data and len(data['items']) > 0:
                        # Look for knowledge panel type results (usually first result)
                        for item in data['items']:
                            website_url = item.get('link')
                            
                            if website_url and self._is_valid_website(website_url):
                                confidence = self._calculate_search_confidence(
                                    item, business_name, city, state
                                )
                                
                                if confidence >= 0.75:  # Higher threshold for knowledge panel
                                    return {
                                        'url': website_url,
                                        'source': 'google_knowledge_panel',
                                        'confidence': confidence,
                                        'title': item.get('title', ''),
                                        'snippet': item.get('snippet', '')
                                    }
                    
                elif response.status == 429:
                    logger.warning(f"Google Knowledge Panel search returned status 429")
                else:
                    logger.warning(f"Google Knowledge Panel search returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Google Knowledge Panel search error for {business_name}: {e}")
            
        return None
    
    async def crawl_website(self, url: str) -> Optional[str]:
        """Crawl website content for validation with improved SSL handling"""
        try:
            session = await self._get_session()
            
            # Create SSL context that's more permissive for certificate issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Try with SSL context first
            try:
                async with session.get(url, timeout=10, ssl=ssl_context) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Extract meaningful content (first 1000 characters)
                        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                        
                        return content[:1000] if content else None
                    else:
                        logger.warning(f"Website crawl failed for {url}: status {response.status}")
                        
            except Exception as ssl_error:
                logger.warning(f"SSL crawl failed for {url}, trying without SSL: {ssl_error}")
                
                # Try without SSL context
                try:
                    async with session.get(url, timeout=10, ssl=False) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Extract meaningful content (first 1000 characters)
                            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                            content = re.sub(r'<[^>]+>', '', content)
                            content = re.sub(r'\s+', ' ', content).strip()
                            
                            return content[:1000] if content else None
                        else:
                            logger.warning(f"Website crawl failed for {url}: status {response.status}")
                            
                except Exception as no_ssl_error:
                    logger.error(f"Website crawl error for {url}: {no_ssl_error}")
                    
        except Exception as e:
            logger.error(f"Website crawl error for {url}: {e}")
            
        return None
    
    def _is_valid_website(self, url: str) -> bool:
        """Check if URL is a valid business website (not directory/social)"""
        if not url:
            return False
        
        # Use the centralized domain validation function
        return is_valid_website_domain(url)
    
    async def enhanced_website_discovery(self, contractor: Contractor, logger_ctx) -> float:
        """Website discovery using multiple sources"""
        try:
            logger_ctx.log_search_query(f"Discovery for: {contractor.business_name}")
            
            business_name = contractor.business_name
            city = contractor.city or ""
            state = contractor.state or ""
            
            best_result = None
            best_confidence = 0.0
            
            # 1. Try Clearbit API (free tier)
            logger_ctx.log_ai_call("clearbit_api", {
                "business_name": business_name,
                "api_endpoint": "https://autocomplete.clearbit.com/v1/companies/suggest"
            })
            
            clearbit_domain = await self.try_clearbit_enrichment(business_name)
            if clearbit_domain:
                clearbit_url = f"https://{clearbit_domain}"
                crawled_content = await self.crawl_website(clearbit_url)
                
                if crawled_content:
                    validated_website = {
                        'url': clearbit_url,
                        'content': crawled_content,
                        'source': 'clearbit_api',
                        'confidence': 0.90
                    }
                    best_result = validated_website
                    best_confidence = 0.90
                    logger_ctx.log_website_selection(clearbit_url, 0.90)
                else:
                    logger_ctx.log_search_results([{
                        'title': 'Clearbit domain found but crawl failed',
                        'url': clearbit_url,
                        'snippet': f'Domain {clearbit_domain} found but website crawl failed',
                        'source': 'clearbit_api'
                    }])
            else:
                logger_ctx.log_search_results([{
                    'title': 'Clearbit API - No results',
                    'url': 'N/A',
                    'snippet': f'Clearbit API returned no results for {business_name}',
                    'source': 'clearbit_api'
                }])
            
            # 2. Try Google Custom Search API (10 results, multiple query strategies)
            if not best_result or best_confidence < 0.90:
                logger_ctx.log_ai_call("google_api", {
                    "business_name": business_name,
                    "city": city,
                    "state": state,
                    "api_endpoint": "Google Custom Search API"
                })
                
                google_api_result = await self.search_google_api(business_name, city, state, logger_ctx)
                if google_api_result:
                    crawled_content = await self.crawl_website(google_api_result['url'])
                    if crawled_content:
                        google_api_result['content'] = crawled_content
                        if google_api_result['confidence'] > best_confidence:
                            best_result = google_api_result
                            best_confidence = google_api_result['confidence']
                            logger_ctx.log_website_selection(google_api_result['url'], google_api_result['confidence'])
                    else:
                        logger_ctx.log_search_results([{
                            'title': 'Google API result found but crawl failed',
                            'url': google_api_result['url'],
                            'snippet': f'Google API found website but crawl failed',
                            'source': 'google_api'
                        }])
                else:
                    logger_ctx.log_search_results([{
                        'title': 'Google API - No results',
                        'url': 'N/A',
                        'snippet': f'Google API returned no results for {business_name}',
                        'source': 'google_api'
                    }])
            
            # 3. Try Google Knowledge Panel
            if not best_result or best_confidence < 0.88:
                logger_ctx.log_ai_call("google_knowledge_panel", {
                    "business_name": business_name,
                    "city": city,
                    "state": state,
                    "search_url": "Google Knowledge Panel"
                })
                
                knowledge_panel_result = await self.search_google_knowledge_panel(business_name, city, state)
                if knowledge_panel_result:
                    crawled_content = await self.crawl_website(knowledge_panel_result['url'])
                    if crawled_content:
                        knowledge_panel_result['content'] = crawled_content
                        if knowledge_panel_result['confidence'] > best_confidence:
                            best_result = knowledge_panel_result
                            best_confidence = knowledge_panel_result['confidence']
                            logger_ctx.log_website_selection(knowledge_panel_result['url'], knowledge_panel_result['confidence'])
                    else:
                        logger_ctx.log_search_results([{
                            'title': 'Google Knowledge Panel result found but crawl failed',
                            'url': knowledge_panel_result['url'],
                            'snippet': f'Google Knowledge Panel found website but crawl failed',
                            'source': 'google_knowledge_panel'
                        }])
                else:
                    logger_ctx.log_search_results([{
                        'title': 'Google Knowledge Panel - No results',
                        'url': 'N/A',
                        'snippet': f'No website found in Google Knowledge Panel for {business_name}',
                        'source': 'google_knowledge_panel'
                    }])
            
            # 4. Try Google Local Pack
            if not best_result or best_confidence < 0.85:
                logger_ctx.log_ai_call("google_local_pack", {
                    "business_name": business_name,
                    "city": city,
                    "state": state,
                    "search_url": "Google Local Pack"
                })
                
                local_pack_result = await self.search_google_local_pack(business_name, city, state)
                if local_pack_result:
                    crawled_content = await self.crawl_website(local_pack_result['url'])
                    if crawled_content:
                        local_pack_result['content'] = crawled_content
                        if local_pack_result['confidence'] > best_confidence:
                            best_result = local_pack_result
                            best_confidence = local_pack_result['confidence']
                            logger_ctx.log_website_selection(local_pack_result['url'], local_pack_result['confidence'])
                    else:
                        logger_ctx.log_search_results([{
                            'title': 'Google Local Pack result found but crawl failed',
                            'url': local_pack_result['url'],
                            'snippet': f'Google Local Pack found website but crawl failed',
                            'source': 'google_local_pack'
                        }])
                else:
                    logger_ctx.log_search_results([{
                        'title': 'Google Local Pack - No results',
                        'url': 'N/A',
                        'snippet': f'No website found in Google Local Pack for {business_name}',
                        'source': 'google_local_pack'
                    }])
            
            # Update contractor with discovered website
            if best_result:
                contractor.website_url = best_result['url']
                contractor.website_status = 'found'
                contractor.data_sources = {
                    'discovery_method': best_result['source'],
                    'search_confidence': best_confidence,
                    'discovery': True,
                    'crawled_content': best_result.get('content', '')[:500]  # Store first 500 chars
                }
                logger_ctx.log_website_selection(best_result['url'], best_confidence)
                logger.info(f"Discovery found website: {best_result['url']} via {best_result['source']} (confidence: {best_confidence:.2f})")
            else:
                contractor.website_status = 'not_found'
                contractor.data_sources = {
                    'discovery_method': 'none',
                    'search_confidence': 0.0,
                    'discovery': True
                }
                # Log the discovery process summary
                logger_ctx.log_search_results([{
                    'title': 'No website found',
                    'url': 'N/A',
                    'snippet': f'All discovery methods attempted for {business_name}',
                    'source': 'discovery_summary'
                }])
            
            return best_confidence
            
        except Exception as e:
            logger.error(f"Website discovery failed for {contractor.business_name}: {e}")
            return 0.0
    
    async def enhanced_content_analysis(self, contractor: Contractor, logger_ctx) -> float:
        """AI-powered business categorization and analysis"""
        try:
            if not contractor.website_url or contractor.website_status != 'found':
                return 0.5  # Base confidence for no website
            
            # Get website content from data sources
            content = contractor.data_sources.get('crawled_content', '') if contractor.data_sources else ''
            
            if not content:
                # Try to crawl the website again
                content = await self.crawl_website(contractor.website_url)
                if content and contractor.data_sources:
                    contractor.data_sources['crawled_content'] = content[:1000]  # Store more content for analysis
            
            if not content:
                return 0.5
            
            # AI Analysis for Business Categorization
            # This analyzes: residential vs commercial focus, service categories, business legitimacy
            
            # Simple keyword-based analysis (placeholder for AI)
            content_lower = content.lower()
            business_name_lower = contractor.business_name.lower()
            
            confidence = 0.0
            
            # 1. Residential Focus Analysis (40% weight)
            residential_keywords = [
                'residential', 'home', 'house', 'family', 'residential services',
                'home improvement', 'home repair', 'home maintenance', 'homeowner',
                'residential contractor', 'home contractor', 'residential services'
            ]
            
            residential_score = 0.0
            for keyword in residential_keywords:
                if keyword in content_lower:
                    residential_score += 0.1
            residential_score = min(residential_score, 1.0)
            confidence += residential_score * 0.4
            
            # 2. Contractor Service Analysis (30% weight)
            contractor_services = [
                'plumbing', 'electrical', 'hvac', 'heating', 'cooling', 'roofing',
                'painting', 'carpentry', 'landscaping', 'concrete', 'foundation',
                'remodeling', 'renovation', 'repair', 'installation', 'maintenance',
                'construction', 'contractor', 'contracting', 'home services'
            ]
            
            service_score = 0.0
            for service in contractor_services:
                if service in content_lower:
                    service_score += 0.05
            service_score = min(service_score, 1.0)
            confidence += service_score * 0.3
            
            # 3. Business Legitimacy Analysis (20% weight)
            legitimacy_keywords = [
                'licensed', 'insured', 'bonded', 'certified', 'professional',
                'experience', 'years', 'established', 'trusted', 'reliable',
                'quality', 'warranty', 'guarantee', 'satisfaction', 'customer'
            ]
            
            legitimacy_score = 0.0
            for keyword in legitimacy_keywords:
                if keyword in content_lower:
                    legitimacy_score += 0.05
            legitimacy_score = min(legitimacy_score, 1.0)
            confidence += legitimacy_score * 0.2
            
            # 4. Business Name Relevance (10% weight)
            # Check if business name appears in content
            if business_name_lower in content_lower:
                confidence += 0.1
            
            # Determine category based on content analysis
            category = self._determine_category_from_content(content.lower(), contractor.business_name.lower())
            
            logger_ctx.log_classification(category, confidence)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Content analysis failed for {contractor.business_name}: {e}")
            return 0.5
    
    async def _comprehensive_website_validation(self, contractor: Contractor, content: str, logger_ctx) -> Dict[str, Any]:
        """Perform comprehensive website validation checks"""
        validation_results = {
            'business_name_match': False,
            'keyword_business_name_match': False,
            'license_match': False,
            'phone_match': False,
            'address_match': False,
            'principal_name_match': False,
            'details': {
                'business_name': '',
                'business_name_found': False,
                'license': '',
                'license_found': False,
                'phone': '',
                'phone_found': False,
                'address': '',
                'address_found': False,
                'principal_name': '',
                'principal_name_found': False
            }
        }
        
        content_lower = content.lower()
        business_name_lower = contractor.business_name.lower()
        
        # 1. Business Name Matching (Factor 1)
        business_name_match = self._advanced_business_name_matching(contractor.business_name, content)
        keyword_business_name_match = self._keyword_business_name_matching(contractor.business_name, content)
        
        validation_results['business_name_match'] = business_name_match
        validation_results['keyword_business_name_match'] = keyword_business_name_match
        validation_results['details']['business_name'] = contractor.business_name
        validation_results['details']['business_name_found'] = business_name_match or keyword_business_name_match
        
        # 2. License Number Matching (Factor 2)
        if contractor.contractor_license_number:
            license_match = self._license_matching(contractor.contractor_license_number, content)
            validation_results['license_match'] = license_match
            validation_results['details']['license'] = contractor.contractor_license_number
            validation_results['details']['license_found'] = license_match
        else:
            validation_results['license_match'] = False
            validation_results['details']['license'] = ''
            validation_results['details']['license_found'] = False
        
        # 3. Phone Number Matching
        validation_results['phone_match'] = self._phone_number_matching(contractor.phone_number, content)
        validation_results['details']['phone'] = contractor.phone_number
        validation_results['details']['phone_found'] = validation_results['phone_match']
        
        # 4. Address Matching (Factor 5)
        validation_results['address_match'] = self._address_matching(contractor.address1, content)
        validation_results['details']['address'] = contractor.address1
        validation_results['details']['address_found'] = validation_results['address_match']
        
        # 5. Principal Name Matching (Factor 4)
        validation_results['principal_name_match'] = self._principal_name_matching(contractor.primary_principal_name, content)
        validation_results['details']['principal_name'] = contractor.primary_principal_name
        validation_results['details']['principal_name_found'] = validation_results['principal_name_match']
        
        # 7. Contractor Keywords Analysis
        contractor_keywords = [
            'plumbing', 'electrical', 'hvac', 'heating', 'cooling', 'air conditioning',
            'roofing', 'construction', 'remodeling', 'renovation', 'contractor',
            'painting', 'flooring', 'landscaping', 'handyman', 'maintenance',
            'repair', 'installation', 'service', 'professional', 'licensed'
        ]
        validation_results['contractor_keywords'] = sum(1 for keyword in contractor_keywords if keyword in content_lower)
        
        return validation_results
    
    def _advanced_business_name_matching(self, business_name: str, content: str) -> float:
        """Advanced business name matching with fuzzy logic"""
        # Clean business name
        clean_name = re.sub(r'[^\w\s]', '', business_name).strip()
        words = clean_name.split()
        
        if len(words) <= 1:
            return 1.0 if clean_name in content else 0.0
        
        # Calculate word-by-word match score
        matched_words = 0
        total_words = len(words)
        
        for word in words:
            if len(word) > 2:  # Only consider words longer than 2 characters
                if word in content:
                    matched_words += 1
                else:
                    # Try partial matches for longer words
                    for content_word in content.split():
                        if len(content_word) > 3 and word in content_word:
                            matched_words += 0.5
                            break
        
        return matched_words / total_words if total_words > 0 else 0.0
    
    def _keyword_business_name_matching(self, business_name: str, content: str) -> float:
        """Extract key business name components and match against content"""
        # Extract potential business name components
        business_words = business_name.split()
        
        # Look for business name patterns in content
        # This is a simplified version - could be enhanced with NLP
        business_patterns = [
            r'\b' + re.escape(word) + r'\b' for word in business_words if len(word) > 2
        ]
        
        matches = 0
        total_patterns = len(business_patterns)
        
        for pattern in business_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0.0
    
    def _license_matching(self, license_number: str, content: str) -> bool:
        """Check if contractor license number appears in website content"""
        if not license_number:
            return False
        
        # Clean license number (remove common formatting)
        clean_license = re.sub(r'[^\w]', '', license_number.upper())
        
        # Look for license number in content
        content_upper = content.upper()
        
        # Direct match
        if clean_license in content_upper:
            return True
        
        # Look for license patterns
        license_patterns = [
            r'license[:\s]*' + re.escape(clean_license),
            r'lic[:\s]*' + re.escape(clean_license),
            r'contractor[:\s]*' + re.escape(clean_license)
        ]
        
        for pattern in license_patterns:
            if re.search(pattern, content_upper):
                return True
        
        return False
    
    def _phone_number_matching(self, phone_number: str, content: str) -> bool:
        """Check if contractor phone number appears in website content"""
        if not phone_number:
            return False
        
        # Normalize phone number (remove all non-digits)
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        
        # Must have at least 10 digits for a valid phone number
        if len(clean_phone) < 10:
            return False
        
        # Normalize content (remove all non-digits)
        content_digits = re.sub(r'[^\d]', '', content)
        
        # Look for full normalized phone number in content
        if clean_phone in content_digits:
            return True
        
        # Look for phone patterns with full number
        phone_patterns = [
            r'phone[:\s]*' + re.escape(phone_number),
            r'tel[:\s]*' + re.escape(phone_number),
            r'call[:\s]*' + re.escape(phone_number),
            r'contact[:\s]*' + re.escape(phone_number)
        ]
        
        for pattern in phone_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _address_matching(self, address: str, content: str) -> bool:
        """Check if contractor address appears in website content"""
        if not address:
            return False
        
        # Clean address (remove common formatting)
        clean_address = re.sub(r'[^\w\s,.]', '', address.upper())
        
        # Look for address in content
        content_upper = content.upper()
        
        # Direct match
        if clean_address in content_upper:
            return True
        
        # Look for address patterns
        address_patterns = [
            r'\b' + re.escape(word) + r'\b' for word in clean_address.split() if len(word) > 2
        ]
        
        for pattern in address_patterns:
            if re.search(pattern, content_upper):
                return True
        
        return False
    
    def _principal_name_matching(self, principal_name: str, content: str) -> bool:
        """Check if principal name (e.g., owner, manager) appears in website content"""
        if not principal_name:
            return False
        
        # Clean principal name (remove common formatting and convert to lowercase)
        clean_principal = re.sub(r'[^\w\s]', '', principal_name).strip().lower()
        
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Direct match (case insensitive)
        if clean_principal in content_lower:
            return True
        
        # Split principal name into words and look for individual word matches
        principal_words = clean_principal.split()
        
        # Look for principal name patterns (individual words)
        for word in principal_words:
            if len(word) > 2:  # Only match words longer than 2 characters
                # Look for word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, content_lower):
                    return True
        
        return False
    
    def _calculate_validation_confidence(self, validation_results: Dict[str, Any]) -> float:
        """Calculate confidence score based on 5-factor validation system"""
        confidence = 0.0
        
        # Factor 1: Business Name Match (0.25 points)
        if validation_results['business_name_match']:
            confidence += 0.25
        elif validation_results['keyword_business_name_match']:
            confidence += 0.15  # Partial credit for keyword match
        
        # Factor 2: License Number Match (0.25 points)
        if validation_results['license_match']:
            confidence += 0.25
        
        # Factor 3: Phone Number Match (0.25 points)
        if validation_results['phone_match']:
            confidence += 0.25
        
        # Factor 4: Principal Name Match (0.25 points)
        if validation_results['principal_name_match']:
            confidence += 0.25
        
        # Factor 5: Address Match (0.25 points)
        if validation_results['address_match']:
            confidence += 0.25
        
        return max(confidence, 0.0)  # Ensure non-negative
    
    def _determine_category_from_content(self, content: str, business_name: str) -> str:
        """Determine contractor category from website content"""
        content_lower = content.lower()
        
        # Category keywords mapping
        category_keywords = {
            'Electrical Contractor': ['electrical', 'electrician', 'wiring', 'electrical contractor'],
            'Plumbing Contractor': ['plumbing', 'plumber', 'pipe', 'drain', 'sewer'],
            'HVAC Contractor': ['hvac', 'heating', 'cooling', 'air conditioning', 'furnace', 'ac'],
            'Roofing Contractor': ['roofing', 'roof', 'shingle', 'gutter'],
            'General Contractor': ['construction', 'remodeling', 'renovation', 'general contractor']
        }
        
        # Check for category matches
        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        
        # Default to General Contractor if no specific category found
        return 'General Contractor'
    
    async def process_contractor(self, contractor: Contractor) -> Contractor:
        """Process a single contractor with discovery"""
        with contractor_logger.contractor_processing(contractor.id, contractor.business_name) as logger_ctx:
            try:
                # Update status to processing
                await self.update_contractor_status(contractor.id, 'processing')
                
                # Step 1: Website Discovery (returns confidence score)
                website_discovery_confidence = await self.enhanced_website_discovery(contractor, logger_ctx)
                
                # Step 2: Website Validation (5-factor system) - only if website was found
                website_confidence = 0.0
                classification_confidence = 0.0
                
                if contractor.website_url and contractor.website_status == 'found':
                    # Validate the discovered website using 5-factor system
                    crawled_content = contractor.data_sources.get('crawled_content', '')
                    if crawled_content:  # Only validate if we have content to validate
                        validation_results = await self._comprehensive_website_validation(contractor, crawled_content, logger_ctx)
                        website_confidence = self._calculate_validation_confidence(validation_results)
                        
                        # Log validation results
                        logger_ctx.log_search_results([{
                            'title': '5-Factor Validation Results',
                            'url': contractor.website_url,
                            'snippet': f'Business Name Match: {validation_results["business_name_match"]} | License Match: {validation_results["license_match"]} | Phone Match: {validation_results["phone_match"]} | Address Match: {validation_results["address_match"]} | Principal Match: {validation_results["principal_name_match"]} | Validation Confidence: {website_confidence:.3f} | Website Confidence: {contractor.website_confidence:.3f if contractor.website_confidence is not None else "N/A"}',
                            'source': 'validation_system'
                        }])
                    else:
                        # No content to validate - set confidence to 0
                        website_confidence = 0.0
                        logger_ctx.log_search_results([{
                            'title': '5-Factor Validation Results',
                            'url': contractor.website_url,
                            'snippet': 'No content available for validation - website crawl failed',
                            'source': 'validation_system'
                        }])
                    
                    # Step 3: AI Classification (run if we have a website, regardless of validation score)
                    try:
                        classification_confidence = await self.enhanced_content_analysis(contractor, logger_ctx)
                    except Exception as e:
                        logger.error(f"AI classification failed for {contractor.business_name}: {e}")
                        classification_confidence = 0.0
                
                # Calculate overall confidence using proper formula
                if website_confidence >= 0.4:  # Website validation threshold
                    # Combined confidence: (Website Confidence × 60%) + (AI Confidence × 40%)
                    overall_confidence = (website_confidence * 0.6) + (classification_confidence * 0.4)
                elif website_discovery_confidence > 0.0:
                    # Website was found but validation failed - show actual validation results
                    overall_confidence = website_confidence  # Use actual validation confidence
                    # Still run AI classification for better analysis
                    if contractor.website_url and contractor.website_status == 'found':
                        classification_confidence = await self.enhanced_content_analysis(contractor, logger_ctx)
                else:
                    # No website found
                    overall_confidence = 0.0
                    classification_confidence = 0.0
                
                # Update contractor with results
                contractor.website_confidence = website_confidence  # Always use actual validation confidence
                contractor.classification_confidence = classification_confidence
                contractor.confidence_score = overall_confidence
                
                # Update the log object to reflect the actual validation confidence
                if logger_ctx:
                    task_storage = logger_ctx._get_task_storage()
                    if task_storage and task_storage['contractor_log']:
                        task_storage['contractor_log'].website_confidence = website_confidence
                
                # Status assignment based on confidence thresholds
                if overall_confidence >= 0.8:
                    contractor.processing_status = 'completed'
                    contractor.review_status = 'approved_download'
                elif overall_confidence >= 0.6:
                    contractor.processing_status = 'completed'
                    contractor.review_status = 'pending_review'
                else:
                    contractor.processing_status = 'completed'
                    contractor.review_status = 'rejected'
                
                contractor.is_home_contractor = overall_confidence > 0.5
                contractor.mailer_category = self._determine_category_from_content(
                    contractor.data_sources.get('crawled_content', '').lower() if contractor.data_sources else '',
                    contractor.business_name.lower()
                )
                contractor.last_processed = datetime.utcnow()
                
                # Log final result
                logger_ctx.log_final_result(overall_confidence, contractor.processing_status)
                
                # Save results
                await self.update_contractor(contractor)
                
                return contractor
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing contractor {contractor.business_name}: {error_msg}")
                contractor.processing_status = 'error'
                contractor.error_message = error_msg
                await self.update_contractor(contractor)
                
                # Log error in logging
                logger_ctx.log_final_result(0.0, 'error', error_msg)
                raise
    
    async def update_contractor_status(self, contractor_id: int, status: str):
        """Update contractor processing status"""
        query = """
        UPDATE contractors 
        SET processing_status = $1, updated_at = NOW()
        WHERE id = $2
        """
        await db_pool.execute(query, status, contractor_id)
    
    async def update_contractor(self, contractor: Contractor):
        """Update contractor with processing results"""
        query = """
        UPDATE contractors 
        SET 
            processing_status = $1,
            confidence_score = $2,
            website_confidence = $3,
            classification_confidence = $4,
            is_home_contractor = $5,
            mailer_category = $6,
            website_url = $7,
            website_status = $8,
            data_sources = $9,
            last_processed = $10,
            error_message = $11,
            updated_at = NOW()
        WHERE id = $12
        """
        
        await db_pool.execute(
            query,
            contractor.processing_status,
            contractor.confidence_score,
            contractor.website_confidence,
            contractor.classification_confidence,
            contractor.is_home_contractor,
            contractor.mailer_category,
            contractor.website_url,
            contractor.website_status,
            json.dumps(contractor.data_sources) if contractor.data_sources else None,
            contractor.last_processed,
            contractor.error_message,
            contractor.id
        )
    
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
            
        return contractors
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        query = """
        SELECT 
            processing_status,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence
        FROM contractors 
        GROUP BY processing_status
        """
        
        rows = await db_pool.fetch(query)
        
        stats = {}
        for row in rows:
            status = row['processing_status']
            stats[status] = {
                'count': row['count'],
                'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0
            }
        
        return stats
    
    async def process_batch(self, contractors: List[Contractor]) -> Dict[str, int]:
        """Process a batch of contractors with discovery"""
        
        completed = 0
        errors = 0
        
        # Process contractors sequentially to avoid logging intermixing
        for contractor in contractors:
            try:
                await self.process_contractor(contractor)
                completed += 1
            except Exception as e:
                business_name = contractor.business_name if contractor else 'Unknown'
                logger.error(f"Error processing {business_name}: {e}")
                errors += 1
        
        manual_review = len(contractors) - completed - errors
        
        batch_results = {
            'processed': len(contractors),
            'completed': completed,
            'manual_review': manual_review,
            'errors': errors
        }
        
        return batch_results
    
    async def close(self):
        """Close the service and cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
