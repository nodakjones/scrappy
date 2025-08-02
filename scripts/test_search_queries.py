#!/usr/bin/env python3
"""
Test script to demonstrate the simplified search queries
"""
import asyncio
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService

async def test_search_queries(contractor_name):
    """Test the simplified search queries for a contractor"""
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
        
        contractor = ContractorService()
        
        # Test the simplified search queries
        business_name = result['business_name']
        city = result['city'] or ''
        state = result['state'] or ''
        
        print(f"🔍 Testing search queries for: {business_name}")
        print(f"📍 Location: {city}, {state}")
        print("=" * 60)
        
        # Generate and display the queries
        queries = contractor._generate_search_queries(business_name, city, state)
        
        print("📋 Generated Search Queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        # Test simple business name generation
        simple_name = contractor._generate_simple_business_name(business_name)
        print(f"\n🔄 Simple Business Name: '{simple_name}'")
        
        print(f"\n📊 Query Analysis:")
        print(f"  Original: '{business_name}'")
        print(f"  Simple:   '{simple_name}'")
        print(f"  Location: '{city}, {state}'")
        
        await contractor.close()
    
    await db_pool.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test simplified search queries')
    parser.add_argument('--contractor', '-c', type=str, default='425 CONSTRUCTION', help='Contractor name to test')
    args = parser.parse_args()
    
    asyncio.run(test_search_queries(args.contractor)) 