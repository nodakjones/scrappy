#!/usr/bin/env python3
"""
Parallel Contractor Processing Test Suite
=======================================

Process contractors in parallel with multiple processes for faster processing.
Optimized for daily Puget Sound processing with Google API limits.

USAGE:
    python scripts/run_parallel_test.py --limit 5000 --processes 3

OPTIONS:
    --limit N        Number of contractors to process (default: 5000)
    --processes N    Number of parallel processes (default: 3)
    --all           Process all ACTIVE contractors (overrides default Puget Sound filter)
    --show-details   Show detailed results table (default: summary only)
    --help          Show this help message

EXAMPLES:
    # Run 5000 ACTIVE Puget Sound contractors with 3 parallel processes (default)
    python scripts/run_parallel_test.py
    
    # Run 1000 ACTIVE Puget Sound contractors with 2 parallel processes
    python scripts/run_parallel_test.py --limit 1000 --processes 2
    
    # Run 5000 all ACTIVE contractors with 3 parallel processes
    python scripts/run_parallel_test.py --all
    
    # Run 100 ACTIVE contractors for testing
    python scripts/run_parallel_test.py --limit 100 --processes 1
"""

import asyncio
import multiprocessing
import argparse
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.database.models import Contractor
from src.services.contractor_service import ContractorService, QuotaExceededError, quota_tracker

