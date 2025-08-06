#!/usr/bin/env python3
"""
Processing orchestrator for contractor enrichment pipeline
"""
import asyncio
import logging
import argparse
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from src.database.connection import db_pool
from src.services.contractor_service import ContractorService
from src.services.export_service import ExportService
from src.utils.logging_utils import contractor_logger
from src.services.contractor_service import QuotaExceededError, quota_tracker

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """Orchestrates the contractor processing and export pipeline"""
    
    def __init__(self, processes: int = 3, puget_sound_only: bool = True):
        self.processes = processes
        self.puget_sound_only = puget_sound_only
        self.contractor_service = ContractorService()
        self.export_service = ExportService()
        self.processed_count = 0
        self.exported_count = 0
        self.start_time = None
        self.end_time = None
    
    async def initialize(self):
        """Initialize the system"""
        logger.info("Initializing Processing Orchestrator...")
        
        # Validate configuration
        if not config.validate():
            raise RuntimeError("Configuration validation failed")
        
        # Initialize database pool
        await db_pool.initialize()
        
        logger.info("System initialization completed")
    
    async def get_contractors(self, limit: int) -> List[Any]:
        """Get contractors to process with optional Puget Sound filtering"""
        if self.puget_sound_only:
            # Get Puget Sound contractors only (ACTIVE only)
            query = """
                SELECT * FROM contractors 
                WHERE processing_status = 'pending' 
                AND puget_sound = TRUE
                AND status_code = 'A'
                ORDER BY id 
                LIMIT $1
            """
        else:
            # Get all contractors (ACTIVE only)
            query = """
                SELECT * FROM contractors 
                WHERE processing_status = 'pending'
                AND status_code = 'A'
                ORDER BY id 
                LIMIT $1
            """
        
        rows = await db_pool.fetch(query, limit)
        contractors = []
        for row in rows:
            contractor_data = dict(row)
            # Remove puget_sound field if it exists to avoid model issues
            contractor_data.pop('puget_sound', None)
            contractors.append(contractor_data)
        
        logger.info(f"Found {len(contractors)} contractors to process")
        if self.puget_sound_only:
            logger.info("   (ACTIVE Puget Sound contractors only)")
        else:
            logger.info("   (ACTIVE contractors only)")
        
        return contractors
    
    async def process_contractor_chunk(self, contractors: List[Dict], chunk_id: int) -> Dict[str, Any]:
        """Process a chunk of contractors in a single process"""
        service = ContractorService()
        results = {
            'chunk_id': chunk_id,
            'total': len(contractors),
            'completed': 0,
            'failed': 0,
            'quota_exceeded': False,
            'start_time': time.time(),
            'end_time': None
        }
        
        try:
            for i, contractor_data in enumerate(contractors):
                try:
                    # Check quota before processing each contractor
                    if quota_tracker.is_quota_exceeded():
                        results['quota_exceeded'] = True
                        logger.info(f"🛑 Process {chunk_id}: Daily quota exceeded - stopping chunk")
                        break
                    
                    # Create contractor object
                    from src.database.models import Contractor
                    contractor = Contractor.from_dict(contractor_data)
                    
                    # Process contractor
                    await service.process_contractor(contractor)
                    results['completed'] += 1
                    
                    # Log progress every 10 contractors
                    if (i + 1) % 10 == 0:
                        quota_status = quota_tracker.get_quota_status()
                        logger.info(f"📊 Process {chunk_id}: {i + 1}/{len(contractors)} completed | "
                                  f"Queries: {quota_status['queries_today']:,}/{quota_status['daily_limit']:,}")
                    
                except QuotaExceededError:
                    results['quota_exceeded'] = True
                    logger.info(f"🛑 Process {chunk_id}: Daily quota exceeded - stopping chunk")
                    break
                except Exception as e:
                    logger.error(f"❌ Process {chunk_id}: Error processing {contractor_data.get('business_name', 'Unknown')}: {e}")
                    results['failed'] += 1
        
        except Exception as e:
            logger.error(f"❌ Process {chunk_id}: Fatal error: {e}")
            results['failed'] = len(contractors) - results['completed']
        
        finally:
            results['end_time'] = time.time()
            await service.close()
        
        return results
    
    async def process_contractors(self, target_count: int = None, batch_size: int = None):
        """Process contractors through the enrichment pipeline with parallel processing"""
        if batch_size is None:
            batch_size = config.BATCH_SIZE
            
        logger.info(f"Starting contractor processing (target: {target_count or 'all'}, batch size: {batch_size}, processes: {self.processes})")
        logger.info(f"Region filter: {'Puget Sound only' if self.puget_sound_only else 'All contractors'}")
        
        self.start_time = time.time()
        
        # Get contractors to process
        contractors = await self.get_contractors(target_count or batch_size)
        if not contractors:
            logger.info("No contractors found to process")
            return 0
        
        # Split contractors into chunks for parallel processing
        chunk_size = len(contractors) // self.processes
        chunks = []
        for i in range(self.processes):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.processes - 1 else len(contractors)
            chunks.append(contractors[start_idx:end_idx])
        
        logger.info(f"🔄 Starting parallel processing with {self.processes} processes...")
        logger.info(f"   - Chunk sizes: {[len(chunk) for chunk in chunks]}")
        
        # Process chunks in parallel
        tasks = []
        for i, chunk in enumerate(chunks):
            if chunk:  # Only create task if chunk has contractors
                task = asyncio.create_task(self.process_contractor_chunk(chunk, i + 1))
                tasks.append(task)
        
        # Wait for all tasks to complete
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        total_completed = 0
        total_failed = 0
        quota_exceeded = False
        
        for i, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Process {i + 1}: Exception: {result}")
                total_failed += len(chunks[i]) if i < len(chunks) else 0
            else:
                total_completed += result['completed']
                total_failed += result['failed']
                if result['quota_exceeded']:
                    quota_exceeded = True
                
                duration = result['end_time'] - result['start_time']
                logger.info(f"✅ Process {i + 1}: {result['completed']} completed, {result['failed']} failed "
                          f"({duration:.1f}s)")
        
        self.end_time = time.time()
        self.processed_count = total_completed
        
        # Print final results
        logger.info(f"📊 Final Results:")
        logger.info(f"   - Total completed: {total_completed:,}")
        logger.info(f"   - Total failed: {total_failed:,}")
        logger.info(f"   - Success rate: {total_completed / (total_completed + total_failed) * 100:.1f}%")
        logger.info(f"   - Total time: {(self.end_time - self.start_time) / 60:.1f} minutes")
        
        # Check quota status
        quota_status = quota_tracker.get_quota_status()
        logger.info(f"   - Queries used: {quota_status['queries_today']:,}/{quota_status['daily_limit']:,}")
        logger.info(f"   - Remaining queries: {quota_status['remaining_queries']:,}")
        
        if quota_exceeded:
            logger.info("🛑 Processing stopped due to daily Google API quota exceeded")
            logger.info("   Please wait until tomorrow to continue processing")
        
        return total_completed
    
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
    parser.add_argument('--processes', '-p', type=int, default=3, help='Number of parallel processes (default: 3)')
    parser.add_argument('--all', action='store_true', help='Process all ACTIVE contractors (overrides default Puget Sound filter)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set puget_sound_only based on --all flag
    puget_sound_only = not args.all
    
    orchestrator = ProcessingOrchestrator(
        processes=args.processes,
        puget_sound_only=puget_sound_only
    )
    
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