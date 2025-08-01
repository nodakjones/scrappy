#!/usr/bin/env python3
"""
Deduplicate and merge contractor export files
Keeps the most recent record for each contractor based on file timestamp
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import sys

def parse_timestamp(filename):
    """Extract timestamp from filename like contractor_export_full_20250801_212933.csv"""
    try:
        # Extract timestamp parts from filename
        parts = filename.stem.split('_')
        date_part = parts[-2]  # 20250801
        time_part = parts[-1]  # 212933
        
        # Convert to datetime for comparison
        timestamp_str = f"{date_part}_{time_part}"
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return timestamp
    except Exception as e:
        print(f"Warning: Could not parse timestamp from {filename}: {e}")
        return datetime.min

def main():
    parser = argparse.ArgumentParser(description='Deduplicate contractor export files')
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
    
    # Find all matching export files
    export_files = sorted(export_dir.glob(args.pattern))
    
    if not export_files:
        print(f"No files found matching pattern '{args.pattern}' in {export_dir}")
        return 1
    
    print(f"🔍 Found {len(export_files)} export files:")
    print("=" * 60)
    
    file_data = []
    total_records = 0
    
    # Load all files with their timestamps
    for file_path in export_files:
        try:
            df = pd.read_csv(file_path)
            timestamp = parse_timestamp(file_path)
            size_mb = file_path.stat().st_size / (1024*1024)
            
            print(f"{file_path.name}:")
            print(f"  Records: {len(df):,}")
            print(f"  Size: {size_mb:.1f} MB") 
            print(f"  Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Add file timestamp to dataframe for tracking
            df['_file_timestamp'] = timestamp
            df['_source_file'] = file_path.name
            
            file_data.append(df)
            total_records += len(df)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    if not file_data:
        print("No valid files to process")
        return 1
    
    print(f"📊 BEFORE DEDUPLICATION:")
    print(f"Total files: {len(file_data)}")
    print(f"Total records: {total_records:,}")
    
    # Combine all dataframes
    print("\n🔄 Combining all dataframes...")
    combined_df = pd.concat(file_data, ignore_index=True)
    
    # Identify duplicate contractors
    # Use business_name and phone_number as the key for identifying duplicates
    print("🔍 Identifying duplicates...")
    
    # Check different duplicate identification strategies
    dup_strategies = {
        'business_name + phone': ['business_name', 'phone_number'],
        'business_name + address': ['business_name', 'address_line_1'],
        'business_name only': ['business_name']
    }
    
    for strategy_name, columns in dup_strategies.items():
        # Only use columns that exist in the dataframe
        available_columns = [col for col in columns if col in combined_df.columns]
        if available_columns:
            duplicates = combined_df.duplicated(subset=available_columns, keep=False)
            dup_count = duplicates.sum()
            print(f"  {strategy_name}: {dup_count:,} duplicate records")
    
    # Use the most reliable strategy (business_name + phone_number if available)
    dedup_columns = ['business_name', 'phone_number']
    if 'phone_number' not in combined_df.columns:
        # Fallback strategies if phone_number column doesn't exist
        if 'address_line_1' in combined_df.columns:
            dedup_columns = ['business_name', 'address_line_1']
        else:
            dedup_columns = ['business_name']
            print("⚠️ Warning: Using business_name only for deduplication")
    
    print(f"\n🎯 Using deduplication strategy: {' + '.join(dedup_columns)}")
    
    # Sort by file timestamp (most recent first) so we keep the latest version
    combined_df_sorted = combined_df.sort_values('_file_timestamp', ascending=False)
    
    # Remove duplicates, keeping the first occurrence (which is now the most recent due to sorting)
    print("🔧 Removing duplicates (keeping most recent records)...")
    deduplicated_df = combined_df_sorted.drop_duplicates(subset=dedup_columns, keep='first')
    
    # Remove the helper columns we added
    deduplicated_df = deduplicated_df.drop(['_file_timestamp', '_source_file'], axis=1)
    
    print(f"\n📊 AFTER DEDUPLICATION:")
    print(f"Original records: {len(combined_df):,}")
    print(f"Unique records: {len(deduplicated_df):,}")
    print(f"Duplicates removed: {len(combined_df) - len(deduplicated_df):,}")
    print(f"Reduction: {((len(combined_df) - len(deduplicated_df)) / len(combined_df) * 100):.1f}%")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No output file created")
        print("Use without --dry-run to create the deduplicated file")
        return 0
    
    # Generate output filename if not specified
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"contractor_export_deduplicated_{timestamp}.csv"
    
    output_path = export_dir / args.output
    
    # Create the deduplicated export
    print(f"\n💾 Creating deduplicated export: {output_path}")
    deduplicated_df.to_csv(output_path, index=False)
    
    # Show file info
    output_size_mb = output_path.stat().st_size / (1024*1024)
    print(f"✅ Export complete!")
    print(f"Output file: {output_path}")
    print(f"Records: {len(deduplicated_df):,}")
    print(f"Size: {output_size_mb:.1f} MB")
    
    # Show sample of deduplicated data
    print(f"\n📋 Sample of deduplicated data (first 5 records):")
    print("=" * 80)
    sample_columns = ['business_name', 'phone_number', 'city', 'state', 'website_url']
    available_sample_columns = [col for col in sample_columns if col in deduplicated_df.columns]
    
    if available_sample_columns:
        sample_df = deduplicated_df[available_sample_columns].head()
        for idx, row in sample_df.iterrows():
            print(f"{idx+1}. {row.get('business_name', 'N/A')} | {row.get('phone_number', 'N/A')} | {row.get('city', 'N/A')}, {row.get('state', 'N/A')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())