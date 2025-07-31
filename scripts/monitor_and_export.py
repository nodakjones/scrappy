#!/usr/bin/env python3
"""
Monitor processing completion and auto-export results
"""
import asyncio
import subprocess
import time
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database.connection import DatabasePool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_completion_and_export():
    """Check if processing is complete and export if ready"""
    db = DatabasePool()
    await db.initialize()
    
    try:
        # Check if processing is complete (5000 records processed)
        completed = await db.pool.fetchval(
            'SELECT COUNT(*) FROM contractors WHERE processing_status = $1', 
            'completed'
        )
        
        # Check if background process is still running
        result = subprocess.run(['pgrep', '-f', 'run_processing.py'], 
                              capture_output=True, text=True)
        process_running = bool(result.stdout.strip())
        
        ready_for_export = await db.pool.fetchval('''
            SELECT COUNT(*) FROM contractors 
            WHERE processing_status = 'completed' 
            AND review_status = 'approved_download'
            AND exported_at IS NULL
        ''')
        
        logger.info(f"Status: {completed}/5000 processed, {ready_for_export} ready for export, process running: {process_running}")
        
        # Export if we have records ready and either completed 5000 or process stopped
        if ready_for_export > 0 and (completed >= 5000 or not process_running):
            logger.info(f"🎯 Processing complete! Exporting {ready_for_export} records...")
            
            # Generate export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contractors_batch_{timestamp}.csv"
            
            # Run export
            export_cmd = [
                'python3', 'scripts/export_contractors.py',
                '--unexported-only',
                '--exported-by', 'auto_monitor',
                '--filename', filename
            ]
            
            result = subprocess.run(export_cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            if result.returncode == 0:
                logger.info(f"✅ Export successful: {filename}")
                
                # Commit and push to git
                git_commands = [
                    ['git', 'add', f'exports/{filename}'],
                    ['git', 'commit', '-m', f'Export {ready_for_export} processed contractors - batch complete'],
                    ['git', 'push', 'origin', 'cursor/export-previous-records-again-e478']
                ]
                
                for cmd in git_commands:
                    git_result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
                    if git_result.returncode == 0:
                        logger.info(f"✅ Git command successful: {' '.join(cmd)}")
                    else:
                        logger.error(f"❌ Git command failed: {' '.join(cmd)}")
                        logger.error(git_result.stderr)
                
                logger.info("🎉 Processing and export complete!")
                return True
            else:
                logger.error(f"❌ Export failed: {result.stderr}")
                return False
        
        return False
        
    finally:
        await db.close()

async def monitor_loop():
    """Main monitoring loop"""
    logger.info("🔍 Starting processing monitor...")
    
    while True:
        try:
            completed = await check_completion_and_export()
            if completed:
                logger.info("✅ Monitoring complete - processing finished and exported!")
                break
                
            # Wait 5 minutes before checking again
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    asyncio.run(monitor_loop())