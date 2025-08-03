#!/usr/bin/env python3
"""
Debug script to replicate our Google search API process step by step.
Tests the search process for "guardian roofing auburn wa"
"""

import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.services.contractor_service import ContractorService

class GoogleSearchDebugger:
    def __init__(self):
        self.service = ContractorService()
        self.google_api_key = getattr(config, 'GOOGLE_API_KEY', None)
        self.google_cse_id = getattr(config, 'GOOGLE_CSE_ID', None)
        
    def print_step(self, step_num: int, title: str, content: str = ""):
        """Print a formatted step header"""
        print(f"\n{'='*60}")
        print(f"STEP {step_num}: {title}")
        print(f"{'='*60}")
        if content:
            print(content)
    
    def print_substep(self, title: str, content: str = ""):
        """Print a formatted substep"""
        print(f"\n--- {title} ---")
        if content:
            print(content)
    
    def _generate_simple_business_name(self, business_name: str) -> str:
        """Replicate the simple business name generation"""
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
        """Replicate the search query generation"""
        simple_name = self._generate_simple_business_name(business_name)
        
        queries = [
            f'{business_name} {city} {state}',             # 1. Full business name with city/state
            f'{simple_name} {city} {state}',               # 2. Simple business name with city/state
            f'{simple_name} {state}',                      # 3. Simple business name with state only
            f'{business_name} {city}',                     # 4. Full business name with city only
            f'{simple_name} {city}'                        # 5. Simple business name with city only
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries
    
    def _calculate_search_confidence(self, search_item: Dict[str, Any], business_name: str, city: str, state: str) -> float:
        """Replicate the confidence calculation"""
        title = search_item.get('title', '').lower()
        snippet = search_item.get('snippet', '').lower()
        url = search_item.get('link', '').lower()
        
        business_name_lower = business_name.lower()
        simple_name = self._generate_simple_business_name(business_name).lower()
        city_lower = city.lower()
        state_lower = state.lower()
        
        confidence = 0.0
        
        print(f"    Business name: '{business_name}'")
        print(f"    Simple name: '{simple_name}'")
        print(f"    City: '{city}'")
        print(f"    State: '{state}'")
        print(f"    URL: {url}")
        print(f"    Title: {title[:100]}...")
        print(f"    Snippet: {snippet[:100]}...")
        
        # Business name match (highest weight) - try exact match first, then simple name
        if business_name_lower in title:
            confidence += 0.4
            print(f"    ✅ Business name found in title (+0.4)")
        elif simple_name in title:
            confidence += 0.35  # Slightly lower for simple name match
            print(f"    ✅ Simple name found in title (+0.35)")
        elif business_name_lower in snippet:
            confidence += 0.3
            print(f"    ✅ Business name found in snippet (+0.3)")
        elif simple_name in snippet:
            confidence += 0.25  # Slightly lower for simple name match
            print(f"    ✅ Simple name found in snippet (+0.25)")
        elif business_name_lower in url:
            confidence += 0.2
            print(f"    ✅ Business name found in URL (+0.2)")
        elif simple_name in url:
            confidence += 0.15  # Slightly lower for simple name match
            print(f"    ✅ Simple name found in URL (+0.15)")
        else:
            print(f"    ❌ No business name match found")
        
        # Location match
        if city_lower in title or city_lower in snippet:
            confidence += 0.2
            print(f"    ✅ City '{city_lower}' found (+0.2)")
        else:
            print(f"    ❌ City '{city_lower}' not found")
            
        if state_lower in title or state_lower in snippet:
            confidence += 0.1
            print(f"    ✅ State '{state_lower}' found (+0.1)")
        else:
            print(f"    ❌ State '{state_lower}' not found")
        
        # Domain quality check
        if self.service._is_valid_website(url):
            confidence += 0.1
            print(f"    ✅ Domain is valid (+0.1)")
        else:
            print(f"    ❌ Domain is invalid")
        
        # Contractor-related keywords
        contractor_keywords = ['contractor', 'construction', 'plumbing', 'electrical', 'hvac', 'roofing', 'insulation', 'mold', 'attic']
        keyword_found = False
        for keyword in contractor_keywords:
            if keyword in title or keyword in snippet:
                confidence += 0.1
                print(f"    ✅ Contractor keyword '{keyword}' found (+0.1)")
                keyword_found = True
                break
        
        if not keyword_found:
            print(f"    ❌ No contractor keywords found")
        
        final_confidence = min(confidence, 0.95)  # Cap at 0.95
        print(f"    📊 Final confidence: {final_confidence:.3f}")
        
        return final_confidence
    
    async def debug_search_process(self, business_name: str, city: str, state: str):
        """Debug the entire search process step by step"""
        
        self.print_step(1, "INITIAL SETUP")
        print(f"Business Name: {business_name}")
        print(f"City: {city}")
        print(f"State: {state}")
        print(f"Google API Key: {'✅ Configured' if self.google_api_key else '❌ Not configured'}")
        print(f"Google CSE ID: {'✅ Configured' if self.google_cse_id else '❌ Not configured'}")
        
        if not self.google_api_key or not self.google_cse_id:
            print("❌ Cannot proceed - Google API not configured")
            return
        
        self.print_step(2, "SIMPLE BUSINESS NAME GENERATION")
        simple_name = self._generate_simple_business_name(business_name)
        print(f"Original: '{business_name}'")
        print(f"Simple:   '{simple_name}'")
        print(f"Changed:  {'Yes' if business_name != simple_name else 'No'}")
        
        self.print_step(3, "SEARCH QUERY GENERATION")
        queries = self._generate_search_queries(business_name, city, state)
        print(f"Generated {len(queries)} unique queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        self.print_step(4, "GOOGLE API SEARCHES")
        
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(queries, 1):
                self.print_substep(f"Query #{i}: {query}")
                
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cse_id,
                    'q': query,
                    'num': 10
                }
                
                try:
                    async with session.get(url, params=params) as response:
                        print(f"    API Response Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # Show API response info
                            search_info = data.get('searchInformation', {})
                            total_results = search_info.get('totalResults', 'Unknown')
                            print(f"    Total Results Available: {total_results}")
                            
                            if 'items' in data and len(data['items']) > 0:
                                print(f"    Items Returned: {len(data['items'])}")
                                
                                # Analyze each result
                                for j, item in enumerate(data['items'], 1):
                                    self.print_substep(f"Result #{j}")
                                    
                                    website_url = item.get('link', '')
                                    title = item.get('title', '')
                                    snippet = item.get('snippet', '')
                                    
                                    print(f"        URL: {website_url}")
                                    print(f"        Title: {title}")
                                    print(f"        Snippet: {snippet[:150]}...")
                                    
                                    # Check domain validity
                                    domain_valid = self.service._is_valid_website(website_url)
                                    print(f"        Domain Valid: {domain_valid}")
                                    
                                    if domain_valid:
                                        # Calculate confidence
                                        confidence = self._calculate_search_confidence(
                                            item, business_name, city, state
                                        )
                                        
                                        if confidence >= 0.25:
                                            print(f"        🎯 HIGH CONFIDENCE MATCH: {confidence:.3f}")
                                        else:
                                            print(f"        ❌ Low confidence: {confidence:.3f}")
                                    else:
                                        print(f"        ❌ Domain excluded")
                                    
                                    print()  # Empty line for readability
                            else:
                                print("    ❌ No search results returned")
                        else:
                            error_text = await response.text()
                            print(f"    ❌ API Error: {error_text}")
                            
                except Exception as e:
                    print(f"    ❌ Request failed: {e}")
                
                # Add delay between queries
                await asyncio.sleep(1)
        
        self.print_step(5, "SUMMARY")
        print("Search process completed. Check the results above to understand:")
        print("1. Which queries were generated")
        print("2. What results Google API returned")
        print("3. How confidence scores were calculated")
        print("4. Why certain results were accepted/rejected")

async def main():
    """Main function to run the debug process"""
    debugger = GoogleSearchDebugger()
    
    # Test with "guardian roofing auburn wa"
    business_name = "guardian roofing"
    city = "auburn"
    state = "wa"
    
    print("🔍 GOOGLE SEARCH API DEBUG PROCESS")
    print("Testing: guardian roofing auburn wa")
    
    await debugger.debug_search_process(business_name, city, state)

if __name__ == "__main__":
    asyncio.run(main()) 