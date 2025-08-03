#!/usr/bin/env python3
"""
Comprehensive Contractor Processing Test Suite
============================================

This script provides a complete testing workflow for the contractor processing system.

USAGE:
    python scripts/run_comprehensive_test.py --limit 100

OPTIONS:
    --limit N        Number of contractors to process (default: 10)
    --show-details   Show detailed results table (default: summary only)
    --test-specific  Test specific problematic cases first
    --help          Show this help message

EXAMPLES:
    # Run a quick 10-contractor test
    python scripts/run_comprehensive_test.py --limit 10
    
    # Run a comprehensive 100-contractor test
    python scripts/run_comprehensive_test.py --limit 100 --show-details
    
    # Test specific problematic cases first
    python scripts/run_comprehensive_test.py --test-specific

FEATURES:
    - Processes contractors in batches
    - Displays comprehensive results table
    - Shows confidence distribution analysis
    - Identifies potential issues
    - Provides actionable insights
    - Saves results to log file
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from tabulate import tabulate

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import db_pool
from src.services.contractor_service import ContractorService

class ComprehensiveTestSuite:
    def __init__(self):
        self.service = None
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def initialize(self):
        """Initialize the test suite"""
        print("🚀 INITIALIZING COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Initialize database and service
        await db_pool.initialize()
        self.service = ContractorService()
        
        print("✅ Database and service initialized")
        print("✅ Ready to process contractors")
        print()
    
    async def test_specific_cases(self):
        """Test specific problematic cases to validate system improvements"""
        print("🧪 TESTING SPECIFIC PROBLEMATIC CASES")
        print("=" * 60)
        
        test_cases = [
            {
                "business_name": "509 HEATING & COOLING",
                "city": "YAKIMA",
                "state": "WA",
                "url": "https://www.thermallheating.com/service-areas/yakima",
                "title": "Thermal Heating & Cooling - HVAC Services",
                "snippet": "Professional HVAC services in Yakima area",
                "expected": "REJECTED"
            },
            {
                "business_name": "509 SERVICES",
                "city": "COLBERT",
                "state": "WA",
                "url": "https://nevinfloorcompany.com/removing-hardwood-floors/colbert-washington/",
                "title": "Nevin Floor Company - Hardwood Floor Removal",
                "snippet": "Professional hardwood floor removal services in Colbert, Washington",
                "expected": "REJECTED"
            },
            {
                "business_name": "5 Star Guttering",
                "city": "PASCO",
                "state": "WA",
                "url": "https://5starguttering.com/",
                "title": "5 Star Guttering - Professional Gutter Services",
                "snippet": "Professional gutter installation and repair services in Pasco, Washington",
                "expected": "ACCEPTED"
            }
        ]
        
        results = []
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔍 Testing Case {i}: {case['business_name']}")
            
            # Create mock search item
            search_item = {
                'title': case['title'],
                'snippet': case['snippet'],
                'link': case['url']
            }
            
            # Test confidence calculation
            confidence = self.service._calculate_search_confidence(
                search_item, 
                case['business_name'], 
                case['city'], 
                case['state']
            )
            
            # Determine if accepted
            accepted = confidence >= 0.4
            status = "✅ ACCEPTED" if accepted else "❌ REJECTED"
            expected_match = case['expected'] == "ACCEPTED"
            
            result = {
                'case': i,
                'business': case['business_name'],
                'url': case['url'],
                'confidence': confidence,
                'status': status,
                'expected': case['expected'],
                'correct': (accepted and expected_match) or (not accepted and not expected_match)
            }
            
            results.append(result)
            
            print(f"  Confidence: {confidence:.3f}")
            print(f"  Status: {status}")
            print(f"  Expected: {case['expected']}")
            print(f"  Correct: {'✅ YES' if result['correct'] else '❌ NO'}")
        
        # Display summary
        print(f"\n📊 SPECIFIC CASES SUMMARY:")
        print("=" * 40)
        correct = sum(1 for r in results if r['correct'])
        total = len(results)
        print(f"Correct Predictions: {correct}/{total} ({correct/total*100:.1f}%)")
        
        return results
    
    async def run_batch_test(self, limit: int):
        """Run a batch test on the specified number of contractors"""
        print(f"🚀 RUNNING BATCH TEST ({limit} contractors)")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        try:
            # Get pending contractors
            contractors = await self.service.get_pending_contractors(limit=limit)
            
            if not contractors:
                print("❌ No pending contractors found!")
                return []
            
            print(f"📋 Found {len(contractors)} contractors to process")
            print()
            
            # Process contractors
            for i, contractor in enumerate(contractors, 1):
                print(f"Processing {i}/{len(contractors)}: {contractor.business_name} ({contractor.city}, {contractor.state})")
                
                try:
                    # Process the contractor
                    processed_contractor = await self.service.process_contractor(contractor)
                    
                    # Store results
                    result = {
                        'business_name': processed_contractor.business_name,
                        'website_url': processed_contractor.website_url or "None",
                        'category': processed_contractor.mailer_category or "None",
                        'confidence': processed_contractor.confidence_score or 0.0,
                        'location': f"{processed_contractor.city}, {processed_contractor.state}",
                        'review_status': processed_contractor.review_status or "unknown",
                        'is_home_contractor': "Yes" if processed_contractor.is_home_contractor else "No",
                        'processing_status': processed_contractor.processing_status
                    }
                    
                    self.results.append(result)
                    
                    # Display result
                    status_icon = "✅" if processed_contractor.website_url else "❌"
                    print(f"   {status_icon} Completed: {result['category']} | Confidence: {result['confidence']:.2f} | Website: {result['website_url']}")
                    
                except Exception as e:
                    print(f"   ❌ Error processing {contractor.business_name}: {e}")
                    # Add error result
                    self.results.append({
                        'business_name': contractor.business_name,
                        'website_url': "ERROR",
                        'category': "ERROR",
                        'confidence': 0.0,
                        'location': f"{contractor.city}, {contractor.state}",
                        'review_status': "error",
                        'is_home_contractor': "No",
                        'processing_status': "error"
                    })
            
            self.end_time = datetime.now()
            return self.results
            
        except Exception as e:
            print(f"❌ Batch test error: {e}")
            return []
    
    def analyze_results(self, show_details: bool = False):
        """Analyze and display test results"""
        if not self.results:
            print("❌ No results to analyze")
            return
        
        print(f"\n📊 COMPREHENSIVE RESULTS ANALYSIS")
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
        
        # Display summary statistics
        print(f"📈 SUMMARY STATISTICS:")
        print(f"  Total Processed: {total}")
        print(f"  Websites Found: {websites_found}/{total} ({websites_found/total*100:.1f}%)")
        print(f"  Errors: {errors}/{total} ({errors/total*100:.1f}%)")
        print(f"  Processing Time: {self.end_time - self.start_time}")
        print()
        
        print(f"🎯 CONFIDENCE DISTRIBUTION:")
        print(f"  High (≥0.8): {high_conf}/{total} ({high_conf/total*100:.1f}%)")
        print(f"  Medium (0.6-0.79): {med_conf}/{total} ({med_conf/total*100:.1f}%)")
        print(f"  Low (<0.6): {low_conf}/{total} ({low_conf/total*100:.1f}%)")
        print()
        
        print(f"🏠 HOME CONTRACTOR RATE:")
        print(f"  Home Contractors: {home_contractors}/{total} ({home_contractors/total*100:.1f}%)")
        print()
        
        print(f"📂 CATEGORY DISTRIBUTION:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        print()
        
        # Display detailed results table if requested
        if show_details:
            print(f"📋 DETAILED RESULTS TABLE:")
            print("=" * 60)
            
            # Prepare table data
            table_data = []
            for r in self.results:
                # Truncate long values for display
                business_name = r['business_name'][:30] + "..." if len(r['business_name']) > 30 else r['business_name']
                website_url = r['website_url'][:35] + "..." if len(r['website_url']) > 35 else r['website_url']
                category = r['category'][:20] + "..." if len(r['category']) > 20 else r['category']
                
                table_data.append([
                    business_name,
                    website_url,
                    category,
                    f"{r['confidence']:.2f}",
                    r['location'],
                    r['review_status'],
                    r['is_home_contractor']
                ])
            
            headers = ["Business Name", "Website", "Category", "Confidence", "Location", "Review Status", "Home Contractor"]
            table = tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 35, 20, 10, 20, 12, 8])
            print(table)
        
        # Quality assessment
        print(f"🔍 QUALITY ASSESSMENT:")
        if websites_found/total >= 0.8:
            print("  ✅ Website Discovery: EXCELLENT")
        elif websites_found/total >= 0.6:
            print("  ✅ Website Discovery: GOOD")
        elif websites_found/total >= 0.4:
            print("  ⚠️ Website Discovery: FAIR")
        else:
            print("  ❌ Website Discovery: POOR")
        
        if high_conf/total >= 0.3:
            print("  ✅ High Confidence Rate: EXCELLENT")
        elif high_conf/total >= 0.2:
            print("  ✅ High Confidence Rate: GOOD")
        elif high_conf/total >= 0.1:
            print("  ⚠️ High Confidence Rate: FAIR")
        else:
            print("  ❌ High Confidence Rate: POOR")
        
        if errors/total <= 0.05:
            print("  ✅ Error Rate: EXCELLENT")
        elif errors/total <= 0.1:
            print("  ✅ Error Rate: GOOD")
        elif errors/total <= 0.2:
            print("  ⚠️ Error Rate: FAIR")
        else:
            print("  ❌ Error Rate: POOR")
        
        print()
        print(f"⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'service') and self.service:
            await self.service.close()
        await db_pool.close()

async def main():
    """Main function to run the comprehensive test suite"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Contractor Processing Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    python scripts/run_comprehensive_test.py --limit 10
    python scripts/run_comprehensive_test.py --limit 100 --show-details
    python scripts/run_comprehensive_test.py --test-specific
        """
    )
    
    parser.add_argument('--limit', type=int, default=10, 
                       help='Number of contractors to process (default: 10)')
    parser.add_argument('--show-details', action='store_true',
                       help='Show detailed results table (default: summary only)')
    parser.add_argument('--test-specific', action='store_true',
                       help='Test specific problematic cases first')

    
    args = parser.parse_args()
    

    
    # Create test suite
    test_suite = ComprehensiveTestSuite()
    
    try:
        # Initialize
        await test_suite.initialize()
        
        # Test specific cases if requested
        if args.test_specific:
            await test_suite.test_specific_cases()
            print("\n" + "="*60 + "\n")
        
        # Run batch test
        results = await test_suite.run_batch_test(args.limit)
        
        # Analyze results
        test_suite.analyze_results(args.show_details)
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 