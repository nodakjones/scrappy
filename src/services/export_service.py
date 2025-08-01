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