#!/usr/bin/env python3
"""
Re-export all processed contractors with fixed address columns
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import csv

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import db_pool
from src.database.models import Contractor

async def get_all_processed_contractors():
    """Get all contractors that have been processed"""
    query = """
    SELECT * FROM contractors 
    WHERE processing_status IN ('completed', 'manual_review', 'approved')
    ORDER BY confidence_score DESC, business_name ASC
    """
    
    rows = await db_pool.fetch(query)
    
    contractors = []
    for row in rows:
        contractor = Contractor.from_dict(dict(row))
        contractors.append(contractor)
        
    return contractors

async def export_contractors_fixed(contractors, export_dir):
    """Export contractors using the FIXED column structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fixed column definitions (matching our corrected export service)
    full_columns = [
        'id', 'business_name', 'phone_number', 'address1', 'address2', 'city', 'state', 'zip',
        'website_url', 'confidence_score', 'is_home_contractor', 'mailer_category',
        'contractor_license_type_code_desc', 'processing_status', 'last_processed'
    ]
    
    summary_columns = [
        'business_name', 'phone_number', 'address1', 'address2', 'city', 'state', 'website_url', 
        'confidence_score', 'is_home_contractor', 'mailer_category'
    ]
    
    # Create full export
    full_file = export_dir / f"contractor_export_REPROCESSED_full_{timestamp}.csv"
    with open(full_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=full_columns)
        writer.writeheader()
        
        for contractor in contractors:
            row = {}
            for col in full_columns:
                value = getattr(contractor, col, None)
                
                if value is None:
                    row[col] = ''
                elif isinstance(value, datetime):
                    row[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif col == 'confidence_score' and value is not None:
                    row[col] = f"{float(value):.3f}"
                else:
                    row[col] = str(value)
            
            writer.writerow(row)
    
    # Create summary export
    summary_file = export_dir / f"contractor_export_REPROCESSED_summary_{timestamp}.csv"
    with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=summary_columns)
        writer.writeheader()
        
        for contractor in contractors:
            row = {}
            for col in summary_columns:
                value = getattr(contractor, col, None)
                
                if value is None:
                    row[col] = ''
                elif col == 'confidence_score' and value is not None:
                    row[col] = f"{float(value):.3f}"
                else:
                    row[col] = str(value)
            
            writer.writerow(row)
    
    return full_file, summary_file

async def analyze_address_coverage(contractors):
    """Analyze address coverage in the processed contractors"""
    total = len(contractors)
    has_address1 = sum(1 for c in contractors if c.address1 and str(c.address1).strip())
    has_address2 = sum(1 for c in contractors if c.address2 and str(c.address2).strip())
    
    coverage1 = (has_address1 / total * 100) if total > 0 else 0
    coverage2 = (has_address2 / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'address1_count': has_address1,
        'address1_coverage': coverage1,
        'address2_count': has_address2,
        'address2_coverage': coverage2
    }

async def main():
    """Main export function"""
    print("🔄 RE-EXPORTING ALL PROCESSED CONTRACTORS")
    print("=" * 60)
    
    await db_pool.initialize()
    
    try:
        # Get all processed contractors
        print("📋 Fetching all processed contractors from database...")
        contractors = await get_all_processed_contractors()
        
        if not contractors:
            print("❌ No processed contractors found")
            return
        
        print(f"✅ Found {len(contractors):,} processed contractors")
        
        # Analyze address coverage in database
        print("\n🔍 Analyzing address coverage in database...")
        coverage = await analyze_address_coverage(contractors)
        
        print(f"📊 DATABASE ADDRESS COVERAGE:")
        print(f"  Total contractors: {coverage['total']:,}")
        print(f"  Address1 coverage: {coverage['address1_count']:,} ({coverage['address1_coverage']:.1f}%)")
        print(f"  Address2 coverage: {coverage['address2_count']:,} ({coverage['address2_coverage']:.1f}%)")
        
        # Show sample addresses from database
        print(f"\n📋 SAMPLE ADDRESSES FROM DATABASE:")
        contractors_with_addresses = [c for c in contractors[:5] if c.address1 and str(c.address1).strip()]
        
        for i, contractor in enumerate(contractors_with_addresses[:3], 1):
            print(f"{i}. {contractor.business_name}")
            print(f"   📞 {contractor.phone_number}")
            print(f"   📍 {contractor.address1}" + (f", {contractor.address2}" if contractor.address2 and str(contractor.address2).strip() else ""))
            print(f"   🏙️ {contractor.city}, {contractor.state}")
            print()
        
        # Create exports with fixed structure
        print("💾 Creating exports with FIXED address columns...")
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        full_file, summary_file = await export_contractors_fixed(contractors, export_dir)
        
        # Show export results
        full_size = full_file.stat().st_size
        summary_size = summary_file.stat().st_size
        
        print(f"\n✅ RE-EXPORT COMPLETED!")
        print(f"📄 Files created:")
        print(f"  Full: {full_file.name} ({full_size:,} bytes / {full_size/1024/1024:.1f} MB)")
        print(f"  Summary: {summary_file.name} ({summary_size:,} bytes / {summary_size/1024:.1f} KB)")
        
        # Verify addresses in export
        print(f"\n🔍 VERIFYING ADDRESS DATA IN EXPORT:")
        with open(full_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sample_count = 0
            address_count = 0
            
            for row in reader:
                if row['address1'] and row['address1'].strip():
                    address_count += 1
                    if sample_count < 3:
                        print(f"{sample_count + 1}. {row['business_name']}")
                        print(f"   📍 {row['address1']}" + (f", {row['address2']}" if row['address2'] else ""))
                        print(f"   🏙️ {row['city']}, {row['state']}")
                        sample_count += 1
                        print()
            
            export_coverage = (address_count / len(contractors) * 100) if len(contractors) > 0 else 0
            print(f"📊 EXPORT ADDRESS COVERAGE: {address_count:,}/{len(contractors):,} ({export_coverage:.1f}%)")
        
        if export_coverage > 95:
            print("🎉 EXCELLENT! Near-perfect address coverage achieved!")
        elif export_coverage > 80:
            print("✅ GOOD! High address coverage in export!")
        else:
            print("⚠️ Address coverage could be improved")
        
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())