#!/usr/bin/env python3
"""
Configuration test for contractor enrichment system
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def test_config_import():
    """Test that config can be imported and loaded"""
    print("Testing configuration import...")
    
    try:
        from src.config import Config, config
        print("✅ Config module imported successfully")
        
        # Test that basic config values exist
        assert hasattr(config, 'DB_HOST')
        assert hasattr(config, 'DB_NAME')
        assert hasattr(config, 'BATCH_SIZE')
        print("✅ Config attributes exist")
        
        # Test that config has reasonable defaults
        assert config.DB_HOST is not None
        assert config.DB_NAME is not None
        assert config.BATCH_SIZE > 0
        print("✅ Config has reasonable values")
        
        print(f"  - Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        print(f"  - Batch size: {config.BATCH_SIZE}")
        print(f"  - Debug mode: {config.DEBUG}")
        
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_database_models():
    """Test that database models can be imported"""
    print("Testing database models import...")
    
    try:
        from src.database.models import Contractor, MailerCategory
        print("✅ Database models imported successfully")
        
        # Test creating a basic contractor object
        contractor = Contractor(business_name="Test Contractor")
        assert contractor.business_name == "Test Contractor"
        print("✅ Contractor model works")
        
        return True
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        return False

def test_required_packages():
    """Test that required packages can be imported"""
    print("Testing required package imports...")
    
    required_packages = [
        'asyncpg',
        'pandas', 
        'asyncio',
        'logging',
        'pathlib'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            return False
    
    return True

def main():
    """Run all configuration tests"""
    print("=== Contractor Enrichment System Configuration Tests ===\n")
    
    tests = [
        test_required_packages,
        test_config_import,
        test_database_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n--- {test.__name__} ---")
        if test():
            passed += 1
        print()
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All configuration tests passed! System is properly configured.")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)