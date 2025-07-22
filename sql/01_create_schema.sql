-- Main contractor enrichment database schema
-- PostgreSQL 15+ required

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Main contractors table (core entity)
CREATE TABLE contractors (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    
    -- Original contractor data fields (from CSV)
    business_name VARCHAR(255) NOT NULL,
    contractor_license_number VARCHAR(50),
    contractor_license_type_code VARCHAR(10),
    contractor_license_type_code_desc VARCHAR(100),
    address1 VARCHAR(255),
    address2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    zip VARCHAR(20),
    phone_number VARCHAR(50),
    license_effective_date DATE,
    license_expiration_date DATE,
    business_type_code VARCHAR(10),
    business_type_code_desc VARCHAR(100),
    specialty_code1 VARCHAR(10),
    specialty_code1_desc VARCHAR(100),
    specialty_code2 VARCHAR(10),
    specialty_code2_desc VARCHAR(100),
    ubi VARCHAR(20),
    primary_principal_name VARCHAR(255),
    status_code VARCHAR(10),
    contractor_license_status VARCHAR(50),
    contractor_license_suspend_date DATE,
    
    -- Enriched data fields
    is_home_contractor BOOLEAN,
    mailer_category VARCHAR(100),
    priority_category BOOLEAN DEFAULT FALSE,
    website_url VARCHAR(500),
    website_status VARCHAR(50), -- 'found', 'not_found', 'error', 'invalid'
    business_description TEXT,
    tagline VARCHAR(255),
    established_year INTEGER,
    years_in_business INTEGER,
    services_offered TEXT[],
    service_categories TEXT[],
    specializations TEXT[],
    additional_licenses TEXT[],
    certifications TEXT[],
    insurance_types TEXT[],
    website_email VARCHAR(255),
    website_phone VARCHAR(50),
    physical_address TEXT,
    social_media_urls JSONB,
    residential_focus BOOLEAN,
    commercial_focus BOOLEAN,
    emergency_services BOOLEAN,
    free_estimates BOOLEAN,
    warranty_offered BOOLEAN,
    
    -- Processing and quality fields
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    classification_confidence DECIMAL(3,2) CHECK (classification_confidence >= 0 AND classification_confidence <= 1),
    website_confidence DECIMAL(3,2) CHECK (website_confidence >= 0 AND website_confidence <= 1),
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN 
        ('pending', 'processing', 'completed', 'manual_review', 'error')),
    last_processed TIMESTAMP,
    error_message TEXT,
    manual_review_needed BOOLEAN DEFAULT FALSE,
    manual_review_reason TEXT,
    
    -- Manual review workflow fields
    review_status VARCHAR(50) CHECK (review_status IN 
        ('pending_review', 'approved_download', 'rejected', 'exported')),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    manual_review_outcome VARCHAR(50),
    marked_for_download BOOLEAN DEFAULT FALSE,
    marked_for_download_at TIMESTAMP,
    exported_at TIMESTAMP,
    export_batch_id INTEGER,
    
    -- Analysis storage
    gpt4mini_analysis JSONB,
    gpt4_verification JSONB,
    data_sources JSONB,
    website_content_hash VARCHAR(64),
    processing_attempts INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Mailer categories table (service categories)
CREATE TABLE mailer_categories (
    record_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    priority BOOLEAN DEFAULT FALSE,
    afb_name VARCHAR(100),
    category VARCHAR(100),
    keywords TEXT[],
    typical_services TEXT[],
    active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Website searches table (search attempt logging)
CREATE TABLE website_searches (
    id SERIAL PRIMARY KEY,
    contractor_id INTEGER REFERENCES contractors(id) ON DELETE CASCADE,
    search_query VARCHAR(500),
    search_method VARCHAR(50), -- 'serpapi', 'google', 'bing', 'duckduckgo'
    results_found INTEGER DEFAULT 0,
    search_results JSONB,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- 4. Website crawls table (crawling attempt logging)
CREATE TABLE website_crawls (
    id SERIAL PRIMARY KEY,
    contractor_id INTEGER REFERENCES contractors(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    crawl_status VARCHAR(50), -- 'success', 'timeout', 'error', '403', '404'
    response_code INTEGER,
    content_length INTEGER,
    crawl_duration_seconds DECIMAL(6,3),
    content_hash VARCHAR(64),
    raw_content TEXT,
    structured_content JSONB,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Manual review queue table (review management)
CREATE TABLE manual_review_queue (
    id SERIAL PRIMARY KEY,
    contractor_id INTEGER REFERENCES contractors(id) ON DELETE CASCADE,
    queue_priority INTEGER DEFAULT 50,
    assigned_to VARCHAR(100),
    review_deadline TIMESTAMP,
    review_reason TEXT,
    confidence_threshold_failed DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Export batches table (export tracking)
CREATE TABLE export_batches (
    batch_id SERIAL PRIMARY KEY,
    export_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_by VARCHAR(100),
    contractor_count INTEGER,
    file_path VARCHAR(500),
    download_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted'))
);

-- 7. Processing logs table (detailed processing audit)
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    contractor_id INTEGER REFERENCES contractors(id) ON DELETE CASCADE,
    processing_step VARCHAR(100), -- 'website_discovery', 'crawling', 'llm_analysis', 'verification'
    step_status VARCHAR(50), -- 'started', 'completed', 'failed', 'retrying'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    details JSONB,
    error_message TEXT,
    processing_time_seconds DECIMAL(8,3)
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to contractors table
CREATE TRIGGER update_contractors_updated_at BEFORE UPDATE ON contractors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply updated_at trigger to manual_review_queue table
CREATE TRIGGER update_manual_review_queue_updated_at BEFORE UPDATE ON manual_review_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();