"""
Export service for generating CSV files from processed contractors
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..database.connection import db_pool
from ..database.models import Contractor
from ..config import config

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting processed contractor data to CSV"""
    
    def __init__(self):
        self.export_dir = Path(config.EXPORT_DIR)
        self.export_dir.mkdir(exist_ok=True)
    
    async def get_exportable_contractors(self, limit: int = None) -> List[Contractor]:
        """Get contractors ready for export (completed or approved)"""
        query = """
        SELECT * FROM contractors 
        WHERE processing_status IN ('completed', 'approved')
        AND (exported_at IS NULL OR exported_at < updated_at)
        ORDER BY confidence_score DESC, updated_at ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        rows = await db_pool.fetch(query)
        
        contractors = []
        for row in rows:
            contractor = Contractor.from_dict(dict(row))
            contractors.append(contractor)
            
        logger.info(f"Found {len(contractors)} contractors ready for export")
        return contractors
    
    async def export_to_csv(self, contractors: List[Contractor], filename: str = None) -> str:
        """Export contractors to CSV file"""
        if not contractors:
            logger.warning("No contractors to export")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contractor_export_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Define CSV columns (original + enriched data)
        columns = [
            # Original contractor data
            'id',
            'business_name',
            'contractor_license_number',
            'contractor_license_type_code',
            'contractor_license_type_code_desc',
            'address1',
            'address2', 
            'city',
            'state',
            'zip',
            'phone_number',
            'license_effective_date',
            'license_expiration_date',
            'business_type_code',
            'business_type_code_desc',
            'specialty_code1',
            'specialty_code1_desc',
            'specialty_code2',
            'specialty_code2_desc',
            'ubi',
            'primary_principal_name',
            'status_code',
            'contractor_license_status',
            'contractor_license_suspend_date',
            
            # Enriched data
            'is_home_contractor',
            'mailer_category',
            'priority_category',
            'website_url',
            'website_status',
            'business_description',
            'tagline',
            'established_year',
            'years_in_business',
            'services_offered',
            'service_categories',
            'specializations',
            'website_email',
            'website_phone',
            'physical_address',
            'residential_focus',
            'commercial_focus',
            'emergency_services',
            'free_estimates',
            'warranty_offered',
            
            # Quality metrics
            'confidence_score',
            'classification_confidence',  
            'website_confidence',
            'processing_status',
            'last_processed',
            'manual_review_needed',
            'manual_review_reason',
            'review_status',
            'reviewed_by',
            'reviewed_at'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                
                for contractor in contractors:
                    row = {}
                    for column in columns:
                        value = getattr(contractor, column, None)
                        
                        # Format special data types
                        if isinstance(value, datetime):
                            row[column] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(value, list):
                            row[column] = ', '.join(str(item) for item in value) if value else ''
                        elif isinstance(value, dict):
                            row[column] = str(value) if value else ''
                        elif value is None:
                            row[column] = ''
                        else:
                            row[column] = str(value)
                    
                    writer.writerow(row)
            
            # Mark contractors as exported
            await self.mark_as_exported(contractors, filename)
            
            logger.info(f"Successfully exported {len(contractors)} contractors to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    async def mark_as_exported(self, contractors: List[Contractor], filename: str):
        """Mark contractors as exported in the database"""
        contractor_ids = [c.id for c in contractors]
        
        if not contractor_ids:
            return
            
        # Create export batch record
        batch_query = """
        INSERT INTO export_batches (export_date, exported_by, contractor_count, file_path, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING batch_id
        """
        
        try:
            batch_id = await db_pool.fetchval(
                batch_query,
                datetime.utcnow(),
                'system',
                len(contractors),
                filename,
                'completed'
            )
        except Exception:
            # If export_batches table doesn't exist, just continue
            batch_id = None
            logger.warning("export_batches table not found, skipping batch tracking")
        
        # Update contractors
        update_query = """
        UPDATE contractors 
        SET exported_at = $1, export_batch_id = $2, updated_at = $3
        WHERE id = ANY($4)
        """
        
        await db_pool.execute(
            update_query,
            datetime.utcnow(),
            batch_id,
            datetime.utcnow(),
            contractor_ids
        )
        
        logger.info(f"Marked {len(contractor_ids)} contractors as exported")
    
    async def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics"""
        stats = {}
        
        # Total contractors by status
        status_query = """
        SELECT processing_status, COUNT(*) as count
        FROM contractors
        GROUP BY processing_status
        """
        
        rows = await db_pool.fetch(status_query)
        stats['by_status'] = {row['processing_status']: row['count'] for row in rows}
        
        # Export readiness
        ready_query = """
        SELECT COUNT(*) as ready_count
        FROM contractors
        WHERE processing_status IN ('completed', 'approved')
        AND (exported_at IS NULL OR exported_at < updated_at)
        """
        
        ready_count = await db_pool.fetchval(ready_query)
        stats['ready_for_export'] = ready_count
        
        # Already exported
        exported_query = """
        SELECT COUNT(*) as exported_count
        FROM contractors  
        WHERE exported_at IS NOT NULL
        """
        
        exported_count = await db_pool.fetchval(exported_query)
        stats['already_exported'] = exported_count
        
        return stats
    
    def list_export_files(self) -> List[Dict[str, Any]]:
        """List existing export files"""
        files = []
        
        for file_path in self.export_dir.glob("*.csv"):
            stat = file_path.stat()
            files.append({
                'filename': file_path.name,
                'filepath': str(file_path),
                'size_bytes': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
        
        # Sort by creation time, newest first
        files.sort(key=lambda x: x['created'], reverse=True)
        return files
    
    async def create_summary_export(self, contractors: List[Contractor], filename: str = None) -> str:
        """Create a summary CSV with key fields only"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contractor_summary_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Summary columns for quick review
        columns = [
            'id',
            'business_name',
            'city',
            'state', 
            'phone_number',
            'contractor_license_number',
            'is_home_contractor',
            'mailer_category',
            'website_url',
            'confidence_score',
            'processing_status',
            'last_processed'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for contractor in contractors:
                row = {}
                for column in columns:
                    value = getattr(contractor, column, None)
                    
                    if isinstance(value, datetime):
                        row[column] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif value is None:
                        row[column] = ''
                    else:
                        row[column] = str(value)
                
                writer.writerow(row)
        
        logger.info(f"Created summary export with {len(contractors)} contractors: {filepath}")
        return str(filepath)