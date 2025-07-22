#!/usr/bin/env python3
"""
API Integration Test for contractor enrichment system
Tests OpenAI and Google Search API connectivity and basic functionality
"""
import sys
import os
from pathlib import Path
import asyncio
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
import openai
import aiohttp

async def test_openai_api():
    """Test OpenAI API connectivity"""
    print("🤖 Testing OpenAI API...")
    
    try:
        # Test basic OpenAI API connectivity
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Simple test query
        response = client.chat.completions.create(
            model=config.GPT4_MINI_MODEL,
            messages=[
                {"role": "user", "content": "What type of business is 'ABC Plumbing Services'? Respond with just the business type."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"  ✅ OpenAI API working - Response: '{result}'")
        
        # Validate response makes sense
        if "plumb" in result.lower() or "service" in result.lower():
            print("  ✅ AI response is contextually appropriate")
        else:
            print("  ⚠️ AI response may not be optimal, but API is working")
            
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI API failed: {e}")
        return False

async def test_google_search_api():
    """Test Google Custom Search API connectivity"""
    print("🔍 Testing Google Search API...")
    
    try:
        # Check if Google API credentials are configured
        google_api_key = os.getenv('GOOGLE_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not google_api_key or not search_engine_id:
            print("  ⚠️ Google API credentials not found in environment")
            return False
            
        # Test Google Custom Search API
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': google_api_key,
            'cx': search_engine_id,
            'q': 'ABC Plumbing Services Seattle WA',
            'num': 3
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results_count = len(data.get('items', []))
                    print(f"  ✅ Google Search API working - Found {results_count} results")
                    
                    if results_count > 0:
                        first_result = data['items'][0]
                        print(f"  ✅ Sample result: {first_result.get('title', 'N/A')}")
                    
                    return True
                else:
                    error_data = await response.json()
                    print(f"  ❌ Google Search API error: {error_data}")
                    return False
                    
    except Exception as e:
        print(f"  ❌ Google Search API failed: {e}")
        return False

async def test_database_connectivity():
    """Test database connectivity and data access"""
    print("🗄️ Testing Database Connectivity...")
    
    try:
        from src.database.connection import DatabasePool
        
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        # Test basic query
        result = await db_pool.fetchrow("SELECT COUNT(*) as count FROM contractors WHERE processing_status = 'pending'")
        pending_count = result['count']
        
        print(f"  ✅ Database connected - {pending_count} contractors pending processing")
        
        # Test sample contractor data
        sample = await db_pool.fetchrow("""
            SELECT business_name, city, state, phone_number 
            FROM contractors 
            WHERE business_name IS NOT NULL 
            AND city IS NOT NULL 
            LIMIT 1
        """)
        
        if sample:
            print(f"  ✅ Sample contractor: {sample['business_name']} in {sample['city']}, {sample['state']}")
        
        await db_pool.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database connectivity failed: {e}")
        return False

async def test_configuration():
    """Test system configuration"""
    print("⚙️ Testing Configuration...")
    
    try:
        # Test basic config values
        assert config.DB_NAME == 'contractor_enrichment'
        assert config.BATCH_SIZE > 0
        assert config.AUTO_APPROVE_THRESHOLD > 0
        
        print(f"  ✅ Database: {config.DB_NAME}")
        print(f"  ✅ Batch size: {config.BATCH_SIZE}")
        print(f"  ✅ Auto-approve threshold: {config.AUTO_APPROVE_THRESHOLD}")
        print(f"  ✅ Manual review threshold: {config.MANUAL_REVIEW_THRESHOLD}")
        
        # Check API keys are present
        if config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'sk-placeholder-key-here':
            print("  ✅ OpenAI API key configured")
        else:
            print("  ⚠️ OpenAI API key not properly configured")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_project_structure():
    """Test that all required files and directories exist"""
    print("📁 Testing Project Structure...")
    
    required_files = [
        'src/config.py',
        'src/database/connection.py', 
        'src/database/models.py',
        'scripts/setup_database.py',
        'scripts/import_data.py',
        'sql/01_create_schema.sql',
        'sql/02_create_indexes.sql',
        'sql/03_insert_categories.sql'
    ]
    
    required_dirs = [
        'src/database',
        'src/processors', 
        'src/services',
        'src/utils',
        'scripts',
        'sql',
        'tests',
        'exports',
        'logs'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if not missing_files and not missing_dirs:
        print("  ✅ All required files and directories present")
        return True
    else:
        if missing_files:
            print(f"  ❌ Missing files: {missing_files}")
        if missing_dirs:
            print(f"  ❌ Missing directories: {missing_dirs}")
        return False

async def main():
    """Run comprehensive system validation"""
    print("🎯 CONTRACTOR ENRICHMENT SYSTEM - COMPREHENSIVE VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Configuration", test_configuration),
        ("Database Connectivity", test_database_connectivity),
        ("OpenAI API", test_openai_api),
        ("Google Search API", test_google_search_api)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"  ❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS GO! The contractor enrichment system is fully operational.")
        print("\n🚀 Ready to start processing contractors!")
        print("   Next step: Run 'python scripts/run_processing.py' to begin enrichment")
    else:
        print("⚠️ Some components need attention before full operation.")
        
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())