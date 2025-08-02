#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.database.models import Contractor

async def debug_navigation(contractor_name):
    """Debug navigation link extraction for a specific contractor"""
    await db_pool.initialize()
    
    # Get the contractor
    async with db_pool.pool.acquire() as conn:
        result = await conn.fetchrow('''
            SELECT * FROM contractors 
            WHERE business_name ILIKE $1
            LIMIT 1
        ''', f'%{contractor_name}%')
        
        if not result:
            print(f"No contractor found matching: {contractor_name}")
            return
        
        contractor = Contractor(**dict(result))
        print(f"Debugging navigation for: {contractor.business_name}")
        print(f"Website URL: {contractor.website_url}")
        print("=" * 60)
        
        # Get the raw HTML first
        service = ContractorService()
        try:
            if contractor.website_url:
                # Get raw HTML content
                session = await service._get_session()
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                try:
                    async with session.get(contractor.website_url, timeout=10, ssl=ssl_context) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            print(f"✅ Successfully fetched HTML content")
                            print(f"HTML Length: {len(html_content)} characters")
                            
                            # Test navigation extraction
                            from bs4 import BeautifulSoup
                            import urllib.parse
                            
                            soup = BeautifulSoup(html_content, 'html.parser')
                            
                            # Test different selectors
                            selectors_to_test = [
                                'nav a', 'header a', '.nav a', '.navigation a', 
                                '.menu a', '.navbar a', '#nav a', '#navigation a',
                                '.navbar-nav a', '.nav-menu a', '.main-menu a', '.primary-menu a',
                                '.site-nav a', '.main-nav a', '.top-nav a', '.header-nav a',
                                '[class*="nav"] a', '[class*="menu"] a', '[class*="header"] a',
                                '.navbar-nav .nav-link', '.nav-menu .menu-item a', '.main-menu .menu-item a',
                                'a[href]'
                            ]
                            
                            print(f"\n🔍 TESTING SELECTORS:")
                            for selector in selectors_to_test:
                                elements = soup.select(selector)
                                if elements:
                                    print(f"  ✅ '{selector}': {len(elements)} elements found")
                                    for i, element in enumerate(elements[:3]):  # Show first 3
                                        href = element.get('href', '')
                                        text = element.get_text(strip=True)[:50]
                                        print(f"    {i+1}. href='{href}' text='{text}'")
                                else:
                                    print(f"  ❌ '{selector}': No elements found")
                            
                            # Test the actual extraction method
                            print(f"\n🎯 TESTING EXTRACTION METHOD:")
                            links = service._extract_navigation_links(contractor.website_url, html_content)
                            print(f"  Extracted {len(links)} links:")
                            for i, link in enumerate(links):
                                print(f"    {i+1}. {link}")
                            
                        else:
                            print(f"❌ Failed to fetch HTML: status {response.status}")
                            
                except Exception as e:
                    print(f"❌ Error fetching HTML: {e}")
                    
        except Exception as e:
            print(f"Error debugging navigation: {e}")
            import traceback
            traceback.print_exc()
        
        await service.close()
    
    await db_pool.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Debug navigation link extraction')
    parser.add_argument('--contractor', '-c', type=str, default='425 CONSTRUCTION', help='Contractor name to analyze')
    args = parser.parse_args()
    
    asyncio.run(debug_navigation(args.contractor)) 