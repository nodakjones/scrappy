#!/usr/bin/env python3
"""
Smart deduplicate contractor export files
Prioritizes records with address data over just timestamp recency
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import sys
import numpy as np

def parse_timestamp(filename):
    """Extract timestamp from filename like contractor_export_full_20250801_212933.csv"""
    try:
        parts = filename.stem.split('_')
        date_part = parts[-2]
        time_part = parts[-1]
        timestamp_str = f"{date_part}_{time_part}"
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return timestamp
    except Exception as e:
        print(f"Warning: Could not parse timestamp from {filename}: {e}")
        return datetime.min

def has_address_data(row):
    """Check if a row has actual address data"""
    address_columns = ['address1', 'address2', 'address_line_1']
    for col in address_columns:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != '':
            return True
    return False

def calculate_record_priority(row):
    """Calculate priority score for record selection (higher = better)"""
    score = 0
    
    # Priority 1: Has address data (+1000 points)
    if has_address_data(row):
        score += 1000
    
    # Priority 2: More recent timestamp (+timestamp points)
    if '_file_timestamp' in row.index:
        # Convert timestamp to score (more recent = higher score)
        timestamp_score = row['_file_timestamp'].timestamp() / 1000000  # Scale down
        score += timestamp_score
    
    # Priority 3: Has website (+10 points)
    if 'website_url' in row.index and pd.notna(row['website_url']) and str(row['website_url']).strip() != '':
        score += 10
    
    # Priority 4: Higher confidence score (+confidence points)
    if 'confidence_score' in row.index and pd.notna(row['confidence_score']):
        try:
            score += float(row['confidence_score'])
        except:
            pass
    
    return score

def main():
    parser = argparse.ArgumentParser(description='Smart deduplicate contractor export files')
    parser.add_argument('--export-dir', '-d', default='exports', 
                       help='Directory containing export files (default: exports)')
    parser.add_argument('--output', '-o', 
                       help='Output filename (default: auto-generated with timestamp)')
    parser.add_argument('--pattern', '-p', default='contractor_export_full_*.csv',
                       help='File pattern to match (default: contractor_export_full_*.csv)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without creating output file')
    
    args = parser.parse_args()
    
    export_dir = Path(args.export_dir)
    if not export_dir.exists():
        print(f"Error: Export directory '{export_dir}' does not exist")
        return 1
    
    export_files = sorted(export_dir.glob(args.pattern))
    
    if not export_files:
        print(f"No files found matching pattern '{args.pattern}' in {export_dir}")
        return 1
    
    print(f"🔍 Found {len(export_files)} export files:")
    print("=" * 60)
    
    file_data = []
    total_records = 0
    
    # Load all files with their timestamps and address data info
    for file_path in export_files:
        try:
            df = pd.read_csv(file_path)
            timestamp = parse_timestamp(file_path)
            size_mb = file_path.stat().st_size / (1024*1024)
            
            # Check address data availability
            address_cols = ['address1', 'address2', 'address_line_1']
            address_data_count = 0
            for col in address_cols:
                if col in df.columns:
                    address_data_count += (df[col].notna() & (df[col] != '')).sum()
            
            print(f"{file_path.name}:")
            print(f"  Records: {len(df):,}")
            print(f"  Size: {size_mb:.1f} MB") 
            print(f"  Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Address data: {address_data_count:,} records")
            print()
            
            # Add metadata to dataframe
            df['_file_timestamp'] = timestamp
            df['_source_file'] = file_path.name
            df['_has_address'] = df.apply(has_address_data, axis=1)
            
            file_data.append(df)
            total_records += len(df)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    if not file_data:
        print("No valid files to process")
        return 1
    
    print(f"📊 BEFORE SMART DEDUPLICATION:")
    print(f"Total files: {len(file_data)}")
    print(f"Total records: {total_records:,}")
    
    # Combine all dataframes
    print("\n🔄 Combining all dataframes...")
    combined_df = pd.concat(file_data, ignore_index=True)
    
    # Check address data availability across all records
    has_address_count = combined_df['_has_address'].sum()
    print(f"Records with address data: {has_address_count:,} / {len(combined_df):,}")
    
    # Use business_name + phone_number for deduplication
    dedup_columns = ['business_name', 'phone_number']
    print(f"\n🎯 Using deduplication strategy: {' + '.join(dedup_columns)}")
    
    # Calculate priority scores for all records
    print("🧠 Calculating smart priority scores...")
    combined_df['_priority_score'] = combined_df.apply(calculate_record_priority, axis=1)
    
    # Sort by priority score (highest first) so we keep the best record for each duplicate group
    combined_df_sorted = combined_df.sort_values('_priority_score', ascending=False)
    
    # Remove duplicates, keeping the first occurrence (which is now the highest priority)
    print("🔧 Removing duplicates (keeping highest priority records)...")
    deduplicated_df = combined_df_sorted.drop_duplicates(subset=dedup_columns, keep='first')
    
    # Remove the helper columns we added
    deduplicated_df = deduplicated_df.drop(['_file_timestamp', '_source_file', '_has_address', '_priority_score'], axis=1)
    
    # Check how many records have address data after deduplication
    final_address_count = 0
    address_cols = ['address1', 'address2', 'address_line_1']
    for col in address_cols:
        if col in deduplicated_df.columns:
            final_address_count += (deduplicated_df[col].notna() & (deduplicated_df[col] != '')).sum()
    
    print(f"\n📊 AFTER SMART DEDUPLICATION:")
    print(f"Original records: {len(combined_df):,}")
    print(f"Unique records: {len(deduplicated_df):,}")
    print(f"Duplicates removed: {len(combined_df) - len(deduplicated_df):,}")
    print(f"Reduction: {((len(combined_df) - len(deduplicated_df)) / len(combined_df) * 100):.1f}%")
    print(f"Records with address data: {final_address_count:,}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No output file created")
        print("Smart prioritization would preserve records with address data!")
        return 0
    
    # Generate output filename if not specified
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"contractor_export_smart_deduplicated_{timestamp}.csv"
    
    output_path = export_dir / args.output
    
    # Create the deduplicated export
    print(f"\n💾 Creating smart deduplicated export: {output_path}")
    deduplicated_df.to_csv(output_path, index=False)
    
    # Show file info
    output_size_mb = output_path.stat().st_size / (1024*1024)
    print(f"✅ Smart deduplication complete!")
    print(f"Output file: {output_path}")
    print(f"Records: {len(deduplicated_df):,}")
    print(f"Size: {output_size_mb:.1f} MB")
    
    # Show sample of deduplicated data with addresses
    print(f"\n📋 Sample of smart deduplicated data (first 5 records):")
    print("=" * 80)
    sample_columns = ['business_name', 'phone_number', 'address1', 'city', 'state', 'website_url']
    available_sample_columns = [col for col in sample_columns if col in deduplicated_df.columns]
    
    if available_sample_columns:
        sample_df = deduplicated_df[available_sample_columns].head()
        for idx, row in sample_df.iterrows():
            address = row.get('address1', 'N/A')
            if pd.isna(address) or str(address).strip() == '':
                address = row.get('address2', 'No Address')
            print(f"{idx+1}. {row.get('business_name', 'N/A')} | {row.get('phone_number', 'N/A')} | {address} | {row.get('city', 'N/A')}, {row.get('state', 'N/A')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())