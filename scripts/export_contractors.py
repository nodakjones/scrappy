#!/usr/bin/env python3
"""
Export contractor data with proper database tracking
"""
import asyncio
import pandas as pd
import asyncpg
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import csv
from typing import List, Dict, Any, Optional

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContractorExporter:
    """Handles contractor data export with database tracking"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.export_dir = Path(config.EXPORT_DIR)
        self.export_dir.mkdir(exist_ok=True)
    
    async def create_export_batch(self, exported_by: str, contractor_count: int, file_path: str) -> int:
        """Create a new export batch record and return the batch_id"""
        batch_id = await self.db_pool.fetchval("""
            INSERT INTO export_batches (exported_by, contractor_count, file_path, export_date)
            VALUES ($1, $2, $3, $4)
            RETURNING batch_id
        """, exported_by, contractor_count, file_path, datetime.now())
        
        logger.info(f"Created export batch {batch_id} for {contractor_count} contractors")
        return batch_id
    
    async def mark_contractors_as_exported(self, contractor_ids: List[int], batch_id: int):
        """Mark contractors as exported in the database"""
        export_time = datetime.now()
        
        await self.db_pool.execute("""
            UPDATE contractors 
            SET 
                exported_at = $1,
                export_batch_id = $2,
                marked_for_download = TRUE,
                marked_for_download_at = $1
            WHERE id = ANY($3)
        """, export_time, batch_id, contractor_ids)
        
        logger.info(f"Marked {len(contractor_ids)} contractors as exported in batch {batch_id}")
    
    async def get_ready_contractors(self) -> List[Dict[str, Any]]:
        """Get contractors ready for download (approved_download AND pending_review status)"""
        contractors = await self.db_pool.fetch("""
            SELECT 
                id,
                uuid,
                business_name,
                contractor_license_number,
                contractor_license_type_code,
                contractor_license_type_code_desc,
                address1,
                address2,
                city,
                state,
                zip,
                phone_number,
                license_effective_date,
                license_expiration_date,
                business_type_code,
                business_type_code_desc,
                specialty_code1,
                specialty_code1_desc,
                specialty_code2,
                specialty_code2_desc,
                ubi,
                primary_principal_name,
                status_code,
                contractor_license_status,
                contractor_license_suspend_date,
                mailer_category,
                priority_category,
                website_url,
                website_status,
                business_description,
                tagline,
                established_year,
                years_in_business,
                services_offered,
                service_categories,
                specializations,
                additional_licenses,
                certifications,
                insurance_types,
                website_email,
                website_phone,
                physical_address,
                social_media_urls,
                residential_focus,
                commercial_focus,
                emergency_services,
                free_estimates,
                warranty_offered,
                confidence_score,
                classification_confidence,
                website_confidence,
                processing_status,
                last_processed,
                error_message,
                manual_review_needed,
                manual_review_reason,
                review_status,
                reviewed_by,
                reviewed_at,
                review_notes,
                manual_review_outcome,
                marked_for_download,
                marked_for_download_at,
                exported_at,
                export_batch_id,
                gpt4mini_analysis,
                gpt4_verification,
                data_sources,
                website_content_hash,
                processing_attempts,
                created_at,
                updated_at,
                puget_sound
            FROM contractors 
            WHERE review_status IN ('approved_download', 'pending_review')
            ORDER BY review_status, business_name
        """)
        
        return [dict(row) for row in contractors]
    
    async def get_unexported_ready_contractors(self) -> List[Dict[str, Any]]:
        """Get contractors ready for download that haven't been exported yet (approved_download AND pending_review)"""
        contractors = await self.db_pool.fetch("""
            SELECT 
                id,
                uuid,
                business_name,
                contractor_license_number,
                contractor_license_type_code,
                contractor_license_type_code_desc,
                address1,
                address2,
                city,
                state,
                zip,
                phone_number,
                license_effective_date,
                license_expiration_date,
                business_type_code,
                business_type_code_desc,
                specialty_code1,
                specialty_code1_desc,
                specialty_code2,
                specialty_code2_desc,
                ubi,
                primary_principal_name,
                status_code,
                contractor_license_status,
                contractor_license_suspend_date,
                mailer_category,
                priority_category,
                website_url,
                website_status,
                business_description,
                tagline,
                established_year,
                years_in_business,
                services_offered,
                service_categories,
                specializations,
                additional_licenses,
                certifications,
                insurance_types,
                website_email,
                website_phone,
                physical_address,
                social_media_urls,
                residential_focus,
                commercial_focus,
                emergency_services,
                free_estimates,
                warranty_offered,
                confidence_score,
                classification_confidence,
                website_confidence,
                processing_status,
                last_processed,
                error_message,
                manual_review_needed,
                manual_review_reason,
                review_status,
                reviewed_by,
                reviewed_at,
                review_notes,
                manual_review_outcome,
                marked_for_download,
                marked_for_download_at,
                exported_at,
                export_batch_id,
                gpt4mini_analysis,
                gpt4_verification,
                data_sources,
                website_content_hash,
                processing_attempts,
                created_at,
                updated_at,
                puget_sound
            FROM contractors 
            WHERE review_status IN ('approved_download', 'pending_review') AND exported_at IS NULL
            ORDER BY review_status, business_name
        """)
        
        return [dict(row) for row in contractors]
    
    def prepare_csv_data(self, contractors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare contractor data for CSV export"""
        csv_data = []
        
        for contractor in contractors:
            # Format array fields as comma-separated strings
            array_fields = ['services_offered', 'service_categories', 'specializations', 
                          'additional_licenses', 'certifications', 'insurance_types']
            
            # Clean up None values and format data
            row = {}
            for key, value in contractor.items():
                if key == 'id':  # Skip internal ID
                    continue
                elif key in array_fields:
                    if isinstance(value, list):
                        row[key] = ', '.join(str(item) for item in value)
                    else:
                        row[key] = str(value) if value else ''
                elif key in ['gpt4mini_analysis', 'gpt4_verification', 'data_sources', 'social_media_urls']:
                    # Convert JSONB fields to JSON strings
                    if value is not None:
                        import json
                        row[key] = json.dumps(value)
                    else:
                        row[key] = ''
                elif value is None:
                    row[key] = ''
                else:
                    row[key] = str(value)
            
            csv_data.append(row)
        
        return csv_data
    
    async def export_to_csv(self, contractors: List[Dict[str, Any]], filename: str, exported_by: str) -> str:
        """Export contractors to CSV file with database tracking"""
        if not contractors:
            logger.warning("No contractors to export")
            return None
        
        # Prepare CSV data
        csv_data = self.prepare_csv_data(contractors)
        
        # Create file path
        file_path = self.export_dir / filename
        
        # Write CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        # Create export batch record
        batch_id = await self.create_export_batch(
            exported_by=exported_by,
            contractor_count=len(contractors),
            file_path=str(file_path)
        )
        
        # Mark contractors as exported
        contractor_ids = [c['id'] for c in contractors]
        await self.mark_contractors_as_exported(contractor_ids, batch_id)
        
        logger.info(f"Exported {len(contractors)} contractors to {file_path}")
        return str(file_path)
    
    async def retroactively_track_existing_export(self, csv_file_path: str, exported_by: str = "system"):
        """Retroactively track an existing export that wasn't tracked in the database"""
        file_path = Path(csv_file_path)
        
        if not file_path.exists():
            logger.error(f"CSV file not found: {csv_file_path}")
            return False
        
        # Read the CSV to get the contractor names that were exported
        exported_names = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                exported_names.append(row['business_name'])
        
        logger.info(f"Found {len(exported_names)} contractors in existing CSV")
        
        # Find matching contractors in database
        contractors = await self.db_pool.fetch("""
            SELECT id, business_name 
            FROM contractors 
            WHERE business_name = ANY($1) AND review_status IN ('approved_download', 'pending_review')
        """, exported_names)
        
        if not contractors:
            logger.warning("No matching contractors found in database")
            return False
        
        # Create export batch record
        batch_id = await self.create_export_batch(
            exported_by=exported_by,
            contractor_count=len(contractors),
            file_path=str(file_path)
        )
        
        # Mark contractors as exported
        contractor_ids = [c['id'] for c in contractors]
        await self.mark_contractors_as_exported(contractor_ids, batch_id)
        
        logger.info(f"Retroactively tracked {len(contractors)} contractors from {csv_file_path}")
        return True
    
    async def get_export_summary(self):
        """Get summary of all exports"""
        batches = await self.db_pool.fetch("""
            SELECT 
                batch_id,
                export_date,
                exported_by,
                contractor_count,
                file_path,
                download_count,
                status
            FROM export_batches
            ORDER BY export_date DESC
        """)
        
        total_exported = await self.db_pool.fetchval("""
            SELECT COUNT(*) FROM contractors WHERE exported_at IS NOT NULL
        """)
        
        return {
            'batches': [dict(batch) for batch in batches],
            'total_exported': total_exported
        }


async def main():
    """Main export function"""
    parser = argparse.ArgumentParser(description='Export contractor data with tracking')
    parser.add_argument('--filename', '-f', default=None,
                       help='Output filename (default: auto-generated)')
    parser.add_argument('--exported-by', '-u', default='system',
                       help='Username of person doing export (default: system)')
    parser.add_argument('--unexported-only', '-n', action='store_true',
                       help='Only export contractors that haven\'t been exported yet')
    parser.add_argument('--track-existing', '-t', 
                       help='Retroactively track an existing CSV file')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Show export summary and exit')
    
    args = parser.parse_args()
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        return False
    
    # Connect to database
    db_pool = await asyncpg.create_pool(config.database_url, min_size=1, max_size=5)
    exporter = ContractorExporter(db_pool)
    
    try:
        if args.summary:
            # Show export summary
            summary = await exporter.get_export_summary()
            print(f"\n📊 Export Summary:")
            print(f"Total exported contractors: {summary['total_exported']}")
            print(f"Export batches: {len(summary['batches'])}")
            
            if summary['batches']:
                print(f"\nRecent exports:")
                for batch in summary['batches'][:5]:  # Show last 5
                    print(f"  Batch {batch['batch_id']}: {batch['contractor_count']} contractors on {batch['export_date']}")
                    print(f"    File: {batch['file_path']}")
                    print(f"    By: {batch['exported_by']}")
            
            return True
        
        elif args.track_existing:
            # Retroactively track existing export
            success = await exporter.retroactively_track_existing_export(
                args.track_existing, 
                args.exported_by
            )
            if success:
                print(f"✅ Successfully tracked existing export: {args.track_existing}")
            else:
                print(f"❌ Failed to track existing export: {args.track_existing}")
            return success
        
        else:
            # Regular export
            if args.unexported_only:
                contractors = await exporter.get_unexported_ready_contractors()
                suffix = "new"
            else:
                contractors = await exporter.get_ready_contractors()
                suffix = "all"
            
            if not contractors:
                print("No contractors ready for export")
                return True
            
            # Generate filename if not provided
            if not args.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                args.filename = f"ready_contractors_{suffix}_{timestamp}.csv"
            
            # Export contractors
            file_path = await exporter.export_to_csv(
                contractors, 
                args.filename, 
                args.exported_by
            )
            
            if file_path:
                print(f"✅ Exported {len(contractors)} contractors to: {file_path}")
                
                # Show summary
                summary = await exporter.get_export_summary()
                print(f"📊 Total contractors exported across all batches: {summary['total_exported']}")
            else:
                print("❌ Export failed")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False
    
    finally:
        await db_pool.close()


if __name__ == "__main__":
    if not asyncio.run(main()):
        sys.exit(1)