class ParallelTestSuite:
    def __init__(self, limit: int = 5000, processes: int = 3, puget_sound_only: bool = True):
        self.limit = limit
        self.processes = processes
        self.puget_sound_only = puget_sound_only
        self.service = ContractorService()
        self.start_time = None
        self.end_time = None
        
    async def initialize(self):
        """Initialize the test suite"""
        print(f"🚀 Parallel Contractor Processing Test Suite")
        print(f"📊 Configuration:")
        print(f"   - Batch size: {self.limit:,} contractors")
        print(f"   - Parallel processes: {self.processes}")
        print(f"   - Status filter: ACTIVE contractors only")
        print(f"   - Region filter: {'Puget Sound only' if self.puget_sound_only else 'All contractors'}")
        print(f"   - Google API quota: 10,000 queries/day")
        print(f"   - Estimated processing time: ~{self.limit // 1000 * 2} hours")
        print()
        
        # Check quota status
        quota_status = quota_tracker.get_quota_status()
        print(f"📈 Current Google API Status:")
        print(f"   - Queries used today: {quota_status['queries_today']:,}")
        print(f"   - Remaining queries: {quota_status['remaining_queries']:,}")
        print(f"   - Consecutive 429 errors: {quota_status['consecutive_429_errors']}")
        print(f"   - Quota exceeded: {'Yes' if quota_status['quota_exceeded'] else 'No'}")
        print()
        
        if quota_status['quota_exceeded']:
            print("❌ Daily Google API quota exceeded - cannot process more contractors today")
            print("   Please wait until tomorrow to continue processing")
            return False
        
        if quota_status['remaining_queries'] < self.limit * 2:
            print(f"⚠️  Warning: Only {quota_status['remaining_queries']:,} queries remaining")
            print(f"   This batch requires ~{self.limit * 2:,} queries")
            print(f"   Consider reducing batch size or waiting until tomorrow")
            print()
        
        return True
    
    async def get_contractors(self) -> List[Contractor]:
        """Get contractors to process"""
        # Initialize database pool
        await db_pool.initialize()
        
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
        
        rows = await db_pool.fetch(query, self.limit)
        contractors = [Contractor(**row) for row in rows]
        
        print(f"📋 Found {len(contractors):,} contractors to process")
        if self.puget_sound_only:
            print(f"   (ACTIVE Puget Sound contractors only)")
        else:
            print(f"   (ACTIVE contractors only)")
        print()
        
        return contractors
    
    async def process_contractor_chunk(self, contractors: List[Contractor], chunk_id: int) -> Dict[str, Any]:
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
            for i, contractor in enumerate(contractors):
                try:
                    # Check quota before processing each contractor
                    if quota_tracker.is_quota_exceeded():
                        results['quota_exceeded'] = True
                        print(f"🛑 Process {chunk_id}: Daily quota exceeded - stopping chunk")
                        break
                    
                    # Process contractor
                    await service.process_contractor(contractor)
                    results['completed'] += 1
                    
                    # Log progress every 10 contractors
                    if (i + 1) % 10 == 0:
                        quota_status = quota_tracker.get_quota_status()
                        print(f"📊 Process {chunk_id}: {i + 1}/{len(contractors)} completed | "
                              f"Queries: {quota_status['queries_today']:,}/{quota_status['daily_limit']:,}")
                    
                except QuotaExceededError:
                    results['quota_exceeded'] = True
                    print(f"🛑 Process {chunk_id}: Daily quota exceeded - stopping chunk")
                    break
                except Exception as e:
                    print(f"❌ Process {chunk_id}: Error processing {contractor.business_name}: {e}")
                    results['failed'] += 1
                    contractor.processing_status = 'failed'
                    contractor.error_message = str(e)
                    await service.update_contractor(contractor)
        
        except Exception as e:
            print(f"❌ Process {chunk_id}: Fatal error: {e}")
            results['failed'] = len(contractors) - results['completed']
        
        finally:
            results['end_time'] = time.time()
            await service.close()
        
        return results
    
    async def run_parallel_batch_test(self):
        """Run the parallel batch test"""
        self.start_time = time.time()
        
        # Get contractors to process
        contractors = await self.get_contractors()
        if not contractors:
            print("❌ No contractors found to process")
            return
        
        # Split contractors into chunks for parallel processing
        chunk_size = len(contractors) // self.processes
        chunks = []
        for i in range(self.processes):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.processes - 1 else len(contractors)
            chunks.append(contractors[start_idx:end_idx])
        
        print(f"🔄 Starting parallel processing with {self.processes} processes...")
        print(f"   - Chunk sizes: {[len(chunk) for chunk in chunks]}")
        print()
        
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
                print(f"❌ Process {i + 1}: Exception: {result}")
                total_failed += len(chunks[i]) if i < len(chunks) else 0
            else:
                total_completed += result['completed']
                total_failed += result['failed']
                if result['quota_exceeded']:
                    quota_exceeded = True
                
                duration = result['end_time'] - result['start_time']
                print(f"✅ Process {i + 1}: {result['completed']} completed, {result['failed']} failed "
                      f"({duration:.1f}s)")
        
        self.end_time = time.time()
        
        # Print final results
        print()
        print(f"📊 Final Results:")
        print(f"   - Total completed: {total_completed:,}")
        print(f"   - Total failed: {total_failed:,}")
        print(f"   - Success rate: {total_completed / (total_completed + total_failed) * 100:.1f}%")
        print(f"   - Total time: {(self.end_time - self.start_time) / 60:.1f} minutes")
        
        # Check quota status
        quota_status = quota_tracker.get_quota_status()
        print(f"   - Queries used: {quota_status['queries_today']:,}/{quota_status['daily_limit']:,}")
        print(f"   - Remaining queries: {quota_status['remaining_queries']:,}")
        
        if quota_exceeded:
            print()
            print("🛑 Processing stopped due to daily Google API quota exceeded")
            print("   Please wait until tomorrow to continue processing")
        
        return {
            'completed': total_completed,
            'failed': total_failed,
            'quota_exceeded': quota_exceeded,
            'duration': self.end_time - self.start_time
        }

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Parallel Contractor Processing Test Suite")
    parser.add_argument("--limit", type=int, default=5000, help="Number of contractors to process")
    parser.add_argument("--processes", type=int, default=3, help="Number of parallel processes")
    parser.add_argument("--all", action="store_true", help="Process all ACTIVE contractors (overrides default Puget Sound filter)")
    parser.add_argument("--show-details", action="store_true", help="Show detailed results table")
    
    args = parser.parse_args()
    
    # Set puget_sound_only based on --all flag
    puget_sound_only = not args.all
    
    # Create test suite
    test_suite = ParallelTestSuite(
        limit=args.limit,
        processes=args.processes,
        puget_sound_only=puget_sound_only
    )
    
    # Initialize and check quota
    if not await test_suite.initialize():
        return
    
    # Run the test
    results = await test_suite.run_parallel_batch_test()
    
    if results and results['quota_exceeded']:
        sys.exit(1)  # Exit with error code if quota exceeded

if __name__ == "__main__":
    asyncio.run(main()) 