#!/usr/bin/env python3
"""
Main processing script for contractor enrichment system
Orchestrates the complete pipeline: data processing -> export
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.services.export_service import ExportService

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """Orchestrates the contractor processing and export pipeline"""
    
    def __init__(self):
        self.contractor_service = ContractorService()
        self.export_service = ExportService()
        self.processed_count = 0
        self.exported_count = 0
    
    async def initialize(self):
        """Initialize the system"""
        logger.info("Initializing Processing Orchestrator...")
        
        # Validate configuration
        if not config.validate():
            raise RuntimeError("Configuration validation failed")
        
        # Initialize database pool
        await db_pool.initialize()
        
        logger.info("System initialization completed")
    
    async def process_contractors(self, target_count: int = None, batch_size: int = None):
        """Process contractors through the enrichment pipeline"""
        if batch_size is None:
            batch_size = config.BATCH_SIZE
            
        logger.info(f"Starting contractor processing (target: {target_count or 'all'}, batch size: {batch_size})")
        
        # Get initial stats
        initial_stats = await self.contractor_service.get_processing_stats()
        logger.info(f"Initial processing stats: {initial_stats}")
        
        total_processed = 0
        batch_number = 1
        
        while True:
            # Calculate remaining count for this batch
            remaining_count = None
            if target_count:
                remaining_count = target_count - total_processed
                if remaining_count <= 0:
                    logger.info(f"Target count of {target_count} reached")
                    break
                batch_limit = min(batch_size, remaining_count)
            else:
                batch_limit = batch_size
            
            # Get pending contractors
            contractors = await self.contractor_service.get_pending_contractors(limit=batch_limit)
            
            if not contractors:
                logger.info("No more pending contractors to process")
                break
            
            logger.info(f"Processing batch {batch_number} with {len(contractors)} contractors")
            
            # Process the batch
            try:
                batch_results = await self.contractor_service.process_batch(contractors)
                total_processed += batch_results['processed']
                
                logger.info(f"Batch {batch_number} completed: {batch_results}")
                logger.info(f"Total processed so far: {total_processed}")
                
                # Add delay between batches if configured
                if hasattr(config, 'BATCH_PROCESSING_DELAY') and config.BATCH_PROCESSING_DELAY > 0:
                    logger.info(f"Waiting {config.BATCH_PROCESSING_DELAY}s before next batch...")
                    await asyncio.sleep(config.BATCH_PROCESSING_DELAY)
                
                batch_number += 1
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_number}: {e}")
                # Continue with next batch rather than failing completely
                break
        
        self.processed_count = total_processed
        logger.info(f"Processing completed. Total contractors processed: {total_processed}")
        
        # Get final stats
        final_stats = await self.contractor_service.get_processing_stats()
        logger.info(f"Final processing stats: {final_stats}")
        
        return total_processed
    
    async def get_system_status(self):
        """Get current system status and statistics"""
        logger.info("Getting system status...")
        
        # Processing stats
        processing_stats = await self.contractor_service.get_processing_stats()
        
        # Export stats  
        export_stats = await self.export_service.get_export_stats()
        
        # Export files
        export_files = self.export_service.list_export_files()
        
        status = {
            'processing_stats': processing_stats,
            'export_stats': export_stats, 
            'export_files': export_files[:5],  # Show latest 5 files only
            'timestamp': datetime.now().isoformat()
        }
        
        return status
    
    async def shutdown(self):
        """Clean shutdown"""
        logger.info("Shutting down...")
        await db_pool.close()
        logger.info("Shutdown completed")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run contractor enrichment processing')
    parser.add_argument('--count', '-c', type=int, default=None,
                       help='Number of contractors to process (default: all pending)')
    parser.add_argument('--batch-size', '-b', type=int, default=None,
                       help='Batch size for processing (default: from config)')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    orchestrator = ProcessingOrchestrator()
    
    try:
        await orchestrator.initialize()
        
        if args.status:
            # Show status and exit
            status = await orchestrator.get_system_status()
            print("\n=== SYSTEM STATUS ===")
            print(f"Processing Stats: {status['processing_stats']}")
            print(f"Export Stats: {status['export_stats']}")
            print(f"Recent Export Files: {len(status['export_files'])}")
            for file_info in status['export_files']:
                print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")
            return 0
        
        else:
            # Process contractors
            count = await orchestrator.process_contractors(
                target_count=args.count,
                batch_size=args.batch_size
            )
            print(f"\n✅ Processing completed: {count} contractors processed")
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        return 1
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1
    finally:
        await orchestrator.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))