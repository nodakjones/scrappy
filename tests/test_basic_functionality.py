#!/usr/bin/env python3
"""
Basic functionality tests for contractor enrichment system
"""
import asyncio
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import config
from database.connection import DatabasePool
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test basic database connectivity"""
    logger.info("Testing database connection...")
    
    try:
        conn = await asyncpg.connect(config.database_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database connection returned unexpected result")
            return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def test_database_pool():
    """Test database connection pool"""
    logger.info("Testing database connection pool...")
    
    try:
        pool = DatabasePool()
        await pool.initialize()
        
        # Test basic query
        result = await pool.fetchval("SELECT 1")
        if result != 1:
            logger.error("❌ Database pool query returned unexpected result")
            await pool.close()
            return False
        
        # Test multiple concurrent queries
        tasks = []
        for i in range(5):
            task = pool.fetchval("SELECT $1", i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        expected = list(range(5))
        
        if results != expected:
            logger.error(f"❌ Concurrent queries failed. Expected {expected}, got {results}")
            await pool.close()
            return False
        
        await pool.close()
        logger.info("✅ Database connection pool test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database pool test failed: {e}")
        return False


async def test_schema_exists():
    """Test that database schema exists"""
    logger.info("Testing database schema...")
    
    try:
        conn = await asyncpg.connect(config.database_url)
        
        # Check main tables exist
        expected_tables = [
            'contractors',
            'categories',
            'website_searches',
            'website_crawls',
            'manual_review_queue',
            'export_batches',
            'processing_logs'
        ]
        
        for table in expected_tables:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if not exists:
                logger.error(f"❌ Table {table} does not exist")
                await conn.close()
                return False
        
        # Check categories has data
        categories_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
        if categories_count == 0:
            logger.error("❌ categories table is empty")
            await conn.close()
            return False
        
        await conn.close()
        logger.info(f"✅ Database schema test successful. Found {categories_count} categories")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        return False


async def test_configuration():
    """Test configuration validation"""
    logger.info("Testing configuration...")
    
    try:
        # Test basic config access
        db_host = config.DB_HOST
        db_name = config.DB_NAME
        
        if not db_host or not db_name:
            logger.error("❌ Basic configuration missing")
            return False
        
        # Test database URL generation
        db_url = config.database_url
        if not db_url.startswith('postgresql://'):
            logger.error("❌ Database URL format invalid")
            return False
        
        logger.info(f"✅ Configuration test successful. DB: {db_name}@{db_host}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def test_data_import_readiness():
    """Test if system is ready for data import"""
    logger.info("Testing data import readiness...")
    
    try:
        conn = await asyncpg.connect(config.database_url)
        
        # Check if we can insert a test contractor
        test_record = {
            'business_name': 'Test Contractor LLC',
            'city': 'Seattle',
            'state': 'WA',
            'processing_status': 'pending'
        }
        
        # Insert test record
        await conn.execute("""
            INSERT INTO contractors (business_name, city, state, processing_status)
            VALUES ($1, $2, $3, $4)
        """, test_record['business_name'], test_record['city'], 
            test_record['state'], test_record['processing_status'])
        
        # Verify it was inserted
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM contractors WHERE business_name = $1",
            test_record['business_name']
        )
        
        if count != 1:
            logger.error("❌ Test record insert verification failed")
            await conn.close()
            return False
        
        # Clean up test record
        await conn.execute(
            "DELETE FROM contractors WHERE business_name = $1",
            test_record['business_name']
        )
        
        await conn.close()
        logger.info("✅ Data import readiness test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data import readiness test failed: {e}")
        return False


async def run_all_tests():
    """Run all basic functionality tests"""
    logger.info("🧪 Running basic functionality tests...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Database Pool", test_database_pool),
        ("Schema Exists", test_schema_exists),
        ("Data Import Readiness", test_data_import_readiness),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Total: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! System is ready for operation.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix issues before proceeding.")
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_all_tests())
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()