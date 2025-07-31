#!/usr/bin/env python3
"""
System State Validation - Run BEFORE making any configuration changes
"""
import os
import sys
from pathlib import Path

def check_system_state():
    """Check current system state and warn about existing configuration"""
    issues = []
    warnings = []
    
    print("🔍 SYSTEM STATE VALIDATION")
    print("=" * 50)
    
    # Check .env file
    if os.path.exists('.env'):
        warnings.append("⚠️  .env file EXISTS - DO NOT OVERWRITE!")
        print("✅ Found existing .env configuration")
        
        # Check if it has real values
        with open('.env', 'r') as f:
            content = f.read()
            if 'your_openai_api_key_here' in content or 'placeholder' in content:
                issues.append("❌ .env file contains placeholder values")
            else:
                print("✅ .env appears to have real configuration")
    else:
        print("ℹ️  No .env file found - safe to create from template")
    
    # Check database
    try:
        sys.path.append(str(Path('.') / 'src'))
        import asyncio
        from database.connection import DatabasePool
        
        async def check_db():
            try:
                db = DatabasePool()
                await db.initialize()
                count = await db.pool.fetchval('SELECT COUNT(*) FROM contractors')
                if count > 0:
                    warnings.append(f"⚠️  Database has {count:,} contractors - DO NOT RESET!")
                    print(f"✅ Database is populated with {count:,} contractors")
                else:
                    print("ℹ️  Database is empty - safe to initialize")
                await db.close()
                return True
            except Exception as e:
                issues.append(f"❌ Database connection failed: {e}")
                return False
        
        db_ok = asyncio.run(check_db())
    except Exception as e:
        issues.append(f"❌ Cannot check database: {e}")
    
    # Check for running processes
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'run_processing.py'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            warnings.append("⚠️  Processing script is currently running!")
            print("✅ Found running processing script")
        else:
            print("ℹ️  No processing scripts currently running")
    except:
        pass
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("❌ CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    
    if warnings:
        print("⚠️  IMPORTANT WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
        print("\n🚨 SYSTEM APPEARS TO BE ALREADY CONFIGURED!")
        print("   Ask user about current state before making changes!")
    
    if not issues and not warnings:
        print("✅ System appears to be in clean state - safe to configure")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = check_system_state()
    if not success:
        print("\n❌ System validation failed!")
        sys.exit(1)
    else:
        print("\n✅ System validation passed")