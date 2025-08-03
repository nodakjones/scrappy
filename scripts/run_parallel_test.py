#!/usr/bin/env python3
"""
Parallel Contractor Processing Test Suite
=======================================

This script provides parallel processing for contractor testing with multiple processes.

USAGE:
    python scripts/run_parallel_test.py --limit 100 --processes 3

OPTIONS:
    --limit N        Number of contractors to process (default: 100)
    --processes N    Number of parallel processes (default: 3)
    --all           Process all contractors (overrides default Puget Sound filter)
    --show-details   Show detailed results table (default: summary only)
    --help          Show this help message

EXAMPLES:
    # Run 100 Puget Sound contractors with 3 parallel processes (default)
    python scripts/run_parallel_test.py --limit 100 --processes 3
    
    # Run 50 Puget Sound contractors with 2 parallel processes
    python scripts/run_parallel_test.py --limit 50 --processes 2
    
    # Run 100 all contractors with 3 parallel processes
    python scripts/run_parallel_test.py --limit 100 --processes 3 --all
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from tabulate import tabulate
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService

class ParallelTestSuite:
    def __init__(self, num_processes: int = 3, puget_sound_only: bool = True):
        self.num_processes = num_processes
        self.puget_sound_only = puget_sound_only
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def initialize(self):
        """Initialize the test suite"""
        print("🚀 INITIALIZING PARALLEL TEST SUITE")
        print("=" * 60)
        print(f"📊 Parallel Processes: {self.num_processes}")
        if self.puget_sound_only:
            print("🏔️ Puget Sound Filter: ENABLED")
        else:
            print("🌍 All Contractors: ENABLED")
        
        # Initialize database and service
        await db_pool.initialize()
        
        print("✅ Database and service initialized")
        print("✅ Ready for parallel processing")
        print()
    
    async def process_contractor_chunk(self, contractors_chunk, chunk_id: int):
        """Process a chunk of contractors (runs in separate process)"""
        service = ContractorService()
        chunk_results = []
        
        print(f"🔄 Process {chunk_id}: Starting {len(contractors_chunk)} contractors")
        
        for i, contractor in enumerate(contractors_chunk, 1):
            try:
                # Process the contractor
                processed_contractor = await service.process_contractor(contractor)
                
                # Store results
                result = {
                    'business_name': processed_contractor.business_name,
                    'website_url': processed_contractor.website_url or "None",
                    'category': processed_contractor.mailer_category or "None",
                    'confidence': processed_contractor.confidence_score or 0.0,
                    'location': f"{processed_contractor.city}, {processed_contractor.state}",
                    'review_status': processed_contractor.review_status or "unknown",
                    'is_home_contractor': "Yes" if processed_contractor.is_home_contractor else "No",
                    'processing_status': processed_contractor.processing_status,
                    'process_id': chunk_id
                }
                
                chunk_results.append(result)
                
                # Display result
                status_icon = "✅" if processed_contractor.website_url else "❌"
                print(f"   Process {chunk_id} - {i}/{len(contractors_chunk)}: {contractor.business_name}")
                print(f"   {status_icon} Completed: {result['category']} | Confidence: {result['confidence']:.2f} | Website: {result['website_url']}")
                
            except Exception as e:
                print(f"   ❌ Process {chunk_id} - Error processing {contractor.business_name}: {e}")
                # Add error result
                chunk_results.append({
                    'business_name': contractor.business_name,
                    'website_url': "ERROR",
                    'category': "ERROR",
                    'confidence': 0.0,
                    'location': f"{contractor.city}, {contractor.state}",
                    'review_status': "error",
                    'is_home_contractor': "No",
                    'processing_status': "error",
                    'process_id': chunk_id
                })
        
        await service.close()
        return chunk_results
    
    async def run_parallel_batch_test(self, limit: int):
        """Run a parallel batch test on the specified number of contractors"""
        print(f"🚀 RUNNING PARALLEL BATCH TEST ({limit} contractors, {self.num_processes} processes)")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        try:
            # Get pending contractors with optional Puget Sound filter
            service = ContractorService()
            
            if self.puget_sound_only:
                # Get Puget Sound contractors only
                contractors = await db_pool.fetch('''
                    SELECT * FROM contractors 
                    WHERE processing_status = 'pending' 
                    AND puget_sound = TRUE
                    ORDER BY created_at ASC 
                    LIMIT $1
                ''', limit)
                
                # Convert to Contractor objects
                from src.database.models import Contractor
                contractors = [Contractor.from_dict(dict(row)) for row in contractors]
            else:
                # Get all pending contractors
                contractors = await service.get_pending_contractors(limit=limit)
            
            await service.close()
            
            if not contractors:
                print("❌ No pending contractors found!")
                return []
            
            print(f"📋 Found {len(contractors)} contractors to process")
            print(f"🔄 Splitting into {self.num_processes} parallel processes")
            print()
            
            # Split contractors into chunks for parallel processing
            chunk_size = len(contractors) // self.num_processes
            if len(contractors) % self.num_processes:
                chunk_size += 1
            
            contractor_chunks = []
            for i in range(0, len(contractors), chunk_size):
                chunk = contractors[i:i + chunk_size]
                contractor_chunks.append(chunk)
            
            print(f"📦 Created {len(contractor_chunks)} chunks of ~{chunk_size} contractors each")
            print()
            
            # Process chunks in parallel using asyncio
            tasks = []
            for i, chunk in enumerate(contractor_chunks):
                task = asyncio.create_task(self.process_contractor_chunk(chunk, i + 1))
                tasks.append(task)
            
            # Wait for all tasks to complete
            chunk_results = await asyncio.gather(*tasks)
            
            # Combine all results
            for chunk_result in chunk_results:
                self.results.extend(chunk_result)
            
            self.end_time = datetime.now()
            return self.results
            
        except Exception as e:
            print(f"❌ Parallel batch test error: {e}")
            return []
    
    def analyze_results(self, show_details: bool = False):
        """Analyze and display test results"""
        if not self.results:
            print("❌ No results to analyze")
            return
        
        print(f"\n📊 PARALLEL RESULTS ANALYSIS")
        print("=" * 60)
        
        # Basic statistics
        total = len(self.results)
        websites_found = sum(1 for r in self.results if r['website_url'] and r['website_url'] != "None" and r['website_url'] != "ERROR")
        errors = sum(1 for r in self.results if r['website_url'] == "ERROR")
        
        # Confidence distribution
        high_conf = sum(1 for r in self.results if r['confidence'] >= 0.8)
        med_conf = sum(1 for r in self.results if 0.6 <= r['confidence'] < 0.8)
        low_conf = sum(1 for r in self.results if r['confidence'] < 0.6)
        
        # Category distribution
        categories = {}
        for r in self.results:
            category = r['category']
            if category != "ERROR":
                categories[category] = categories.get(category, 0) + 1
        
        # Home contractor rate
        home_contractors = sum(1 for r in self.results if r['is_home_contractor'] == "Yes")
        
        # Process distribution
        process_stats = {}
        for r in self.results:
            process_id = r.get('process_id', 'unknown')
            process_stats[process_id] = process_stats.get(process_id, 0) + 1
        
        # Display summary statistics
        print(f"📈 SUMMARY STATISTICS:")
        print(f"  Total Processed: {total}")
        print(f"  Websites Found: {websites_found}/{total} ({websites_found/total*100:.1f}%)")
        print(f"  Errors: {errors}/{total} ({errors/total*100:.1f}%)")
        print(f"  Processing Time: {self.end_time - self.start_time}")
        print(f"  Parallel Processes: {self.num_processes}")
        
        print(f"\n🎯 CONFIDENCE DISTRIBUTION:")
        print(f"  High (≥0.8): {high_conf}/{total} ({high_conf/total*100:.1f}%)")
        print(f"  Medium (0.6-0.79): {med_conf}/{total} ({med_conf/total*100:.1f}%)")
        print(f"  Low (<0.6): {low_conf}/{total} ({low_conf/total*100:.1f}%)")
        
        print(f"\n🏠 HOME CONTRACTOR RATE:")
        print(f"  Home Contractors: {home_contractors}/{total} ({home_contractors/total*100:.1f}%)")
        
        print(f"\n📂 CATEGORY DISTRIBUTION:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        print(f"\n⚙️ PROCESS DISTRIBUTION:")
        for process_id, count in sorted(process_stats.items()):
            print(f"  Process {process_id}: {count} contractors")
        
        # Quality assessment
        print(f"\n🔍 QUALITY ASSESSMENT:")
        if websites_found/total >= 0.8:
            website_quality = "EXCELLENT"
        elif websites_found/total >= 0.6:
            website_quality = "GOOD"
        elif websites_found/total >= 0.4:
            website_quality = "FAIR"
        else:
            website_quality = "POOR"
        
        if high_conf/total >= 0.3:
            confidence_quality = "EXCELLENT"
        elif high_conf/total >= 0.2:
            confidence_quality = "GOOD"
        elif high_conf/total >= 0.1:
            confidence_quality = "FAIR"
        else:
            confidence_quality = "POOR"
        
        if errors/total <= 0.05:
            error_quality = "EXCELLENT"
        elif errors/total <= 0.1:
            error_quality = "GOOD"
        elif errors/total <= 0.2:
            error_quality = "FAIR"
        else:
            error_quality = "POOR"
        
        print(f"  ⚠️ Website Discovery: {website_quality}")
        print(f"  ⚠️ High Confidence Rate: {confidence_quality}")
        print(f"  ✅ Error Rate: {error_quality}")
        
        # Show detailed results table if requested
        if show_details:
            print(f"\n📋 DETAILED RESULTS TABLE:")
            print("=" * 60)
            
            # Prepare table data
            table_data = []
            for result in self.results:
                table_data.append([
                    result['business_name'][:30] + "..." if len(result['business_name']) > 30 else result['business_name'],
                    result['website_url'][:50] + "..." if result['website_url'] and len(result['website_url']) > 50 else result['website_url'],
                    result['category'],
                    f"{result['confidence']:.2f}",
                    result['location'],
                    result['review_status'],
                    result['is_home_contractor'],
                    f"P{result.get('process_id', '?')}"
                ])
            
            # Display table
            headers = ["Business Name", "Website", "Category", "Confidence", "Location", "Review Status", "Home Contractor", "Process"]
            print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 50, 20, 10, 20, 15, 15, 8]))
        
        print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def cleanup(self):
        """Clean up resources"""
        await db_pool.close()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Parallel Contractor Processing Test Suite")
    parser.add_argument("--limit", type=int, default=100, help="Number of contractors to process")
    parser.add_argument("--processes", type=int, default=3, help="Number of parallel processes")
    parser.add_argument("--all", action="store_true", help="Process all contractors (overrides default Puget Sound filter)")
    parser.add_argument("--show-details", action="store_true", help="Show detailed results table")
    
    args = parser.parse_args()
    
    # Create and run test suite (default to Puget Sound, override with --all)
    puget_sound_only = not args.all  # Default True, False if --all is specified
    test_suite = ParallelTestSuite(num_processes=args.processes, puget_sound_only=puget_sound_only)
    
    try:
        await test_suite.initialize()
        await test_suite.run_parallel_batch_test(args.limit)
        test_suite.analyze_results(show_details=args.show_details)
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 