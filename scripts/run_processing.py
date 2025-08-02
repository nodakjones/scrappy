#!/usr/bin/env python3
"""
Processing orchestrator for contractor enrichment pipeline
"""
import asyncio
import logging
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.services.export_service import ExportService
from src.utils.logging_utils import contractor_logger

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
        contractor_logger.log_periodic_stats(initial_stats)
        
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
                
                # Log batch progress with logging
                contractor_logger.log_batch_progress(batch_number, total_processed, batch_results)
                
                logger.info(f"Batch {batch_number} completed: {batch_results}")
                logger.info(f"Total processed so far: {total_processed}")
                
                # Log periodic stats every 5 batches
                if batch_number % 5 == 0:
                    current_stats = await self.contractor_service.get_processing_stats()
                    contractor_logger.log_periodic_stats(current_stats)
                
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
        contractor_logger.log_periodic_stats(final_stats)
        
        return total_processed
    
    async def get_system_status(self):
        """Get current system status"""
        try:
            # Get processing stats
            stats = await self.contractor_service.get_processing_stats()
            
            # Get logger stats
            logger_stats = contractor_logger.get_stats()
            
            return {
                'processing_stats': stats,
                'logger_stats': logger_stats,
                'config': {
                    'batch_size': config.BATCH_SIZE,
                    'max_concurrent_crawls': config.MAX_CONCURRENT_CRAWLS,
                    'auto_approve_threshold': config.AUTO_APPROVE_THRESHOLD
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    async def shutdown(self):
        """Shutdown the system gracefully"""
        logger.info("Shutting down system...")
        
        # Close contractor service
        await self.contractor_service.close()
        
        # Close database pool
        await db_pool.close()
        
        logger.info("System shutdown completed")


async def main():
    """Main processing function"""
    parser = argparse.ArgumentParser(description='Process contractors through enrichment pipeline')
    parser.add_argument('--count', '-c', type=int, help='Number of contractors to process')
    parser.add_argument('--batch-size', '-b', type=int, help='Batch size for processing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    orchestrator = ProcessingOrchestrator()
    
    try:
        # Initialize system
        await orchestrator.initialize()
        
        # Process contractors
        processed_count = await orchestrator.process_contractors(
            target_count=args.count,
            batch_size=args.batch_size
        )
        
        print(f"✅ Processing completed: {processed_count} contractors processed")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())