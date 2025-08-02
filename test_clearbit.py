#!/usr/bin/env python3
import asyncio
import aiohttp
from urllib.parse import quote

async def test_clearbit():
    async with aiohttp.ClientSession() as session:
        # Test with a business that should definitely have results
        test_names = [
            "Microsoft",
            "Apple",
            "Google",
            "Amazon",
            "3PETE CONSTRUCTION",  # This one worked in our test
            "PETE CONSTRUCTION"    # This one also worked
        ]
        
        for business_name in test_names:
            encoded_query = quote(business_name)
            url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={encoded_query}"
            
            print(f"\nTesting: {business_name}")
            print(f"URL: {url}")
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            print(f"✅ Found {len(data)} results:")
                            for i, company in enumerate(data[:3], 1):  # Show first 3
                                print(f"  {i}. {company.get('name', 'N/A')} - {company.get('domain', 'N/A')}")
                        else:
                            print("❌ No results found")
                    else:
                        print(f"❌ Error status: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_clearbit()) 