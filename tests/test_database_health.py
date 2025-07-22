"""
Database health check and performance analysis
Analyzes table sizes, index usage, and identifies potential bottlenecks
"""
import asyncio
import asyncpg
from src.config import config


class DatabaseHealthChecker:
    """Analyze database health and performance characteristics"""
    
    def __init__(self):
        self.db_pool = None
        
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
    
    async def get_table_sizes(self):
        """Get table sizes and row counts"""
        query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation,
                most_common_vals,
                most_common_freqs,
                histogram_bounds,
                CASE 
                    WHEN schemaname = 'public' THEN 
                        (SELECT pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)))
                    ELSE 'N/A'
                END as table_size,
                CASE 
                    WHEN schemaname = 'public' THEN 
                        (SELECT pg_total_relation_size(schemaname||'.'||tablename))
                    ELSE 0
                END as table_size_bytes
            FROM pg_stats 
            WHERE schemaname = 'public' 
                AND tablename IN ('contractors', 'website_searches', 'website_crawls', 
                                'processing_logs', 'manual_review_queue', 'export_batches')
            ORDER BY tablename, attname;
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def get_index_usage_stats(self):
        """Get index usage statistics"""
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC;
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def get_table_row_counts(self):
        """Get row counts for all tables"""
        query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC;
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def get_slow_queries(self):
        """Get recent slow queries from pg_stat_statements"""
        query = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                stddev_time,
                min_time,
                max_time,
                rows
            FROM pg_stat_statements 
            WHERE mean_time > 100  -- queries taking more than 100ms on average
            ORDER BY mean_time DESC
            LIMIT 10;
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                return await conn.fetch(query)
        except asyncpg.UndefinedTableError:
            return []  # pg_stat_statements extension not enabled
    
    async def get_missing_indexes(self):
        """Identify potential missing indexes based on query patterns"""
        query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public' 
                AND tablename = 'contractors'
                AND n_distinct > 100  -- columns with high cardinality
                AND correlation < 0.1  -- low correlation (good for indexes)
            ORDER BY n_distinct DESC;
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def get_connection_stats(self):
        """Get database connection statistics"""
        query = """
            SELECT 
                datname,
                numbackends,
                xact_commit,
                xact_rollback,
                blks_read,
                blks_hit,
                tup_returned,
                tup_fetched,
                tup_inserted,
                tup_updated,
                tup_deleted
            FROM pg_stat_database 
            WHERE datname = current_database();
        """
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(query)
    
    async def run_health_checks(self):
        """Run all health checks and provide analysis"""
        print("🏥 DATABASE HEALTH CHECK")
        print("=" * 80)
        
        # Table sizes and statistics
        print("\n📊 TABLE SIZES AND STATISTICS:")
        print("-" * 50)
        table_sizes = await self.get_table_sizes()
        
        current_table = None
        for row in table_sizes:
            if row['tablename'] != current_table:
                current_table = row['tablename']
                print(f"\n📋 Table: {current_table}")
                if row['table_size'] != 'N/A':
                    print(f"   Size: {row['table_size']}")
            
            if row['n_distinct'] and row['n_distinct'] > 0:
                print(f"   {row['attname']}: {row['n_distinct']} distinct values")
        
        # Row counts
        print("\n📈 ROW COUNTS AND ACTIVITY:")
        print("-" * 50)
        row_counts = await self.get_table_row_counts()
        
        for row in row_counts:
            print(f"📋 {row['tablename']}:")
            print(f"   Live rows: {row['live_rows']:,}")
            print(f"   Dead rows: {row['dead_rows']:,}")
            print(f"   Inserts: {row['inserts']:,}")
            print(f"   Updates: {row['updates']:,}")
            print(f"   Deletes: {row['deletes']:,}")
            
            if row['dead_rows'] > row['live_rows'] * 0.1:  # More than 10% dead rows
                print(f"   ⚠️  WARNING: High dead row ratio - consider VACUUM")
            
            if row['last_vacuum'] is None and row['live_rows'] > 1000:
                print(f"   ⚠️  WARNING: Table never vacuumed - consider maintenance")
        
        # Index usage
        print("\n🔍 INDEX USAGE STATISTICS:")
        print("-" * 50)
        index_stats = await self.get_index_usage_stats()
        
        unused_indexes = []
        for row in index_stats:
            if row['idx_scan'] == 0:
                unused_indexes.append(row['indexname'])
            else:
                print(f"📋 {row['indexname']}:")
                print(f"   Scans: {row['idx_scan']:,}")
                print(f"   Tuples read: {row['idx_tup_read']:,}")
                print(f"   Tuples fetched: {row['idx_tup_fetch']:,}")
                print(f"   Size: {row['index_size']}")
        
        if unused_indexes:
            print(f"\n⚠️  UNUSED INDEXES (consider dropping):")
            for index in unused_indexes:
                print(f"   • {index}")
        
        # Missing indexes
        print("\n🔧 POTENTIAL MISSING INDEXES:")
        print("-" * 50)
        missing_indexes = await self.get_missing_indexes()
        
        for row in missing_indexes:
            print(f"📋 Column: {row['attname']}")
            print(f"   Distinct values: {row['n_distinct']:,}")
            print(f"   Correlation: {row['correlation']:.3f}")
            print(f"   Consider index if frequently queried")
        
        # Connection stats
        print("\n🔌 CONNECTION STATISTICS:")
        print("-" * 50)
        conn_stats = await self.get_connection_stats()
        
        for row in conn_stats:
            print(f"📋 Database: {row['datname']}")
            print(f"   Active connections: {row['numbackends']}")
            print(f"   Commits: {row['xact_commit']:,}")
            print(f"   Rollbacks: {row['xact_rollback']:,}")
            
            if row['blks_hit'] + row['blks_read'] > 0:
                hit_ratio = row['blks_hit'] / (row['blks_hit'] + row['blks_read']) * 100
                print(f"   Cache hit ratio: {hit_ratio:.1f}%")
                
                if hit_ratio < 80:
                    print(f"   ⚠️  WARNING: Low cache hit ratio - consider increasing shared_buffers")
        
        # Slow queries
        print("\n🐌 RECENT SLOW QUERIES:")
        print("-" * 50)
        slow_queries = await self.get_slow_queries()
        
        if slow_queries:
            for row in slow_queries:
                print(f"📋 Query: {row['query'][:100]}...")
                print(f"   Calls: {row['calls']:,}")
                print(f"   Mean time: {row['mean_time']:.2f}ms")
                print(f"   Total time: {row['total_time']:.2f}ms")
                print(f"   Rows: {row['rows']:,}")
        else:
            print("✅ No slow queries detected (or pg_stat_statements not enabled)")
        
        # Recommendations
        self._provide_health_recommendations(row_counts, unused_indexes, missing_indexes, conn_stats)
    
    def _provide_health_recommendations(self, row_counts, unused_indexes, missing_indexes, conn_stats):
        """Provide health recommendations based on analysis"""
        print("\n💡 HEALTH RECOMMENDATIONS:")
        print("-" * 50)
        
        recommendations = []
        
        # Check for tables needing VACUUM
        for row in row_counts:
            if row['dead_rows'] > row['live_rows'] * 0.1:
                recommendations.append(f"• Run VACUUM ANALYZE on {row['tablename']} (high dead row ratio)")
            
            if row['last_vacuum'] is None and row['live_rows'] > 1000:
                recommendations.append(f"• Schedule regular VACUUM for {row['tablename']}")
        
        # Check for unused indexes
        if unused_indexes:
            recommendations.append(f"• Consider dropping unused indexes: {', '.join(unused_indexes[:3])}")
        
        # Check for missing indexes
        if missing_indexes:
            recommendations.append(f"• Consider adding indexes for high-cardinality columns")
        
        # Check cache hit ratio
        for row in conn_stats:
            if row['blks_hit'] + row['blks_read'] > 0:
                hit_ratio = row['blks_hit'] / (row['blks_hit'] + row['blks_read']) * 100
                if hit_ratio < 80:
                    recommendations.append(f"• Consider increasing shared_buffers (cache hit ratio: {hit_ratio:.1f}%)")
        
        # General recommendations
        recommendations.extend([
            "• Monitor query performance with EXPLAIN ANALYZE",
            "• Consider partitioning large tables by date",
            "• Implement connection pooling for better performance",
            "• Regular maintenance: VACUUM, ANALYZE, REINDEX"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")


async def main():
    """Main health check function"""
    checker = DatabaseHealthChecker()
    
    try:
        await checker.connect()
        print("✅ Connected to database")
        
        await checker.run_health_checks()
        
    except Exception as e:
        print(f"❌ Error during health check: {e}")
    finally:
        await checker.disconnect()
        print("✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main()) 