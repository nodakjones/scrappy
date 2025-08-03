#!/usr/bin/env python3
"""
Debug specific cases where the system made incorrect matches.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService

async def debug_specific_cases():
    """Debug specific incorrect matches"""
    print("🔍 DEBUGGING SPECIFIC INCORRECT MATCHES")
    print("=" * 60)
    
    # Initialize database and service
    await db_pool.initialize()
    service = ContractorService()
    
    # Cases to investigate
    cases = [
        {
            "business_name": "509 HEATING & COOLING",
            "expected_issue": "thermallheating.com doesn't match company name and not local"
        },
        {
            "business_name": "509 SERVICES",
            "expected_issue": "nevinfloorcompany.com doesn't match company name and not local"
        },
        {
            "business_name": "57 Wood Floors",
            "expected_issue": "straitfloors.com not correct company"
        },
        {
            "business_name": "509 CUSTOM PAINTING & DRYWALL",
            "expected_issue": "brietspainting.com not correct company"
        },
        {
            "business_name": "509 QUALITY PROPERTY MAINT LLC",
            "expected_issue": "jagelectricwa.com not correct company"
        }
    ]
    
    try:
        for case in cases:
            print(f"\n{'='*60}")
            print(f"🔍 INVESTIGATING: {case['business_name']}")
            print(f"Expected Issue: {case['expected_issue']}")
            print(f"{'='*60}")
            
            # Get contractor data
            async with db_pool.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    SELECT business_name, website_url, mailer_category, confidence_score, 
                           city, state, review_status, is_home_contractor, last_processed
                    FROM contractors 
                    WHERE business_name ILIKE $1
                    AND processing_status = 'completed'
                    ORDER BY last_processed DESC
                    LIMIT 1
                ''', f'%{case["business_name"]}%')
            
            if result:
                business_name = result[0]
                website_url = result[1] or "None"
                category = result[2] or "None"
                confidence = result[3] or 0.0
                location = f"{result[4]}, {result[5]}" if result[4] and result[5] else "Unknown"
                review_status = result[6] or "unknown"
                is_home = "Yes" if result[7] else "No"
                processed_time = result[8] or "Unknown"
                
                print(f"📋 CONTRACTOR DATA:")
                print(f"  Business Name: {business_name}")
                print(f"  Location: {location}")
                print(f"  Website: {website_url}")
                print(f"  Category: {category}")
                print(f"  Confidence: {confidence}")
                print(f"  Home Contractor: {is_home}")
                print(f"  Review Status: {review_status}")
                print(f"  Processed: {processed_time}")
                
                # Analyze the website URL
                if website_url and website_url != "None":
                    print(f"\n🔍 WEBSITE ANALYSIS:")
                    print(f"  URL: {website_url}")
                    
                    # Check if domain matches business name
                    domain = website_url.lower().replace('https://', '').replace('http://', '').split('/')[0]
                    business_name_lower = business_name.lower()
                    
                    print(f"  Domain: {domain}")
                    print(f"  Business Name: {business_name_lower}")
                    
                    # Check for business name in domain
                    if business_name_lower.replace(' ', '') in domain:
                        print(f"  ✅ Business name found in domain")
                    elif any(word in domain for word in business_name_lower.split()):
                        print(f"  ⚠️ Partial business name match in domain")
                    else:
                        print(f"  ❌ No business name match in domain")
                    
                    # Check for location indicators
                    location_indicators = ['wa', 'washington', 'seattle', 'spokane', 'tacoma', 'bellevue', 'everett', 'kent', 'auburn', 'federal way', 'yakima', 'vancouver', 'olympia', 'bellingham', 'kennewick', 'puyallup', 'lynnwood', 'renton', 'spokane valley', 'bremerton', 'pasco', 'marysville', 'lakewood', 'redmond', 'sammamish', 'kirkland', 'bothell', 'mercer island', 'woodinville', 'edmonds', 'mount vernon', 'bainbridge island', 'gig harbor', 'port orchard', 'silverdale', 'poulsbo', 'kingston', 'port townsend', 'sequim', 'port angeles', 'forks', 'aberdeen', 'hoquiam', 'centralia', 'chehalis', 'olympia', 'lacey', 'tumwater', 'shelton', 'bremerton', 'port orchard', 'silverdale', 'poulsbo', 'kingston', 'port townsend', 'sequim', 'port angeles', 'forks', 'aberdeen', 'hoquiam', 'centralia', 'chehalis', 'olympia', 'lacey', 'tumwater', 'shelton']
                    
                    domain_has_location = any(indicator in domain for indicator in location_indicators)
                    print(f"  Location in domain: {'✅ Yes' if domain_has_location else '❌ No'}")
                    
                    # Check if it's a directory or association site
                    directory_indicators = ['association', 'directory', 'listing', 'find', 'search', 'pros', 'contractors', 'bizprofile', 'bizapedia', 'yellowpages', 'whitepages', 'superpages', 'manta', 'zoominfo', 'linkedin', 'facebook', 'twitter', 'instagram', 'youtube', 'vimeo', 'flickr', 'pinterest', 'tumblr', 'reddit', 'quora', 'stackoverflow', 'github', 'gitlab', 'bitbucket', 'sourceforge', 'codeplex', 'google', 'bing', 'yahoo', 'duckduckgo', 'baidu', 'yandex', 'naver', 'seznam', 'qwant', 'startpage', 'searx', 'metager', 'swisscows', 'mojeek', 'gibiru', 'oscobo', 'searchlock', 'searchprivacy', 'searx', 'metager', 'swisscows', 'mojeek', 'gibiru', 'oscobo', 'searchlock', 'searchprivacy']
                    
                    is_directory = any(indicator in domain for indicator in directory_indicators)
                    print(f"  Directory/Association: {'❌ Yes' if is_directory else '✅ No'}")
                    
                    print(f"\n🎯 ANALYSIS:")
                    if not domain_has_location and not any(word in domain for word in business_name_lower.split()):
                        print(f"  ❌ FAILED: Domain doesn't match business name and not local")
                    elif is_directory:
                        print(f"  ❌ FAILED: Directory/association site")
                    elif not domain_has_location:
                        print(f"  ❌ FAILED: Not a local business")
                    else:
                        print(f"  ✅ PASSED: Appears to be legitimate")
                
                else:
                    print(f"❌ No website found")
                
            else:
                print(f"❌ Contractor not found in database")
            
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(debug_specific_cases()) 