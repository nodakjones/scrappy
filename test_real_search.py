#!/usr/bin/env python3
"""
Test script to run a real Google search for A PLUS HANDYMAN
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService

async def test_real_search():
    """Test real Google search for A PLUS HANDYMAN"""
    
    service = ContractorService()
    
    business_name = "A PLUS HANDYMAN"
    city = "MOUNT VERNON"
    state = "WA"
    
    print("🔍 TESTING REAL GOOGLE SEARCH FOR A PLUS HANDYMAN")
    print("=" * 60)
    print(f"Business Name: {business_name}")
    print(f"City: {city}")
    print(f"State: {state}")
    
    # Generate search queries
    queries = service._generate_search_queries(business_name, city, state)
    print(f"\n📋 Generated Queries:")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    
    # Test the first query
    if queries:
        query = queries[0]
        print(f"\n🔍 Testing Query: '{query}'")
        
        # Run the search
        search_results = await service.search_google_api(query, "web")
        
        if search_results and 'items' in search_results:
            print(f"\n📊 Search Results ({len(search_results['items'])} items):")
            
            for i, item in enumerate(search_results['items'][:5], 1):  # Show first 5 results
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                
                print(f"\n  Result {i}:")
                print(f"    Title: {title}")
                print(f"    Snippet: {snippet}")
                print(f"    Link: {link}")
                
                # Calculate confidence for this result
                confidence = service._calculate_search_confidence(item, business_name, city, state)
                print(f"    Confidence: {confidence}")
                
                # Test individual components
                title_lower = title.lower()
                snippet_lower = snippet.lower()
                link_lower = link.lower()
                business_name_lower = business_name.lower()
                
                print(f"    Business name in title: '{business_name_lower}' in '{title_lower}' = {business_name_lower in title_lower}")
                print(f"    Business name in snippet: '{business_name_lower}' in '{snippet_lower}' = {business_name_lower in snippet_lower}")
                print(f"    Business name in URL: '{business_name_lower}' in '{link_lower}' = {business_name_lower in link_lower}")
                
                # Test partial matches
                business_words = business_name_lower.split()
                print(f"    Business words: {business_words}")
                for word in business_words:
                    if word in title_lower:
                        print(f"      '{word}' found in title")
                    if word in snippet_lower:
                        print(f"      '{word}' found in snippet")
                    if word in link_lower:
                        print(f"      '{word}' found in URL")
        else:
            print("❌ No search results returned")
    else:
        print("❌ No queries generated")

if __name__ == "__main__":
    asyncio.run(test_real_search()) 