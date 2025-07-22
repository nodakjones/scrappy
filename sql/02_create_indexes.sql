-- Performance indexes for contractor enrichment system

-- Primary lookup indexes on contractors table
CREATE INDEX idx_contractors_business_name ON contractors USING gin (business_name gin_trgm_ops);
CREATE INDEX idx_contractors_processing_status ON contractors (processing_status);
CREATE INDEX idx_contractors_confidence_score ON contractors (confidence_score) WHERE confidence_score IS NOT NULL;
CREATE INDEX idx_contractors_review_status ON contractors (review_status) WHERE review_status IS NOT NULL;
CREATE INDEX idx_contractors_city_state ON contractors (city, state);
CREATE INDEX idx_contractors_phone ON contractors (phone_number) WHERE phone_number IS NOT NULL;
CREATE INDEX idx_contractors_license_number ON contractors (contractor_license_number);

-- Conditional indexes for workflow states
CREATE INDEX idx_contractors_pending ON contractors (created_at) WHERE processing_status = 'pending';
CREATE INDEX idx_contractors_manual_review ON contractors (confidence_score, created_at) WHERE processing_status = 'manual_review';
CREATE INDEX idx_contractors_for_download ON contractors (marked_for_download_at) WHERE marked_for_download = TRUE;
CREATE INDEX idx_contractors_exported ON contractors (exported_at) WHERE exported_at IS NOT NULL;

-- JSONB indexes for analysis data
CREATE INDEX idx_contractors_gpt4mini_analysis ON contractors USING gin (gpt4mini_analysis);
CREATE INDEX idx_contractors_gpt4_verification ON contractors USING gin (gpt4_verification);
CREATE INDEX idx_contractors_social_media ON contractors USING gin (social_media_urls);

-- Array indexes for services and categories
CREATE INDEX idx_contractors_services_offered ON contractors USING gin (services_offered);
CREATE INDEX idx_contractors_service_categories ON contractors USING gin (service_categories);
CREATE INDEX idx_contractors_specializations ON contractors USING gin (specializations);

-- Boolean indexes for contractor characteristics
CREATE INDEX idx_contractors_home_contractor ON contractors (is_home_contractor) WHERE is_home_contractor IS NOT NULL;
CREATE INDEX idx_contractors_priority_category ON contractors (priority_category) WHERE priority_category = TRUE;
CREATE INDEX idx_contractors_residential_focus ON contractors (residential_focus) WHERE residential_focus = TRUE;

-- Website-related indexes
CREATE INDEX idx_contractors_website_status ON contractors (website_status);
CREATE INDEX idx_contractors_website_confidence ON contractors (website_confidence) WHERE website_confidence IS NOT NULL;

-- Mailer categories indexes
CREATE INDEX idx_mailer_categories_name ON mailer_categories (category_name);
CREATE INDEX idx_mailer_categories_priority ON mailer_categories (priority) WHERE priority = TRUE;
CREATE INDEX idx_mailer_categories_active ON mailer_categories (active, sort_order) WHERE active = TRUE;
CREATE INDEX idx_mailer_categories_keywords ON mailer_categories USING gin (keywords);

-- Website searches indexes
CREATE INDEX idx_website_searches_contractor ON website_searches (contractor_id, attempted_at);
CREATE INDEX idx_website_searches_method ON website_searches (search_method, attempted_at);
CREATE INDEX idx_website_searches_success ON website_searches (success, attempted_at);

-- Website crawls indexes
CREATE INDEX idx_website_crawls_contractor ON website_crawls (contractor_id, attempted_at);
CREATE INDEX idx_website_crawls_url ON website_crawls (url);
CREATE INDEX idx_website_crawls_status ON website_crawls (crawl_status, attempted_at);
CREATE INDEX idx_website_crawls_hash ON website_crawls (content_hash) WHERE content_hash IS NOT NULL;

-- Manual review queue indexes
CREATE INDEX idx_manual_review_priority ON manual_review_queue (queue_priority, created_at);
CREATE INDEX idx_manual_review_assigned ON manual_review_queue (assigned_to, created_at) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_manual_review_deadline ON manual_review_queue (review_deadline) WHERE review_deadline IS NOT NULL;

-- Export batches indexes
CREATE INDEX idx_export_batches_date ON export_batches (export_date);
CREATE INDEX idx_export_batches_status ON export_batches (status);

-- Processing logs indexes
CREATE INDEX idx_processing_logs_contractor ON processing_logs (contractor_id, started_at);
CREATE INDEX idx_processing_logs_step ON processing_logs (processing_step, step_status, started_at);
CREATE INDEX idx_processing_logs_status ON processing_logs (step_status, started_at);