-- Optimized indexes for contractor enrichment system
-- Based on performance analysis and common query patterns

-- Drop any existing indexes that might be redundant or unused
-- (Run these carefully in production - check usage first)

-- DROP INDEX IF EXISTS idx_contractors_business_name;  -- Will be replaced with better version
-- DROP INDEX IF EXISTS idx_contractors_processing_status;  -- Will be replaced with composite

-- 1. COMPOSITE INDEXES FOR COMMON QUERY PATTERNS

-- Manual review queries (most critical for performance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_manual_review_composite 
ON contractors (processing_status, review_status, confidence_score, created_at) 
WHERE processing_status = 'manual_review';

-- Pending contractors for processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_pending_composite 
ON contractors (processing_status, created_at) 
WHERE processing_status = 'pending';

-- High confidence contractors for auto-approval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_high_confidence 
ON contractors (confidence_score, processing_status, is_home_contractor) 
WHERE confidence_score >= 0.8 AND processing_status = 'completed';

-- City/State filtering with processing status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_location_status 
ON contractors (city, state, processing_status, confidence_score);

-- 2. IMPROVED TEXT SEARCH INDEXES

-- Enhanced business name search (fuzzy + exact)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_business_name_enhanced 
ON contractors USING gin (business_name gin_trgm_ops);

-- Business name with confidence score for ranking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_name_confidence 
ON contractors (business_name, confidence_score) 
WHERE confidence_score IS NOT NULL;

-- 3. ARRAY AND JSONB OPTIMIZATIONS

-- Services offered array search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_services_offered_enhanced 
ON contractors USING gin (services_offered) 
WHERE processing_status = 'completed';

-- Service categories array search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_service_categories_enhanced 
ON contractors USING gin (service_categories) 
WHERE processing_status = 'completed';

-- JSONB path indexes for frequently accessed fields
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_gpt4mini_reasoning 
ON contractors USING gin ((gpt4mini_analysis->>'reasoning'));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_gpt4mini_classification 
ON contractors USING gin ((gpt4mini_analysis->>'is_home_contractor'));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_gpt4_verification 
ON contractors USING gin ((gpt4_verification->>'verification_result'));

-- 4. WORKFLOW-SPECIFIC INDEXES

-- Export workflow optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_export_workflow 
ON contractors (marked_for_download, export_batch_id, exported_at) 
WHERE marked_for_download = TRUE;

-- Review workflow optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_review_workflow 
ON contractors (review_status, reviewed_at, reviewed_by) 
WHERE review_status IS NOT NULL;

-- 5. JOIN OPTIMIZATION INDEXES

-- Processing logs join optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processing_logs_contractor_date 
ON processing_logs (contractor_id, started_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processing_logs_step_status 
ON processing_logs (processing_step, step_status, started_at);

-- Website searches analysis optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_website_searches_analysis 
ON website_searches (search_method, success, attempted_at, contractor_id);

-- Website crawls optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_website_crawls_contractor_status 
ON website_crawls (contractor_id, crawl_status, attempted_at);

-- 6. PARTIAL INDEXES FOR COMMON FILTERS

-- Home contractors only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_home_only 
ON contractors (confidence_score, mailer_category, city, state) 
WHERE is_home_contractor = TRUE;

-- Priority categories
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_priority_only 
ON contractors (confidence_score, mailer_category) 
WHERE priority_category = TRUE;

-- Completed processing only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_completed_only 
ON contractors (confidence_score, mailer_category, is_home_contractor) 
WHERE processing_status = 'completed';

-- 7. STATISTICS AND MAINTENANCE

-- Update table statistics for better query planning
ANALYZE contractors;
ANALYZE website_searches;
ANALYZE website_crawls;
ANALYZE processing_logs;
ANALYZE manual_review_queue;

-- 8. MONITORING INDEXES (for performance tracking)

-- Index usage monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_created_at_monitoring 
ON contractors (created_at) 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Performance monitoring for large datasets
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_performance_monitoring 
ON contractors (processing_status, confidence_score, created_at) 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days';

-- 9. CONDITIONAL INDEXES FOR SPECIFIC SCENARIOS

-- Error handling optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_error_handling 
ON contractors (processing_status, error_message, created_at) 
WHERE processing_status = 'error';

-- Manual review reason optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_review_reason 
ON contractors (manual_review_reason, confidence_score) 
WHERE manual_review_needed = TRUE;

-- 10. COMPOSITE INDEXES FOR COMPLEX QUERIES

-- Multi-column filtering for reporting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_reporting 
ON contractors (processing_status, is_home_contractor, mailer_category, confidence_score, created_at);

-- Search and filtering combination
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_search_filter 
ON contractors (business_name, city, state, processing_status, confidence_score);

-- 11. INDEXES FOR AGGREGATION QUERIES

-- Group by city/state with filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contractors_aggregation 
ON contractors (city, state, processing_status, is_home_contractor, confidence_score);

-- 12. CLEANUP AND MAINTENANCE COMMANDS

-- Comment: Run these maintenance commands regularly
-- VACUUM ANALYZE contractors;
-- VACUUM ANALYZE website_searches;
-- VACUUM ANALYZE website_crawls;
-- VACUUM ANALYZE processing_logs;

-- 13. INDEX SIZE MONITORING QUERY
-- Uncomment to check index sizes:
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
*/

-- 14. INDEX USAGE ANALYSIS QUERY
-- Uncomment to analyze index usage:
/*
SELECT 
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 10 THEN 'LOW_USAGE'
        WHEN idx_scan < 100 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/ 