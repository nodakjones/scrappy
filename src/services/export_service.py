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
    
    async def export_to_csv(self, contractors: List[Contractor], filename_prefix: str = "contractor_export") -> str:
        """Export contractors to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_full_{timestamp}.csv"
        filepath = self.export_dir / filename
        
        # Define columns for full export
        columns = [
            'id', 'business_name', 'phone_number', 'address1', 'address2', 'city', 'state', 'zip',
            'website_url', 'confidence_score', 'residential_focus', 'mailer_category',
            'contractor_license_type_code_desc', 'processing_status', 'last_processed'
        ]
        
        logger.info(f"Exporting {len(contractors)} contractors to {filename}")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for contractor in contractors:
                row = {}
                for col in columns:
                    value = getattr(contractor, col, None)
                    
                    # Format values appropriately
                    if value is None:
                        row[col] = ''
                    elif isinstance(value, datetime):
                        row[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, (dict, list)):
                        row[col] = str(value)
                    else:
                        row[col] = str(value)
                
                writer.writerow(row)
        
        logger.info(f"Export completed: {filepath}")
        return str(filepath)
    
    async def create_summary_export(self, contractors: List[Contractor], filename_prefix: str = "contractor_export") -> str:
        """Create a summary CSV with key fields only"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_summary_{timestamp}.csv"
        filepath = self.export_dir / filename
        
        # Define columns for summary export
        columns = [
            'business_name', 'phone_number', 'address1', 'address2', 'city', 'state', 'website_url', 
            'confidence_score', 'residential_focus', 'mailer_category'
        ]
        
        logger.info(f"Creating summary export with {len(contractors)} contractors to {filename}")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for contractor in contractors:
                row = {}
                for col in columns:
                    value = getattr(contractor, col, None)
                    
                    # Format values
                    if value is None:
                        row[col] = ''
                    elif isinstance(value, datetime):
                        row[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif col == 'confidence_score' and value is not None:
                        row[col] = f"{float(value):.3f}"
                    else:
                        row[col] = str(value)
                
                writer.writerow(row)
        
        logger.info(f"Summary export completed: {filepath}")
        return str(filepath)
    
    async def mark_as_exported(self, contractors: List[Contractor], batch_id: str = None):
        """Mark contractors as exported in database"""
        if not contractors:
            return
        
        export_time = datetime.utcnow()
        if batch_id is None:
            batch_id = f"batch_{export_time.strftime('%Y%m%d_%H%M%S')}"
        
        contractor_ids = [c.id for c in contractors]
        
        # Update contractors table
        update_query = """
        UPDATE contractors 
        SET exported_at = $1, export_batch_id = $2, updated_at = $1
        WHERE id = ANY($3)
        """
        
        await db_pool.execute(update_query, export_time, batch_id, contractor_ids)
        
        # Try to create export batch record (table might not exist)
        try:
            batch_query = """
            INSERT INTO export_batches (batch_id, export_time, contractor_count, export_type)
            VALUES ($1, $2, $3, $4)
            """
            await db_pool.execute(batch_query, batch_id, export_time, len(contractors), 'csv')
        except Exception as e:
            logger.warning(f"Could not create export_batches record: {e}")
        
        logger.info(f"Marked {len(contractors)} contractors as exported with batch_id: {batch_id}")
        return batch_id