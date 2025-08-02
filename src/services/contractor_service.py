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
            business_name_variations = [business_name, self._generate_simple_business_name(business_name)]
            
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
            
            # Use simplified query for local pack
            queries = self._generate_search_queries(business_name, city, state)
            query = f'{queries[0]} local business'  # Use first query with "local business" modifier
            
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
            
            # Generate simplified search queries
            query_strategies = self._generate_search_queries(business_name, city, state)
            
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
                                    confidence_str = f"{confidence:.3f}" if confidence is not None else "None"
                                    domain_reason = f"Confidence: {confidence_str} | Threshold: 0.25"
                                    
                                    if confidence >= 0.25:  # Lower threshold for website discovery (will be validated later)
                                        # Log consolidated results for this query before returning
                                        if logger_ctx:
                                            logger_ctx.log_search_results([{
                                                'title': f'Google Search: "{query}"',
                                                'url': f'Status: {response.status} | Items: {len(data["items"])} | Response Keys: {list(data.keys())}',
                                                'snippet': f'Found {len(all_search_results)} results with analysis. High confidence match found: {website_url} (confidence: {confidence_str})'
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
    
    def _generate_simple_business_name(self, business_name: str) -> str:
        """Generate simple business name by removing INC, LLC, etc."""
        simple_name = business_name
        
        # Common business designations to remove
        designations = [
            ' INC', ' LLC', ' CORP', ' CORPORATION', ' CO', ' COMPANY',
            ' LP', ' LLP', ' LPA', ' PA', ' PLLC', ' PC', ' PLLC',
            ' LTD', ' LIMITED', ' GROUP', ' ENTERPRISES', ' ENTERPRISE',
            ' SERVICES', ' SERVICE', ' BUILDING'
        ]
        
        # Remove each designation
        for designation in designations:
            if designation in simple_name.upper():
                simple_name = simple_name.upper().replace(designation, '').strip()
                break  # Only remove the first one found
        
        return simple_name
    
    def _generate_search_queries(self, business_name: str, city: str, state: str) -> List[str]:
        """Generate search queries without quotes for better matching"""
        simple_name = self._generate_simple_business_name(business_name)
        
        queries = [
            f'{business_name} {city} {state}',             # 1. Full business name with city/state
            f'{simple_name} {city} {state}',               # 2. Simple business name with city/state
            f'{simple_name} {state}',                      # 3. Simple business name with state only
            f'{business_name} {city}',                     # 4. Full business name with city only
            f'{simple_name} {city}'                        # 5. Simple business name with city only
        ]
        
        return queries
    
    def _calculate_search_confidence(self, search_item: Dict[str, Any], business_name: str, city: str, state: str) -> float:
        """Calculate confidence score for a search result with improved business name matching"""
        title = search_item.get('title', '').lower()
        snippet = search_item.get('snippet', '').lower()
        url = search_item.get('link', '').lower()
        
        business_name_lower = business_name.lower()
        simple_name = self._generate_simple_business_name(business_name).lower()
        city_lower = city.lower()
        state_lower = state.lower()
        
        confidence = 0.0
        
        # Business name match (highest weight) - try exact match first, then simple name
        if business_name_lower in title:
            confidence += 0.4
        elif simple_name in title:
            confidence += 0.35  # Slightly lower for simple name match
        elif business_name_lower in snippet:
            confidence += 0.3
        elif simple_name in snippet:
            confidence += 0.25  # Slightly lower for simple name match
        elif business_name_lower in url:
            confidence += 0.2
        elif simple_name in url:
            confidence += 0.15  # Slightly lower for simple name match
        
        # Location match
        if city_lower in title or city_lower in snippet:
            confidence += 0.2
        if state_lower in title or state_lower in snippet:
            confidence += 0.1
        
        # Domain quality check
        if self._is_valid_website(url):
            confidence += 0.1
        
        # Contractor-related keywords
        contractor_keywords = ['contractor', 'construction', 'plumbing', 'electrical', 'hvac', 'roofing', 'insulation', 'mold', 'attic']
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
            
            # Use simplified query for knowledge panel
            queries = self._generate_search_queries(business_name, city, state)
            query = queries[0]  # Use the first query (full business name with city/state)
            
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
                                
                                if confidence >= 0.25:  # Lower threshold for website discovery (will be validated later)
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
        return await self._crawl_single_page(url)
    
    async def _get_raw_html(self, url: str) -> Optional[str]:
        """Get raw HTML content for navigation extraction"""
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
                        return await response.text()
                    else:
                        logger.warning(f"Raw HTML fetch failed for {url}: status {response.status}")
                        
            except Exception as ssl_error:
                logger.warning(f"SSL raw HTML fetch failed for {url}, trying without SSL: {ssl_error}")
                
                # Try without SSL context
                try:
                    async with session.get(url, timeout=10, ssl=False) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.warning(f"Raw HTML fetch failed for {url}: status {response.status}")
                            
                except Exception as no_ssl_error:
                    logger.error(f"Raw HTML fetch error for {url}: {no_ssl_error}")
                    
        except Exception as e:
            logger.error(f"Raw HTML fetch error for {url}: {e}")
            
        return None
    
    async def _crawl_single_page(self, url: str) -> Optional[str]:
        """Crawl a single page with improved SSL handling"""
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
                        
                        # Extract meaningful content
                        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                        
                        return content if content else None
                    else:
                        logger.warning(f"Website crawl failed for {url}: status {response.status}")
                        
            except Exception as ssl_error:
                logger.warning(f"SSL crawl failed for {url}, trying without SSL: {ssl_error}")
                
                # Try without SSL context
                try:
                    async with session.get(url, timeout=10, ssl=False) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Extract meaningful content
                            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                            content = re.sub(r'<[^>]+>', '', content)
                            content = re.sub(r'\s+', ' ', content).strip()
                            
                            return content if content else None
                        else:
                            logger.warning(f"Website crawl failed for {url}: status {response.status}")
                            
                except Exception as no_ssl_error:
                    logger.error(f"Website crawl error for {url}: {no_ssl_error}")
                    
        except Exception as e:
            logger.error(f"Website crawl error for {url}: {e}")
            
        return None
    
    async def crawl_website_comprehensive(self, url: str) -> Optional[Dict[str, Any]]:
        """Comprehensive website crawling - multiple pages with navigation analysis"""
        try:
            session = await self._get_session()
            
            # First, get the raw HTML for navigation extraction
            raw_html = await self._get_raw_html(url)
            if not raw_html:
                return None
            
            # Extract navigation links from raw HTML
            nav_links = self._extract_navigation_links(url, raw_html)
            
            # Now crawl the main page for content
            main_content = await self._crawl_single_page(url)
            if not main_content:
                return None
            
            # Crawl additional pages (limit to 5 pages to avoid overwhelming)
            additional_content = []
            crawled_pages = 0
            max_pages = 5
            
            for link in nav_links[:max_pages]:
                try:
                    page_content = await self._crawl_single_page(link)
                    if page_content:
                        additional_content.append(page_content)
                        crawled_pages += 1
                        
                        # Add delay to be respectful
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Failed to crawl additional page {link}: {e}")
                    continue
            
            # Combine all content
            all_content = main_content
            if additional_content:
                all_content += "\n\n" + "\n\n".join(additional_content)
            
            return {
                'main_content': main_content,
                'additional_content': additional_content,
                'combined_content': all_content,
                'pages_crawled': 1 + crawled_pages,
                'nav_links_found': len(nav_links)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive website crawl error for {url}: {e}")
            return None
    
    def _extract_navigation_links(self, base_url: str, html_content: str) -> List[str]:
        """Extract navigation links from HTML content with improved selectors"""
        try:
            from bs4 import BeautifulSoup
            import urllib.parse
            import re
            
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Comprehensive navigation selectors for modern websites
            nav_selectors = [
                # Standard navigation
                'nav a', 'header a', '.nav a', '.navigation a', 
                '.menu a', '.navbar a', '#nav a', '#navigation a',
                # Modern frameworks
                '.navbar-nav a', '.nav-menu a', '.main-menu a', '.primary-menu a',
                '.site-nav a', '.main-nav a', '.top-nav a', '.header-nav a',
                # Common class patterns
                '[class*="nav"] a', '[class*="menu"] a', '[class*="header"] a',
                # Specific modern patterns
                '.navbar-nav .nav-link', '.nav-menu .menu-item a', '.main-menu .menu-item a',
                # Generic link extraction (fallback)
                'a[href]'
            ]
            
            for selector in nav_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href')
                        if href and href.strip():
                            # Convert relative URLs to absolute
                            absolute_url = urllib.parse.urljoin(base_url, href)
                            
                            # Only include links to the same domain
                            if urllib.parse.urlparse(absolute_url).netloc == urllib.parse.urlparse(base_url).netloc:
                                # Filter out common non-content pages and patterns
                                exclude_patterns = [
                                    '/admin', '/login', '/cart', '/checkout', '/search',
                                    '/privacy', '/terms', '/sitemap', '/feed', '/rss',
                                    '/wp-admin', '/wp-login', '/cgi-bin', '/api',
                                    'mailto:', 'tel:', 'javascript:', '#'
                                ]
                                
                                # Check if URL contains excluded patterns
                                if not any(pattern in absolute_url.lower() for pattern in exclude_patterns):
                                    # Focus on content-rich pages with specific keywords
                                    content_keywords = [
                                        'service', 'offering', 'about', 'contact', 
                                        'capabilities', 'capability', 'location'
                                    ]
                                    
                                    # Check if URL path or link text contains content keywords
                                    url_lower = absolute_url.lower()
                                    link_text = element.get_text(strip=True).lower()
                                    
                                    # Look for keywords in URL path or link text
                                    has_content_keyword = any(keyword in url_lower for keyword in content_keywords) or \
                                                        any(keyword in link_text for keyword in content_keywords)
                                    
                                    if has_content_keyword:
                                        links.append(absolute_url)
                                    elif len(links) < 2:  # Limit non-content pages to 2
                                        links.append(absolute_url)
                                        
                except Exception as selector_error:
                    logger.debug(f"Selector '{selector}' failed: {selector_error}")
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            # Log what we found
            logger.info(f"Extracted {len(unique_links)} navigation links from {base_url}")
            for i, link in enumerate(unique_links[:5]):  # Log first 5
                logger.debug(f"  Link {i+1}: {link}")
            
            return unique_links[:10]  # Limit to 10 links
            
        except Exception as e:
            logger.warning(f"Failed to extract navigation links from {base_url}: {e}")
            return []
    
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
                crawled_data = await self.crawl_website_comprehensive(clearbit_url)
                
                if crawled_data and crawled_data['combined_content']:
                    # Store the website for validation, but don't assign high confidence yet
                    validated_website = {
                        'url': clearbit_url,
                        'content': crawled_data['combined_content'],
                        'main_content': crawled_data['main_content'],
                        'additional_content': crawled_data['additional_content'],
                        'pages_crawled': crawled_data['pages_crawled'],
                        'nav_links_found': crawled_data['nav_links_found'],
                        'source': 'clearbit_api',
                        'confidence': 0.0  # Will be calculated after validation
                    }
                    best_result = validated_website
                    best_confidence = 0.0  # Start with 0, will be updated after validation
                    logger_ctx.log_website_selection(clearbit_url, 0.0)
                    
                    # Log comprehensive crawl results
                    logger_ctx.log_search_results([{
                        'title': f'Comprehensive Crawl Results - {clearbit_domain}',
                        'url': clearbit_url,
                        'snippet': f'Crawled {crawled_data["pages_crawled"]} pages, found {crawled_data["nav_links_found"]} nav links, content length: {len(crawled_data["combined_content"])} chars',
                        'source': 'clearbit_api'
                    }])
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
                    crawled_data = await self.crawl_website_comprehensive(google_api_result['url'])
                    if crawled_data and crawled_data['combined_content']:
                        google_api_result['content'] = crawled_data['combined_content']
                        google_api_result['main_content'] = crawled_data['main_content']
                        google_api_result['additional_content'] = crawled_data['additional_content']
                        google_api_result['pages_crawled'] = crawled_data['pages_crawled']
                        google_api_result['nav_links_found'] = crawled_data['nav_links_found']
                        
                        if google_api_result['confidence'] > best_confidence:
                            best_result = google_api_result
                            best_confidence = google_api_result['confidence']
                            logger_ctx.log_website_selection(google_api_result['url'], google_api_result['confidence'])
                        
                        # Log comprehensive crawl results
                        logger_ctx.log_search_results([{
                            'title': f'Comprehensive Crawl Results - Google API',
                            'url': google_api_result['url'],
                            'snippet': f'Crawled {crawled_data["pages_crawled"]} pages, found {crawled_data["nav_links_found"]} nav links, content length: {len(crawled_data["combined_content"])} chars',
                            'source': 'google_api'
                        }])
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
        """AI-powered business categorization and analysis using OpenAI"""
        try:
            if not contractor.website_url or contractor.website_status != 'found':
                return 0.5  # Base confidence for no website
            
            # Get website content from data sources
            content = contractor.data_sources.get('crawled_content', '') if contractor.data_sources else ''
            
            if not content:
                # Try to crawl the website again with comprehensive crawling
                crawled_data = await self.crawl_website_comprehensive(contractor.website_url)
                if crawled_data and crawled_data['combined_content'] and contractor.data_sources:
                    contractor.data_sources['crawled_content'] = crawled_data['combined_content']
                    content = crawled_data['combined_content']
            
            if not content:
                return 0.5
            
            # Check if OpenAI API key is configured
            openai_api_key = getattr(config, 'OPENAI_API_KEY', None)
            if not openai_api_key:
                logger.warning("OpenAI API key not configured, using fallback keyword analysis")
                return self._fallback_content_analysis(content, contractor.business_name, logger_ctx)
            
            # Prepare content for AI analysis (limit to 10K chars for cost efficiency)
            analysis_content = content[:10000]  # Limit to 10K chars for cost-effective analysis
            
            # Log the content being sent to OpenAI
            logger_ctx.log_ai_call("openai_gpt4_mini", {
                "business_name": contractor.business_name,
                "content_length": len(analysis_content),
                "content_preview": analysis_content[:500] + "..." if len(analysis_content) > 500 else analysis_content,
                "estimated_tokens": len(analysis_content) // 4,  # Rough estimate: 1 token ≈ 4 characters
                "estimated_cost": (len(analysis_content) // 4) * 0.0000005  # GPT-4o-mini input cost
            })
            
            # OpenAI GPT-4o-mini analysis
            import openai
            client = openai.OpenAI(api_key=openai_api_key)
            
            # Get categories from config
            try:
                from src.categories_config import ALL_CATEGORIES, PRIORITY_CATEGORIES
                categories_list = ALL_CATEGORIES
                priority_categories = PRIORITY_CATEGORIES
            except ImportError:
                # Fallback if categories config doesn't exist
                categories_list = [
                    "Plumbing", "Electrical", "HVAC", "Roofing", "General Contractor",
                    "Heating and Cooling", "Flooring", "Pools and Spas", "Security Systems",
                    "Window/Door", "Bathroom/Kitchen Remodel", "Storage & Closets",
                    "Decks & Patios", "Fence", "Fireplace", "Sprinklers", "Blinds",
                    "Awning/Patio/Carport", "Media Systems", "Exterior Solutions"
                ]
                priority_categories = [
                    "Heating and Cooling", "Plumbing", "Electrical", "HVAC"
                ]
            
            prompt = f"""
Analyze this contractor business website and provide categorization:

Business: {contractor.business_name}
Location: {contractor.city}, {contractor.state}
License: {contractor.contractor_license_number}

Available Categories: {', '.join(categories_list)}

Priority Categories (high-value residential services): {', '.join(priority_categories)}

Website Content:
{analysis_content}

Please provide a JSON response with:
1. "category" - Specific contractor category from the available categories list above
2. "confidence" - Confidence score 0-1 based on content analysis
3. "residential_focus" - true if primarily serves homeowners, false if commercial, null if unclear
4. "services_offered" - Array of main services mentioned
5. "business_legitimacy" - true if appears to be a legitimate business
6. "reasoning" - Brief explanation of categorization decision

IMPORTANT: 
- Choose category from the provided list, prioritizing priority categories when appropriate
- Base category on actual services mentioned, not business name
- Look for specific service keywords in the content
- Provide a lower confidence score based on if this website looks to be related to a business directory, a business listing site, a business/industry/trade association, a software/service product listing contractor customers, and other non-contractor related websites.
- If content suggests a focus on home services, mark residential_focus as true. Look for words or phrases similar to: "residential" or "homeowners" or "home services" or "home improvement"
- If content suggests a focus on non residential services, mark residential_focus as false. Look for words or phrases similar to: "commercial" or "business services" or "industrial"

Respond with valid JSON only.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.2
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Log AI response
            logger_ctx.log_ai_call("openai_gpt4_mini", {
                "business_name": contractor.business_name,
                "input_content": analysis_content[:500] + "..." if len(analysis_content) > 500 else analysis_content,
                "ai_response": ai_response
            })
            
            try:
                import json
                import re
                
                # Clean the response - remove markdown code blocks if present
                cleaned_response = ai_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                ai_data = json.loads(cleaned_response)
                
                category = ai_data.get('category', 'General Contractor')
                confidence = float(ai_data.get('confidence', 0.5))
                residential_focus = ai_data.get('residential_focus')
                services_offered = ai_data.get('services_offered', [])
                business_legitimacy = ai_data.get('business_legitimacy', True)
                reasoning = ai_data.get('reasoning', '')
                
                # Store AI analysis results
                if contractor.data_sources:
                    contractor.data_sources['ai_analysis'] = {
                        'category': category,
                        'confidence': confidence,
                        'residential_focus': residential_focus,
                        'services_offered': services_offered,
                        'business_legitimacy': business_legitimacy,
                        'reasoning': reasoning
                    }
                
                logger_ctx.log_classification(category, confidence)
                
                return confidence
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response for {contractor.business_name}: {ai_response}")
                return self._fallback_content_analysis(content, contractor.business_name, logger_ctx)
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed for {contractor.business_name}: {e}")
            return self._fallback_content_analysis(content, contractor.business_name, logger_ctx)
    
    def _fallback_content_analysis(self, content: str, business_name: str, logger_ctx) -> float:
        """Fallback keyword-based analysis when OpenAI is not available"""
        content_lower = content.lower()
        business_name_lower = business_name.lower()
        
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
        if business_name_lower in content_lower:
            confidence += 0.1
        
        # Determine category based on content analysis
        category = self._determine_category_from_content(content.lower(), business_name.lower())
        
        logger_ctx.log_classification(category, confidence)
        
        return confidence
    
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
        
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Parse principal name format: "Last, First Middle" -> "First Last"
        # Handle various formats: "Last, First", "Last, First M", "First Last", etc.
        principal_parts = principal_name.split(',')
        if len(principal_parts) >= 2:
            # Format: "Last, First Middle" -> "First Last"
            last_name = principal_parts[0].strip()
            first_part = principal_parts[1].strip()
            first_parts = first_part.split()
            first_name = first_parts[0] if first_parts else ""
            
            # Create reformatted name: "First Last"
            reformatted_name = f"{first_name} {last_name}".strip()
            
            # Clean and convert to lowercase
            clean_reformatted = re.sub(r'[^\w\s]', '', reformatted_name).strip().lower()
            
            # Check for reformatted name match
            if clean_reformatted in content_lower:
                return True
            
            # Also check individual words from reformatted name
            reformatted_words = clean_reformatted.split()
            for word in reformatted_words:
                if len(word) > 2:  # Only match words longer than 2 characters
                    pattern = r'\b' + re.escape(word) + r'\b'
                    if re.search(pattern, content_lower):
                        return True
        else:
            # Original format (no comma) - try as is
            clean_principal = re.sub(r'[^\w\s]', '', principal_name).strip().lower()
            
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
                    # Use the search confidence as the primary website confidence
                    website_confidence = website_discovery_confidence
                    
                    # Validate the discovered website using 5-factor system for additional validation
                    crawled_content = contractor.data_sources.get('crawled_content', '')
                    if crawled_content:  # Only validate if we have content to validate
                        validation_results = await self._comprehensive_website_validation(contractor, crawled_content, logger_ctx)
                        validation_confidence = self._calculate_validation_confidence(validation_results)
                        
                        # Log validation results
                        logger_ctx.log_search_results([{
                            'title': '5-Factor Validation Results',
                            'url': contractor.website_url,
                            'snippet': f'Search Confidence: {f"{website_confidence:.3f}"} | Business Name Match: {validation_results["business_name_match"]} | License Match: {validation_results["license_match"]} | Phone Match: {validation_results["phone_match"]} | Address Match: {validation_results["address_match"]} | Principal Match: {validation_results["principal_name_match"]} | Validation Confidence: {f"{validation_confidence:.3f}" if validation_confidence is not None else "None"}',
                            'source': 'validation_system'
                        }])
                        
                        # Only proceed with AI classification if website validation meets minimum threshold
                        if website_confidence >= 0.25:  # Lowered threshold for website acceptance
                            # Step 3: AI Classification (only for validated websites)
                            try:
                                classification_confidence = await self.enhanced_content_analysis(contractor, logger_ctx)
                            except Exception as e:
                                logger.error(f"AI classification failed for {contractor.business_name}: {e}")
                                classification_confidence = 0.0
                        else:
                            logger_ctx.log_search_results([{
                                'title': 'Website Validation Failed',
                                'url': contractor.website_url,
                                'snippet': f'Website confidence {website_confidence:.3f} below minimum threshold of 0.4 - skipping AI analysis',
                                'source': 'validation_system'
                            }])
                            classification_confidence = 0.0
                    else:
                        # No content to validate - set confidence to 0
                        website_confidence = 0.0
                        logger_ctx.log_search_results([{
                            'title': '5-Factor Validation Results',
                            'url': contractor.website_url,
                            'snippet': 'No content available for validation - website crawl failed',
                            'source': 'validation_system'
                        }])
                
                # Calculate overall confidence - use AI classification confidence directly
                if website_confidence >= 0.25:  # Lowered website validation threshold
                    # Use AI classification confidence as the overall confidence
                    overall_confidence = classification_confidence
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
