#!/usr/bin/env python3
"""
Test Google API Status and Quota
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config

async def test_google_api():
    """Test Google API status"""
    
    print("🔍 TESTING GOOGLE API STATUS")
    print("=" * 40)
    
    # Check configuration
    print(f"API Key configured: {'Yes' if config.GOOGLE_API_KEY else 'No'}")
    print(f"CSE ID configured: {'Yes' if config.GOOGLE_CSE_ID else 'No'}")
    
    if not config.GOOGLE_API_KEY or not config.GOOGLE_CSE_ID:
        print("❌ Google API not configured!")
        return
    
    # Test API call
    import aiohttp
    
    session = aiohttp.ClientSession()
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': config.GOOGLE_API_KEY,
            'cx': config.GOOGLE_CSE_ID,
            'q': 'test query'
        }
        
        async with session.get(url, params=params) as response:
            print(f"Status Code: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print("✅ API is working!")
                print(f"Results found: {len(data.get('items', []))}")
            elif response.status == 429:
                print("❌ Rate limited (429) - Daily quota likely exceeded")
            elif response.status == 403:
                print("❌ Forbidden (403) - API key or CSE ID issue")
            else:
                text = await response.text()
                print(f"❌ Error: {response.status} - {text[:200]}")
                
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_google_api()) 