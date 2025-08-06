#!/usr/bin/env python3
"""
Analyze Website Discovery Issues
==============================

Analyze potential issues with website discovery for specific contractors.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool

async def analyze_website_discovery_issues():
    """Analyze potential issues with website discovery"""
    await db_pool.initialize()
    
    print("🔍 WEBSITE DISCOVERY ISSUE ANALYSIS")
    print("=" * 50)
    
    # Test cases with known websites
    test_cases = [
        {
            'business_name': '5 STAR GARAGE INTERIORS',
            'expected_website': 'https://5stargarageinteriors.com',
            'search_queries': [
                '5 STAR GARAGE INTERIORS',
                '5 Star Garage Interiors',
                '5 Star Garage Interiors Seattle',
                '5 Star Garage Interiors WA'
            ]
        },
        {
            'business_name': '5 CORNERS PLUMBING LLC',
            'expected_website': 'https://5cornersplumbing.com',
            'search_queries': [
                '5 CORNERS PLUMBING LLC',
                '5 Corners Plumbing LLC',
                '5 Corners Plumbing Seattle',
                '5 Corners Plumbing WA'
            ]
        },
        {
            'business_name': 'A-1 Flooring',
            'expected_website': 'https://www.a1professionalflooring.com',
            'search_queries': [
                'A-1 Flooring',
                'A-1 Professional Flooring',
                'A-1 Flooring Puyallup',
                'A-1 Flooring WA'
            ]
        }
    ]
    
    print(f"📊 Analyzing {len(test_cases)} test cases...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 Test Case {i}: {test_case['business_name']}")
        print(f"   - Expected website: {test_case['expected_website']}")
        print(f"   - Search queries to test:")
        
        for query in test_case['search_queries']:
            print(f"     * '{query}'")
        
        print()
    
    # Check current database status for these contractors
    print(f"📋 Current Database Status:")
    print()
    
    for test_case in test_cases:
        business_name = test_case['business_name']
        
        # Find contractor in database
        query = """
            SELECT id, business_name, website_url, confidence_score, processing_status, review_status
            FROM contractors 
            WHERE business_name ILIKE $1
            AND status_code = 'A'
            ORDER BY id
            LIMIT 1
        """
        
        row = await db_pool.fetchrow(query, f"%{business_name}%")
        
        if row:
            print(f"✅ Found: {row['business_name']} (ID: {row['id']})")
            print(f"   - Current website: {row['website_url'] or 'None'}")
            print(f"   - Current confidence: {row['confidence_score'] or 0.0}")
            print(f"   - Processing status: {row['processing_status']}")
            print(f"   - Review status: {row['review_status']}")
        else:
            print(f"❌ Not found in database: {business_name}")
        
        print()
    
    # Analyze potential issues
    print(f"🔍 POTENTIAL ISSUES:")
    print()
    
    issues = [
        "1. **Business Name Variations**: '5 STAR GARAGE INTERIORS' vs '5 Star Garage Interiors'",
        "2. **Special Characters**: 'A-1 Flooring' contains hyphens that might affect search",
        "3. **LLC/Suffix Handling**: '5 CORNERS PLUMBING LLC' vs '5 Corners Plumbing'",
        "4. **Geographic Filtering**: Some contractors might be filtered out by location",
        "5. **Domain Filtering**: Some legitimate domains might be in excluded list",
        "6. **Search Query Generation**: Current queries might not match business names well",
        "7. **Confidence Thresholds**: Website discovery confidence might be too strict"
    ]
    
    for issue in issues:
        print(f"   {issue}")
    
    print()
    print(f"💡 RECOMMENDATIONS:")
    print()
    
    recommendations = [
        "1. **Test search queries manually** to see what Google returns",
        "2. **Review excluded domains** to ensure legitimate sites aren't blocked",
        "3. **Adjust business name processing** to handle special characters better",
        "4. **Lower confidence thresholds** for website discovery",
        "5. **Add more search query variations** for better coverage",
        "6. **Review geographic filtering** to ensure local contractors aren't excluded"
    ]
    
    for rec in recommendations:
        print(f"   {rec}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(analyze_website_discovery_issues()) 