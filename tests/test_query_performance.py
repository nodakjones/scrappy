"""
Performance testing for contractor enrichment system queries
Identifies slow queries and suggests optimizations
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import asyncpg
from src.config import config


class QueryPerformanceTester:
    """Test database query performance and identify bottlenecks"""
    
    def __init__(self):
        self.db_pool = None
        self.results = []
        
    async def connect(self):
        """Establish database connection"""
        self.db_pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            min_size=1,
            max_size=5
        )
    
    async def disconnect(self):
        """Close database connection"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def execute_query_with_timing(self, query: str, params: tuple = None, 
                                      description: str = "", iterations: int = 5) -> Dict[str, Any]:
        """Execute a query multiple times and measure performance"""
        times = []
        results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            async with self.db_pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            times.append(execution_time)
            results.append(len(result))
        
        return {
            'description': description,
            'query': query[:100] + '...' if len(query) > 100 else query,
            'avg_time_ms': statistics.mean(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
            'avg_results': statistics.mean(results),
            'iterations': iterations
        }
    
    def get_test_queries(self) -> List[Dict[str, Any]]:
        """Define test queries to evaluate performance"""
        return [
            {
                'description': 'Pending contractors for processing',
                'query': '''
                    SELECT id, business_name, city, state, phone_number 
                    FROM contractors 
                    WHERE processing_status = 'pending' 
                    ORDER BY created_at 
                    LIMIT 100
                ''',
                'params': None
            },
            {
                'description': 'Manual review queue with confidence scores',
                'query': '''
                    SELECT id, business_name, city, state, confidence_score, 
                           manual_review_reason, gpt4mini_analysis->>'reasoning' as reasoning
                    FROM contractors 
                    WHERE processing_status = 'manual_review' 
                        AND review_status IS NULL
                    ORDER BY confidence_score ASC, business_name
                    LIMIT 50
                ''',
                'params': None
            },
            {
                'description': 'High confidence contractors for auto-approval',
                'query': '''
                    SELECT id, business_name, mailer_category, confidence_score
                    FROM contractors 
                    WHERE confidence_score >= 0.8 
                        AND processing_status = 'completed'
                        AND residential_focus = TRUE
                    ORDER BY confidence_score DESC
                    LIMIT 100
                ''',
                'params': None
            },
            {
                'description': 'Contractors by city and state with filtering',
                'query': '''
                    SELECT city, state, COUNT(*) as contractor_count,
                           COUNT(*) FILTER (WHERE residential_focus = TRUE) as residential_contractors,
                           AVG(confidence_score) as avg_confidence
                    FROM contractors 
                    WHERE processing_status IN ('completed', 'manual_review')
                    GROUP BY city, state
                    HAVING COUNT(*) >= 5
                    ORDER BY contractor_count DESC
                    LIMIT 20
                ''',
                'params': None
            },
            {
                'description': 'Search for specific business name (fuzzy match)',
                'query': '''
                    SELECT id, business_name, city, state, phone_number, confidence_score
                    FROM contractors 
                    WHERE business_name % $1
                    ORDER BY business_name <-> $1, confidence_score DESC
                    LIMIT 10
                ''',
                'params': ('ABC Construction',)
            },
            {
                'description': 'Contractors with specific services',
                'query': '''
                    SELECT id, business_name, services_offered, confidence_score
                    FROM contractors 
                    WHERE services_offered && $1
                        AND processing_status = 'completed'
                    ORDER BY confidence_score DESC
                    LIMIT 20
                ''',
                'params': (['plumbing', 'electrical'],)
            },
            {
                'description': 'Processing status summary with counts',
                'query': '''
                    SELECT 
                        processing_status,
                        COUNT(*) as total_count,
                        COUNT(*) FILTER (WHERE residential_focus = TRUE) as residential_contractors,
                        AVG(confidence_score) as avg_confidence,
                        MIN(confidence_score) as min_confidence,
                        MAX(confidence_score) as max_confidence
                    FROM contractors 
                    GROUP BY processing_status
                    ORDER BY 
                        CASE processing_status
                            WHEN 'pending' THEN 1
                            WHEN 'processing' THEN 2 
                            WHEN 'completed' THEN 3
                            WHEN 'manual_review' THEN 4
                            WHEN 'error' THEN 5
                        END
                ''',
                'params': None
            },
            {
                'description': 'Recent processing logs with contractor details',
                'query': '''
                    SELECT 
                        pl.processing_step,
                        pl.step_status,
                        pl.processing_time_seconds,
                        c.business_name,
                        c.confidence_score
                    FROM processing_logs pl
                    JOIN contractors c ON pl.contractor_id = c.id
                    WHERE pl.started_at >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY pl.started_at DESC
                    LIMIT 50
                ''',
                'params': None
            },
            {
                'description': 'Website search results analysis',
                'query': '''
                    SELECT 
                        ws.search_method,
                        COUNT(*) as total_searches,
                        COUNT(*) FILTER (WHERE ws.success = TRUE) as successful_searches,
                        AVG(ws.results_found) as avg_results,
                        AVG(c.confidence_score) as avg_confidence
                    FROM website_searches ws
                    JOIN contractors c ON ws.contractor_id = c.id
                    WHERE ws.attempted_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY ws.search_method
                    ORDER BY total_searches DESC
                ''',
                'params': None
            },
            {
                'description': 'Complex JSONB analysis query',
                'query': '''
                    SELECT 
                        id,
                        business_name,
                        gpt4mini_analysis->>'residential_focus' as llm_classification,
                        gpt4mini_analysis->>'confidence' as llm_confidence,
                        gpt4_verification->>'verification_result' as verification_result,
                        confidence_score
                    FROM contractors 
                    WHERE gpt4mini_analysis IS NOT NULL 
                        AND gpt4_verification IS NOT NULL
                        AND processing_status = 'completed'
                    ORDER BY confidence_score DESC
                    LIMIT 25
                ''',
                'params': None
            },
            {
                'description': 'Export batch analysis',
                'query': '''
                    SELECT 
                        eb.batch_id,
                        eb.export_date,
                        eb.contractor_count,
                        COUNT(c.id) as actual_exported,
                        AVG(c.confidence_score) as avg_confidence
                    FROM export_batches eb
                    LEFT JOIN contractors c ON c.export_batch_id = eb.batch_id
                    WHERE eb.export_date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY eb.batch_id, eb.export_date, eb.contractor_count
                    ORDER BY eb.export_date DESC
                    LIMIT 10
                ''',
                'params': None
            },
            {
                'description': 'Performance bottleneck: Full table scan on large dataset',
                'query': '''
                    SELECT 
                        business_name,
                        city,
                        state,
                        phone_number,
                        confidence_score,
                        processing_status
                    FROM contractors 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                    ORDER BY created_at DESC
                    LIMIT 1000
                ''',
                'params': None
            }
        ]
    
    async def run_performance_tests(self) -> List[Dict[str, Any]]:
        """Run all performance tests"""
        print("🔍 Starting database query performance tests...")
        print("=" * 80)
        
        results = []
        test_queries = self.get_test_queries()
        
        for i, test in enumerate(test_queries, 1):
            print(f"Testing query {i}/{len(test_queries)}: {test['description']}")
            
            try:
                result = await self.execute_query_with_timing(
                    test['query'], 
                    test['params'], 
                    test['description']
                )
                results.append(result)
                
                # Print immediate results
                if result['avg_time_ms'] > 100:
                    print(f"  ⚠️  SLOW: {result['avg_time_ms']:.1f}ms avg")
                elif result['avg_time_ms'] > 50:
                    print(f"  ⚡ MEDIUM: {result['avg_time_ms']:.1f}ms avg")
                else:
                    print(f"  ✅ FAST: {result['avg_time_ms']:.1f}ms avg")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                results.append({
                    'description': test['description'],
                    'query': test['query'],
                    'error': str(e),
                    'avg_time_ms': 0
                })
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]):
        """Analyze performance test results and provide recommendations"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE ANALYSIS RESULTS")
        print("=" * 80)
        
        # Sort by average time (slowest first)
        slow_queries = [r for r in results if 'error' not in r and r['avg_time_ms'] > 50]
        fast_queries = [r for r in results if 'error' not in r and r['avg_time_ms'] <= 50]
        error_queries = [r for r in results if 'error' in r]
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total queries tested: {len(results)}")
        print(f"  Fast queries (<50ms): {len(fast_queries)}")
        print(f"  Medium queries (50-100ms): {len([r for r in slow_queries if r['avg_time_ms'] <= 100])}")
        print(f"  Slow queries (>100ms): {len([r for r in slow_queries if r['avg_time_ms'] > 100])}")
        print(f"  Failed queries: {len(error_queries)}")
        
        if slow_queries:
            print(f"\n🐌 SLOW QUERIES (needing optimization):")
            for query in sorted(slow_queries, key=lambda x: x['avg_time_ms'], reverse=True):
                print(f"  • {query['description']}")
                print(f"    Avg: {query['avg_time_ms']:.1f}ms | Min: {query['min_time_ms']:.1f}ms | Max: {query['max_time_ms']:.1f}ms")
                print(f"    Results: {query['avg_results']:.0f} rows")
                print()
        
        if error_queries:
            print(f"\n❌ FAILED QUERIES:")
            for query in error_queries:
                print(f"  • {query['description']}: {query['error']}")
        
        # Provide optimization recommendations
        self._provide_optimization_recommendations(slow_queries)
    
    def _provide_optimization_recommendations(self, slow_queries: List[Dict[str, Any]]):
        """Provide specific optimization recommendations"""
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        recommendations = []
        
        for query in slow_queries:
            if 'manual_review' in query['description'].lower():
                recommendations.append({
                    'issue': 'Manual review queries are slow',
                    'solution': 'Add composite index: CREATE INDEX idx_contractors_manual_review_composite ON contractors (processing_status, review_status, confidence_score) WHERE processing_status = \'manual_review\''
                })
            
            if 'business_name' in query['description'].lower() and 'fuzzy' in query['description'].lower():
                recommendations.append({
                    'issue': 'Fuzzy name matching is slow',
                    'solution': 'Ensure pg_trgm extension is enabled and consider adding: CREATE INDEX idx_contractors_business_name_trgm ON contractors USING gin (business_name gin_trgm_ops)'
                })
            
            if 'services_offered' in query['description'].lower():
                recommendations.append({
                    'issue': 'Array searches on services_offered are slow',
                    'solution': 'Add GIN index: CREATE INDEX idx_contractors_services_offered ON contractors USING gin (services_offered)'
                })
            
            if 'processing_logs' in query['description'].lower():
                recommendations.append({
                    'issue': 'Joining processing_logs with contractors is slow',
                    'solution': 'Add index: CREATE INDEX idx_processing_logs_contractor_date ON processing_logs (contractor_id, started_at DESC)'
                })
            
            if 'website_searches' in query['description'].lower():
                recommendations.append({
                    'issue': 'Website searches analysis query is slow',
                    'solution': 'Add composite index: CREATE INDEX idx_website_searches_analysis ON website_searches (search_method, success, attempted_at)'
                })
            
            if 'JSONB' in query['description'].lower():
                recommendations.append({
                    'issue': 'JSONB queries are slow',
                    'solution': 'Add specific JSONB path indexes for frequently queried fields'
                })
        
        # Remove duplicates
        unique_recommendations = []
        seen_issues = set()
        for rec in recommendations:
            if rec['issue'] not in seen_issues:
                unique_recommendations.append(rec)
                seen_issues.add(rec['issue'])
        
        for i, rec in enumerate(unique_recommendations, 1):
            print(f"  {i}. {rec['issue']}")
            print(f"     Solution: {rec['solution']}")
            print()
        
        # General recommendations
        print(f"🔧 GENERAL OPTIMIZATIONS:")
        print(f"  • Run VACUUM ANALYZE on contractors table regularly")
        print(f"  • Consider partitioning large tables by date")
        print(f"  • Monitor query execution plans with EXPLAIN ANALYZE")
        print(f"  • Consider read replicas for heavy reporting queries")
        print(f"  • Implement query result caching for frequently accessed data")


async def main():
    """Main performance testing function"""
    tester = QueryPerformanceTester()
    
    try:
        await tester.connect()
        print("✅ Connected to database")
        
        results = await tester.run_performance_tests()
        tester.analyze_results(results)
        
    except Exception as e:
        print(f"❌ Error during performance testing: {e}")
    finally:
        await tester.disconnect()
        print("✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main()) 