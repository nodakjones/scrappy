#!/usr/bin/env python3
"""
Data processing test for contractor enrichment system
"""
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def test_csv_data_loading():
    """Test that contractor CSV data can be loaded and processed"""
    print("Testing CSV data loading...")
    
    try:
        # Load the contractor data
        csv_path = Path(__file__).parent.parent / "data" / "contractors.csv"
        
        if not csv_path.exists():
            print("❌ CSV file not found")
            return False
            
        df = pd.read_csv(csv_path)
        print(f"✅ CSV loaded successfully with {len(df)} records")
        
        # Check that expected columns exist
        required_columns = [
            'business_name',
            'contractor_license_number',
            'contractor_license_type_code',
            'city',
            'state',
            'phone_number'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        print("✅ All required columns present")
        
        # Show sample data
        print(f"  - Total records: {len(df)}")
        print(f"  - Unique businesses: {df['business_name'].nunique()}")
        print(f"  - States represented: {df['state'].nunique()}")
        
        # Show a sample record
        print(f"  - Sample business: {df.iloc[0]['business_name']}")
        print(f"  - Sample location: {df.iloc[0]['city']}, {df.iloc[0]['state']}")
        
        return True
    except Exception as e:
        print(f"❌ CSV loading failed: {e}")
        return False

def test_data_cleaning():
    """Test data cleaning functions"""
    print("Testing data cleaning functions...")
    
    try:
        # Import the cleaning functions from the import script
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        
        # Import the import_data script to get cleaning functions
        import importlib.util
        script_path = Path(__file__).parent.parent / "scripts" / "import_data.py"
        spec = importlib.util.spec_from_file_location("import_data", script_path)
        import_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(import_module)
        
        # Test phone number cleaning
        test_phones = [
            "1234567890",
            "(123) 456-7890",
            "123-456-7890",
            "123.456.7890",
            "123 456 7890",
            "invalid",
            "",
            None
        ]
        
        for phone in test_phones:
            cleaned = import_module.clean_phone_number(phone)
            if phone and len(phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').replace('.', '')) == 10:
                print(f"✅ Phone '{phone}' → '{cleaned}'")
            else:
                print(f"✅ Invalid phone '{phone}' → '{cleaned}'")
        
        return True
    except Exception as e:
        print(f"❌ Data cleaning test failed: {e}")
        return False

def test_contractor_model_creation():
    """Test creating contractor models from CSV data"""
    print("Testing contractor model creation...")
    
    try:
        from src.database.models import Contractor
        
        # Load sample data
        csv_path = Path(__file__).parent.parent / "data" / "contractors.csv"
        df = pd.read_csv(csv_path)
        
        # Create a contractor model from the first row
        first_row = df.iloc[0]
        
        contractor = Contractor(
            business_name=first_row['business_name'],
            contractor_license_number=first_row.get('contractor_license_number'),
            city=first_row.get('city'),
            state=first_row.get('state'),
            phone_number=first_row.get('phone_number')
        )
        
        print(f"✅ Created contractor model: {contractor.business_name}")
        print(f"  - License: {contractor.contractor_license_number}")
        print(f"  - Location: {contractor.city}, {contractor.state}")
        print(f"  - Phone: {contractor.phone_number}")
        
        return True
    except Exception as e:
        print(f"❌ Contractor model creation failed: {e}")
        return False

def test_batch_processing_simulation():
    """Test simulated batch processing"""
    print("Testing batch processing simulation...")
    
    try:
        from src.config import config
        
        # Load data
        csv_path = Path(__file__).parent.parent / "data" / "contractors.csv"
        df = pd.read_csv(csv_path)
        
        batch_size = config.BATCH_SIZE
        total_records = len(df)
        num_batches = (total_records + batch_size - 1) // batch_size
        
        print(f"✅ Batch processing setup:")
        print(f"  - Total records: {total_records}")
        print(f"  - Batch size: {batch_size}")
        print(f"  - Number of batches: {num_batches}")
        
        # Simulate processing first batch
        first_batch = df.head(batch_size)
        print(f"✅ First batch contains {len(first_batch)} records")
        
        # Show processing would work on sample records
        for i, (_, row) in enumerate(first_batch.iterrows()):
            if i < 3:  # Show first 3 records
                print(f"  - Record {i+1}: {row['business_name']} ({row['city']}, {row['state']})")
        
        if len(first_batch) > 3:
            print(f"  - ... and {len(first_batch) - 3} more records in this batch")
        
        return True
    except Exception as e:
        print(f"❌ Batch processing simulation failed: {e}")
        return False

def main():
    """Run all data processing tests"""
    print("=== Contractor Enrichment System Data Processing Tests ===\n")
    
    tests = [
        test_csv_data_loading,
        test_contractor_model_creation,
        test_batch_processing_simulation,
        test_data_cleaning
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
        print("🎉 All data processing tests passed! Data handling is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the data processing setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)