#!/usr/bin/env python3
"""
Data import script for contractor enrichment system
"""
import asyncio
import pandas as pd
import asyncpg
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import re
from typing import Optional, Dict, Any

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_phone_number(phone: Optional[str]) -> Optional[str]:
    """Standardize phone number to (XXX) XXX-XXXX format"""
    if phone is None or pd.isna(phone) or str(phone).strip() == '':
        return None
    
    phone_str = str(phone).strip()
    
    # Remove all non-digit characters
    digits = re.sub(r'[^\d]', '', phone_str)
    
    # Check if we have exactly 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        # Remove leading 1
        digits = digits[1:]
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Return original if we can't parse it properly
    return phone_str


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date in MM/DD/YYYY or YYYY-MM-DD format"""
    if date_str is None or pd.isna(date_str) or str(date_str).strip() == '':
        return None
    
    date_str = str(date_str).strip()
    
    # Try MM/DD/YYYY format
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        pass
    
    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass
    
    # Try MM-DD-YYYY format
    try:
        return datetime.strptime(date_str, '%m-%d-%Y')
    except ValueError:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def clean_text_field(value: Optional[str]) -> Optional[str]:
    """Clean and standardize text fields"""
    if value is None or pd.isna(value):
        return None
    
    value_str = str(value).strip()
    if value_str in ['', 'nan', 'NaN', 'None']:
        return None
    return value_str


def prepare_contractor_record(row: pd.Series) -> Dict[str, Any]:
    """Prepare a single contractor record for database insertion"""
    record = {
        # Original contractor data fields (matching CSV columns exactly)
        'business_name': clean_text_field(row.get('BusinessName', '')),
        'contractor_license_number': clean_text_field(row.get('ContractorLicenseNumber')),
        'contractor_license_type_code': clean_text_field(row.get('ContractorLicenseTypeCode')),
        'contractor_license_type_code_desc': clean_text_field(row.get('ContractorLicenseTypeCodeDesc')),
        'address1': clean_text_field(row.get('Address1')),
        'address2': clean_text_field(row.get('Address2')),
        'city': clean_text_field(row.get('City')),
        'state': clean_text_field(row.get('State')),
        'zip': clean_text_field(row.get('Zip')),
        'phone_number': clean_phone_number(row.get('PhoneNumber')),
        'license_effective_date': parse_date(row.get('LicenseEffectiveDate')),
        'license_expiration_date': parse_date(row.get('LicenseExpirationDate')),
        'business_type_code': clean_text_field(row.get('BusinessTypeCode')),
        'business_type_code_desc': clean_text_field(row.get('BusinessTypeCodeDesc')),
        'specialty_code1': clean_text_field(row.get('SpecialtyCode1')),
        'specialty_code1_desc': clean_text_field(row.get('SpecialtyCode1Desc')),
        'specialty_code2': clean_text_field(row.get('SpecialtyCode2')),
        'specialty_code2_desc': clean_text_field(row.get('SpecialtyCode2Desc')),
        'ubi': clean_text_field(row.get('UBI')),
        'primary_principal_name': clean_text_field(row.get('PrimaryPrincipalName')),
        'status_code': clean_text_field(row.get('StatusCode')),
        'contractor_license_status': clean_text_field(row.get('ContractorLicenseStatus')),
        'contractor_license_suspend_date': parse_date(row.get('ContractorLicenseSuspendDate')),
        
        # Set default processing status
        'processing_status': 'pending',
        'processing_attempts': 0,
        'manual_review_needed': False,
        'marked_for_download': False,
        'priority_category': False
    }
    
    # Validate required fields
    if not record['business_name']:
        raise ValueError("BusinessName is required")
    
    return record


async def import_contractors(csv_file_path: str, batch_size: int = 1000) -> Dict[str, int]:
    """Import contractor data from CSV file"""
    logger.info(f"Starting import from {csv_file_path}")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path, dtype=str)
        logger.info(f"Loaded {len(df)} records from CSV")
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise
    
    # Connect to database
    conn = await asyncpg.connect(config.database_url)
    
    stats = {
        'total_records': len(df),
        'successful_imports': 0,
        'failed_imports': 0,
        'skipped_records': 0
    }
    
    try:
        # Process records in batches
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: records {i+1}-{min(i + batch_size, len(df))}")
            
            batch_records = []
            batch_errors = []
            
            for idx, row in batch_df.iterrows():
                try:
                    record = prepare_contractor_record(row)
                    batch_records.append(record)
                except Exception as e:
                    batch_errors.append(f"Row {idx + 1}: {e}")
                    stats['failed_imports'] += 1
            
            # Insert batch records
            if batch_records:
                try:
                    # Prepare INSERT statement
                    columns = list(batch_records[0].keys())
                    placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                    insert_query = f"""
                        INSERT INTO contractors ({', '.join(columns)})
                        VALUES ({placeholders})
                    """
                    
                    # Convert records to tuples
                    values_list = []
                    for record in batch_records:
                        values = tuple(record[col] for col in columns)
                        values_list.append(values)
                    
                    # Execute batch insert
                    await conn.executemany(insert_query, values_list)
                    stats['successful_imports'] += len(batch_records)
                    logger.info(f"Successfully imported {len(batch_records)} records")
                    
                except Exception as e:
                    logger.error(f"Error importing batch: {e}")
                    stats['failed_imports'] += len(batch_records)
            
            # Log any batch errors
            for error in batch_errors:
                logger.warning(error)
    
    finally:
        await conn.close()
    
    return stats


async def verify_import() -> None:
    """Verify the import by checking record counts and data quality"""
    logger.info("Verifying import...")
    
    conn = await asyncpg.connect(config.database_url)
    
    try:
        # Basic counts
        total_count = await conn.fetchval("SELECT COUNT(*) FROM contractors")
        pending_count = await conn.fetchval("SELECT COUNT(*) FROM contractors WHERE processing_status = 'pending'")
        
        logger.info(f"Total contractors: {total_count}")
        logger.info(f"Pending processing: {pending_count}")
        
        # Data quality checks
        no_business_name = await conn.fetchval("SELECT COUNT(*) FROM contractors WHERE business_name IS NULL OR business_name = ''")
        has_phone = await conn.fetchval("SELECT COUNT(*) FROM contractors WHERE phone_number IS NOT NULL")
        has_address = await conn.fetchval("SELECT COUNT(*) FROM contractors WHERE city IS NOT NULL AND state IS NOT NULL")
        
        logger.info(f"Records without business name: {no_business_name}")
        logger.info(f"Records with phone numbers: {has_phone}")
        logger.info(f"Records with city/state: {has_address}")
        
        # State distribution
        state_dist = await conn.fetch("""
            SELECT state, COUNT(*) as count 
            FROM contractors 
            WHERE state IS NOT NULL 
            GROUP BY state 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        logger.info("Top 10 states:")
        for row in state_dist:
            logger.info(f"  {row['state']}: {row['count']} contractors")
        
    finally:
        await conn.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import contractor data from CSV')
    parser.add_argument('--file', '-f', default='data/contractors.csv',
                       help='Path to CSV file (default: data/contractors.csv)')
    parser.add_argument('--batch-size', '-b', type=int, default=1000,
                       help='Batch size for imports (default: 1000)')
    parser.add_argument('--verify', '-v', action='store_true',
                       help='Only verify existing data (no import)')
    
    args = parser.parse_args()
    
    async def run_import():
        # Validate configuration
        if not config.validate():
            logger.error("Configuration validation failed")
            return False
        
        if args.verify:
            await verify_import()
            return True
        
        # Check if CSV file exists
        csv_path = Path(args.file)
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        try:
            # Run the import
            stats = await import_contractors(str(csv_path), args.batch_size)
            
            # Display results
            print(f"\n📊 Import Summary:")
            print(f"Total records processed: {stats['total_records']}")
            print(f"✅ Successfully imported: {stats['successful_imports']}")
            print(f"❌ Failed imports: {stats['failed_imports']}")
            print(f"⏭️ Skipped records: {stats['skipped_records']}")
            
            # Verify the import
            await verify_import()
            
            print(f"\n✅ Data import completed!")
            print(f"Next step: Run processing with 'python scripts/run_processing.py'")
            
            return stats['failed_imports'] == 0
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False
    
    if not asyncio.run(run_import()):
        sys.exit(1)


if __name__ == "__main__":
    main()