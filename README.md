# Complete Implementation Plan: Contractor Data Enrichment System

# Complete Implementation Plan: Contractor Data Enrichment System

## Technology Stack

- **Database**: PostgreSQL 15+
- **Backend**: Python 3.11+ (background process, no web framework)
- **LLM APIs**:
  - GPT-4o-mini for website discovery and initial analysis
  - GPT-4o for verification and quality metrics
- **Web Scraping**: Crawl4AI
- **Task Queue**: Python asyncio with simple queue management
- **Deployment**: Cursor background process

## Phase 0: Project Setup & Initial Data Import

### Project Structure

```
contractor_enrichment/
├── data/
│   ├── contractors.csv              # Your initial contractor data
│   └── Mailer_Categories_2025_07_21.csv  # Your categories data
├── sql/
│   ├── 01_create_schema.sql         # Database schema creation
│   ├── 02_create_indexes.sql        # Performance indexes
│   ├── 03_insert_categories.sql     # Load mailer categories
│   └── 04_import_contractors.sql    # Import initial contractors
├── src/
│   ├── __init__.py
│   ├── main.py                      # Main application entry point
│   ├── config.py                    # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py            # Database connection pool
│   │   ├── models.py                # Data models
│   │   └── queries.py               # SQL queries
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── website_discovery.py     # Website search logic
│   │   ├── web_scraper.py           # Crawl4AI wrapper
│   │   ├── llm_analyzer.py          # GPT API integration
│   │   └── quality_checker.py       # Quality verification
│   ├── services/
│   │   ├── __init__.py
│   │   ├── contractor_service.py    # Business logic
│   │   ├── export_service.py        # CSV export
│   │   └── queue_service.py         # Task queue management
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py        # Logging setup
│       ├── helpers.py               # Utility functions
│       └── constants.py             # Constants and enums
├── scripts/
│   ├── setup_database.py           # Database initialization
│   ├── import_data.py               # Data import utilities
│   └── run_processing.py           # Main processing script
├── tests/
│   ├── __init__.py
│   ├── test_processors/
│   ├── test_services/
│   └── conftest.py
├── exports/                         # Output directory for CSV exports
├── logs/                           # Application logs
├── requirements.txt
├── .env.template
├── .env                            # Environment variables (not in git)
├── README.md
├── setup.py
└── docker-compose.yml              # Optional: for local PostgreSQL
```

### Environment Setup

**requirements.txt**

```
asyncpg>=0.29.0
crawl4ai>=0.2.0
openai>=1.0.0
python-dotenv>=1.0.0
asyncio-throttle>=1.0.0
aiohttp>=3.8.0
pandas>=2.0.0
psutil>=5.9.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

**.env.template** (copy to .env and fill in values)

```
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=contractor_enrichment
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
GPT4_MINI_MODEL=gpt-4o-mini
GPT4_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.2
OPENAI_TIMEOUT=60

# Processing Configuration
BATCH_SIZE=10
MAX_CONCURRENT_CRAWLS=5
CRAWL_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# Confidence Thresholds
AUTO_APPROVE_THRESHOLD=0.8
MANUAL_REVIEW_THRESHOLD=0.6

# Rate Limiting (seconds between requests)
SEARCH_DELAY=1.0
LLM_DELAY=0.5

# Search API Keys (optional - for better search results)
SERPAPI_KEY=your_serpapi_key_here
BING_SEARCH_API_KEY=your_bing_api_key_here

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
EXPORT_DIR=./exports
```

### Database Setup Instructions

**Step 1: Create PostgreSQL Database**

```sql
-- Run as postgres superuser
CREATE DATABASE contractor_enrichment;
CREATE USER contractor_app WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE contractor_enrichment TO contractor_app;

-- Connect to contractor_enrichment database
\c contractor_enrichment;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
GRANT ALL ON SCHEMA public TO contractor_app;
```

**Step 2: Import Your Contractor Data**

**Your contractors.csv format** (confirmed fields):

```csv
BusinessName,ContractorLicenseNumber,ContractorLicenseTypeCode,ContractorLicenseTypeCodeDesc,Address1,Address2,City,State,Zip,PhoneNumber,LicenseEffectiveDate,LicenseExpirationDate,BusinessTypeCode,BusinessTypeCodeDesc,SpecialtyCode1,SpecialtyCode1Desc,SpecialtyCode2,SpecialtyCode2Desc,UBI,PrimaryPrincipalName,StatusCode,ContractorLicenseStatus,ContractorLicenseSuspendDate
```

### Data Import Process

**scripts/import_data.py** - Handles CSV import with validation:

```python
# Import process:
# 1. Read data/contractors.csv with UTF-8 encoding
# 2. Validate required fields (BusinessName minimum required)
# 3. Clean phone numbers: standardize to (XXX) XXX-XXXX format
# 4. Parse dates in MM/DD/YYYY or YYYY-MM-DD format
# 5. Handle empty strings as NULL values
# 6. Insert with batch processing (1000 records at a time)
# 7. Generate import summary with success/error counts
# 8. Set all imported records to processing_status = 'pending'
```

**Import command:**

```bash
python scripts/import_data.py --file data/contractors.csv --batch-size 1000
```

### Search API Configuration (SerpAPI)

**Website Discovery Configuration:**

```python
# Search Strategy:
SERPAPI_CONFIG = {
    'results_per_search': 10,  # Get top 10 results per query
    'max_queries_per_contractor': 4,  # Limit queries to prevent API overuse
    'timeout': 15,  # 15 second timeout per search
    'rate_limit': 1.0,  # 1 second between searches (SerpAPI allows 1 req/sec free)
}

# Query Generation Templates (in priority order):
QUERY_TEMPLATES = [
    '"{business_name}" {city} {state} contractor',  # Primary query
    '"{business_name}" {city} {state}',             # Secondary without "contractor"
    '"{business_name}" {phone}',                    # Phone-based search
    '"{business_name}" contractor {state}'          # State-level fallback
]

# Result Filtering Rules:
EXCLUDED_DOMAINS = [
    'facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com',
    'yelp.com', 'yellowpages.com', 'whitepages.com', 'bbb.org',
    'angi.com', 'homeadvisor.com', 'thumbtack.com', 'google.com',
    'bing.com', 'yahoo.com', 'directories.com'
]

# Website Confidence Scoring Algorithm:
# - Business name exact match in title/URL: +40 points
# - Business name partial match: +20 points  
# - City match in content: +15 points
# - State match in content: +10 points
# - Phone number match: +25 points (strong indicator)
# - Domain contains business keywords: +15 points
# - Contains contractor/service keywords: +5 points
# - Professional website indicators: +5 points
# Maximum score: 100 points (converted to 0.0-1.0 scale)
```

### Resource Management for Virtual Server

**Performance Configuration:**

```python
# Concurrent Processing Limits (for virtual server):
MAX_CONCURRENT_SEARCHES = 3      # Limit simultaneous searches
MAX_CONCURRENT_CRAWLS = 2        # Limit simultaneous crawls  
MAX_CONCURRENT_LLM_CALLS = 2     # Limit simultaneous LLM API calls
BATCH_SIZE = 25                  # Process 25 contractors per batch
MEMORY_LIMIT_MB = 1024           # Monitor memory usage
DB_CONNECTION_POOL = 5           # Smaller connection pool

# Rate Limiting (to prevent server overload):
SEARCH_DELAY = 1.2              # 1.2 seconds between searches
CRAWL_DELAY = 2.0               # 2 seconds between crawls
LLM_DELAY = 1.0                 # 1 second between LLM calls
BATCH_PROCESSING_DELAY = 5.0    # 5 seconds between batches

# Error Recovery:
MAX_RETRIES = 2                 # Reduce retries to save resources
EXPONENTIAL_BACKOFF = True      # Increase delays on errors
CIRCUIT_BREAKER_THRESHOLD = 5   # Stop processing after 5 consecutive errors
```

### Manual Review via Database Queries

**Review Status Management:**

```sql
-- Query contractors ready for manual review
SELECT 
    id, business_name, city, state, website_url, mailer_category,
    confidence_score, website_confidence, classification_confidence,
    is_home_contractor, manual_review_reason,
    CASE 
        WHEN confidence_score >= 0.8 THEN 'High Confidence'
        WHEN confidence_score >= 0.6 THEN 'Medium Confidence' 
        ELSE 'Low Confidence'
    END as confidence_level,
    gpt4mini_analysis->>'reasoning' as analysis_reasoning
FROM contractors 
WHERE processing_status = 'manual_review' 
    AND review_status IS NULL
ORDER BY confidence_score ASC, business_name;

-- Approve contractor for final processing
UPDATE contractors 
SET review_status = 'approved', 
    reviewed_at = CURRENT_TIMESTAMP,
    reviewed_by = 'admin_user'
WHERE id = $contractor_id;

-- Reject contractor
UPDATE contractors 
SET review_status = 'rejected',
    reviewed_at = CURRENT_TIMESTAMP, 
    reviewed_by = 'admin_user',
    review_notes = 'Not a home contractor'
WHERE id = $contractor_id;

-- Change category and approve
UPDATE contractors 
SET mailer_category = 'Handyman',
    review_status = 'approved',
    reviewed_at = CURRENT_TIMESTAMP,
    reviewed_by = 'admin_user',
    review_notes = 'Changed category from Plumbing to Handyman'
WHERE id = $contractor_id;

-- Summary queries for review progress
SELECT 
    processing_status,
    review_status,
    COUNT(*) as count
FROM contractors 
GROUP BY processing_status, review_status
ORDER BY processing_status, review_status;
```

**Useful Review Queries:**

```sql
-- Low confidence contractors needing review
SELECT business_name, website_url, confidence_score, manual_review_reason 
FROM contractors 
WHERE confidence_score < 0.6 AND processing_status = 'manual_review';

-- High confidence contractors (can be auto-approved)
SELECT COUNT(*) 
FROM contractors 
WHERE confidence_score >= 0.8 AND processing_status = 'completed';

-- Website discovery success rate
SELECT 
    website_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM contractors 
GROUP BY website_status;

-- Category distribution
SELECT 
    mailer_category,
    priority_category,
    COUNT(*) as count
FROM contractors 
WHERE is_home_contractor = TRUE
GROUP BY mailer_category, priority_category
ORDER BY count DESC;
```

### Manual Review via Database Queries (No Export System)

**All results stored in database for SQL-based analysis and review**

**Review Status Management:**

```sql
-- Query contractors ready for manual review
SELECT 
    id, business_name, city, state, website_url, mailer_category,
    confidence_score, website_confidence, classification_confidence,
    is_home_contractor, manual_review_reason,
    CASE 
        WHEN confidence_score >= 0.8 THEN 'High Confidence'
        WHEN confidence_score >= 0.6 THEN 'Medium Confidence' 
        ELSE 'Low Confidence'
    END as confidence_level,
    gpt4mini_analysis->>'reasoning' as analysis_reasoning
FROM contractors 
WHERE processing_status = 'manual_review' 
    AND review_status IS NULL
ORDER BY confidence_score ASC, business_name;

-- Approve contractor for final processing
UPDATE contractors 
SET review_status = 'approved', 
    reviewed_at = CURRENT_TIMESTAMP,
    reviewed_by = 'admin_user'
WHERE id = $contractor_id;

-- Reject contractor
UPDATE contractors 
SET review_status = 'rejected',
    reviewed_at = CURRENT_TIMESTAMP, 
    reviewed_by = 'admin_user',
    review_notes = 'Not a home contractor'
WHERE id = $contractor_id;

-- Change category and approve
UPDATE contractors 
SET mailer_category = 'Handyman',
    review_status = 'approved',
    reviewed_at = CURRENT_TIMESTAMP,
    reviewed_by = 'admin_user',
    review_notes = 'Changed category from Plumbing to Handyman'
WHERE id = $contractor_id;

-- Summary queries for review progress
SELECT 
    processing_status,
    review_status,
    COUNT(*) as count
FROM contractors 
GROUP BY processing_status, review_status
ORDER BY processing_status, review_status;
```

**Analysis and Reporting Queries:**

```sql
-- Low confidence contractors needing review
SELECT business_name, website_url, confidence_score, manual_review_reason 
FROM contractors 
WHERE confidence_score < 0.6 AND processing_status = 'manual_review';

-- High confidence contractors (can be auto-approved)
SELECT COUNT(*) 
FROM contractors 
WHERE confidence_score >= 0.8 AND processing_status = 'completed';

-- Website discovery success rate
SELECT 
    website_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM contractors 
GROUP BY website_status;

-- Category distribution for home contractors
SELECT 
    mailer_category,
    priority_category,
    COUNT(*) as count
FROM contractors 
WHERE is_home_contractor = TRUE
GROUP BY mailer_category, priority_category
ORDER BY count DESC;

-- Processing pipeline status overview
SELECT 
    processing_status,
    COUNT(*) as count,
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
    END;

-- Quality metrics for completed contractors
SELECT 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'High (0.8+)'
        WHEN confidence_score >= 0.6 THEN 'Medium (0.6-0.8)'
        ELSE 'Low (<0.6)'
    END as confidence_range,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE is_home_contractor = TRUE) as home_contractors,
    ROUND(COUNT(*) FILTER (WHERE is_home_contractor = TRUE) * 100.0 / COUNT(*), 1) as home_contractor_rate
FROM contractors 
WHERE processing_status IN ('completed', 'manual_review')
GROUP BY 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'High (0.8+)'
        WHEN confidence_score >= 0.6 THEN 'Medium (0.6-0.8)'
        ELSE 'Low (<0.6)'
    END
ORDER BY confidence_range DESC;
```

## Additional Missing Components

### 1. **Error Handling & Recovery System**

```python
# Comprehensive error handling for virtual server environment:
# - API rate limits and timeouts with exponential backoff
# - Database connection failures with automatic reconnection
# - Website crawling failures (403, 404, timeouts) with retry logic
# - LLM API errors and token limits with graceful degradation
# - Memory monitoring and cleanup for resource-constrained environment
# - Graceful shutdown on SIGTERM/SIGINT signals
# - Process state persistence for resume capability
```

### 2. **Logging & Monitoring Framework**

```python
# Lightweight monitoring suitable for virtual server:
# - Structured JSON logging with rotation to prevent disk fill
# - Processing progress tracking with periodic status updates
# - Memory and CPU usage monitoring with alerts
# - Error categorization with automatic circuit breakers
# - Daily summary reports via email/webhook
# - Performance metrics: avg processing time, success rates
```

### 3. **Configuration Management**

```python
# Resource-aware configuration:
# - Dynamic batch size adjustment based on available memory
# - Automatic rate limiting based on API response times  
# - Confidence threshold tuning based on manual review outcomes
# - Processing schedule configuration (night processing for heavy loads)
# - Database maintenance scheduling (VACUUM, ANALYZE)
# - Log retention and cleanup policies
```

### 4. **Testing Framework**

```python
# Essential tests for production reliability:
# - Database connection and query tests
# - CSV import validation with sample data
# - Mock LLM API responses for development/testing
# - Website scraping with test HTML content
# - Confidence score calculation accuracy tests
# - Memory leak detection and performance benchmarks
```

### 5. **Performance Optimization for Virtual Server**

```python
# Memory and CPU optimization:
# - Async processing with connection pooling
# - Database query optimization with proper indexing
# - LLM response caching for repeated analyses  
# - Batch processing with memory-efficient data structures
# - Garbage collection tuning for long-running processes
# - Process monitoring with automatic restart on memory threshold
```

### 6. **Data Validation & Quality Assurance**

```python
# Input data validation:
# - Phone number standardization: various formats → (XXX) XXX-XXXX
# - Address normalization and geocoding validation
# - Business name cleaning: remove special chars, standardize case
# - Date parsing: handle MM/DD/YYYY, YYYY-MM-DD, empty values
# - License number format validation by state
# - Duplicate detection based on name + address similarity
```

### 7. **Database Maintenance & Backup**

```sql
-- Automated maintenance for virtual server:
-- Daily VACUUM ANALYZE on large tables
-- Weekly full database backup with compression
-- Log-based point-in-time recovery setup  
-- Index maintenance and statistics updates
-- Partition pruning for time-based data (logs, processing history)
-- Connection monitoring and idle connection cleanup
```

### 8. **Process Management Scripts**

```bash
# Production process management:
# - systemd service file for automatic startup
# - Process health checking and restart logic
# - Graceful shutdown with processing state save
# - Log rotation and compression
# - Resource usage monitoring and alerting
# - Scheduled maintenance tasks
```

## System Complete - Ready for LLM Implementation

**With the clarifications provided, an LLM now has everything needed to build a complete, production-ready contractor enrichment system:**

✅ **Data Model**: Complete schema with your 23 CSV columns + enrichment fields
✅ **Import Process**: Direct mapping from your contractors.csv format  
✅ **Search Strategy**: SerpAPI integration with specific query templates and scoring
✅ **Resource Management**: Virtual server optimized with conservative limits
✅ **Review Process**: SQL-based manual review (no CLI/export needed)
✅ **Storage Strategy**: All analysis results stored in database JSONB fields
✅ **Performance Tuning**: Specific concurrency limits and rate limiting
✅ **Error Handling**: Comprehensive recovery and monitoring system

## Final Implementation Specifications

### **Processing Pipeline**

1. **Import** → Load contractors.csv into PostgreSQL (all records = 'pending')
2. **Website Discovery** → SerpAPI searches with 4 query templates, max 10 results
3. **Content Extraction** → Crawl4AI scraping with LLM-powered structured extraction  
4. **Analysis** → GPT-4o-mini classification + GPT-4o verification
5. **Quality Scoring** → 50/50 website + classification confidence
6. **Review Queue** → Records <0.8 confidence → 'manual_review' status
7. **Database Storage** → All results queryable via SQL

### **Resource Constraints**

- Max 3 concurrent searches, 2 crawls, 2 LLM calls
- 1.2s search delay, 2s crawl delay, 1s LLM delay
- 25 contractors per batch with 5s batch delay
- Memory monitoring with automatic cleanup

### **Manual Review Workflow**  

- Query database for `processing_status = 'manual_review'`
- Review analysis reasoning in `gpt4mini_analysis` JSONB field
- Update `review_status` and `reviewed_by` fields via SQL
- No export system - all data remains queryable in database

### **Quality Assurance**

- Phone standardization to (XXX) XXX-XXXX format
- Date parsing MM/DD/YYYY and YYYY-MM-DD formats
- Business name cleaning and normalization
- Comprehensive error logging and recovery
- Automated database maintenance and backups

**The LLM can now build the complete system with:**

- Full Python codebase with all classes and functions
- Complete database schema with indexes and constraints
- Data import scripts with validation and error handling
- Processing pipeline with concurrent task management
- Configuration system with resource-aware defaults
- Logging, monitoring, and error recovery systems
- Testing framework and deployment scripts

No additional information needed - the system is fully specified!

## Phase 1: Database Schema & Data Model

### Core Tables Structure

**1. contractors table (Main entity)**

- **Primary keys**: id (serial), uuid (UUID)
- **Original input data** (21 fields from your existing data):
  - business_name, contractor_license_number, contractor_license_type_code, contractor_license_type_code_desc
  - address1, address2, city, state, zip, phone_number
  - license_effective_date, license_expiration_date, business_type_code, business_type_code_desc
  - specialty_code1, specialty_code1_desc, specialty_code2, specialty_code2_desc
  - ubi, primary_principal_name, status_code, contractor_license_status, contractor_license_suspend_date

- **Enriched data fields**:
  - is_home_contractor (boolean)
  - mailer_category (varchar) - from your 106 categories
  - priority_category (boolean) - if matches priority category
  - website_url, website_status
  - business_description, tagline, established_year, years_in_business
  - services_offered (text array), service_categories (text array), specializations (text array)
  - additional_licenses, certifications, insurance_types (text arrays)
  - website_email, website_phone, physical_address, social_media_urls (JSONB)
  - residential_focus, commercial_focus, emergency_services, free_estimates, warranty_offered (booleans)

- **Processing & quality fields**:
  - confidence_score, classification_confidence, website_confidence (decimals 0.0-1.0)
  - processing_status, last_processed, error_message
  - manual_review_needed, manual_review_reason

- **Manual review workflow fields**:
  - review_status (pending_review, approved_download, rejected, exported)
  - reviewed_by, reviewed_at, review_notes, manual_review_outcome
  - marked_for_download, marked_for_download_at, exported_at, export_batch_id

- **Analysis storage**:
  - gpt4mini_analysis (JSONB) - stores GPT-4o-mini results
  - gpt4_verification (JSONB) - stores GPT-4o verification results
  - data_sources (JSONB), website_content_hash, processing_attempts

**2. mailer_categories table (Your 106 service categories)**

- record_id, category_name, priority (boolean), afb_name, category
- keywords (text array), typical_services (text array)
- active, sort_order, created_at

**3. website_searches table (Search attempt logging)**

- contractor_id, search_query, search_method, results_found
- search_results (JSONB), attempted_at, success, error_message

**4. website_crawls table (Crawling attempt logging)**

- contractor_id, url, crawl_status, response_code, content_length
- crawl_duration_seconds, content_hash, raw_content, structured_content (JSONB)

**5. manual_review_queue table (Review management)**

- contractor_id, queue_priority, assigned_to, review_deadline
- review_reason, confidence_threshold_failed

**6. export_batches table (Export tracking)**

- batch_id, export_date, exported_by, contractor_count
- file_path, download_count, status

**7. processing_logs table (Detailed processing audit)**

- contractor_id, processing_step, step_status, started_at, completed_at
- details (JSONB), error_message, processing_time_seconds

### Database Indexes & Performance

- Standard indexes on: business_name, processing_status, confidence_score, city/state
- GIN indexes for: services_offered arrays, JSONB fields (gpt analysis data)
- Text search indexes using pg_trgm for fuzzy name matching
- Conditional indexes for manual_review_needed, marked_for_download flags

## Phase 2: Processing Pipeline Architecture

### Core Processing Flow

1. **Input**: Load contractor data into contractors table (status: pending)
2. **Website Discovery**: Search for contractor websites using multiple strategies
3. **Website Scraping**: Use Crawl4AI to extract content and structured data
4. **Initial Analysis**: GPT-4o-mini analyzes content for classification
5. **Quality Verification**: GPT-4o verifies analysis and calculates confidence
6. **Review Queue**: Low confidence records flagged for manual review
7. **Export**: Approved records exported to CSV

### Application Components

**1. Main Controller (main.py)**

- Orchestrates the entire processing pipeline
- Manages batch processing (configurable batch sizes)
- Handles retry logic and error recovery
- Provides status reporting and progress tracking

**2. Website Discovery Service**

- Multiple search strategies: Google, Bing, DuckDuckGo
- Query generation: business name + location, phone number lookups
- Result filtering: excludes social media, directories
- Confidence scoring: name match, location match, domain relevance
- Rate limiting and search attempt logging

**3. Web Scraping Service (Crawl4AI Integration)**

- Asynchronous crawling with configurable timeouts
- JavaScript execution for dynamic content
- Structured data extraction using LLM-powered schemas
- Content hashing for change detection
- Comprehensive crawl logging and error handling

**4. LLM Analysis Service**

- **GPT-4o-mini Analysis**:
  - Input: contractor data + website content + structured data
  - Output: is_home_contractor classification, service category, business details
  - Includes confidence scores and reasoning for each classification
  
- **GPT-4o Verification**:
  - Input: original data + website content + initial analysis
  - Output: verification of classifications, quality assessment, final confidence scores
  - Identifies inconsistencies and recommends manual review

**5. Quality Assessment System**

- **Confidence Score Calculation**: 50% website confidence + 50% classification confidence
- **Review Thresholds**: ≥0.80 (auto-approve), 0.60-0.79 (review), <0.60 (required review)
- **Quality Metrics**: data completeness, consistency, business legitimacy indicators

## Phase 3: Manual Review System

### Review Interface Logic (No Frontend - CLI/Admin Tool)

- **Filter contractors** by confidence levels, categories, processing status
- **Display contractor details** with confidence breakdowns and analysis reasoning
- **Review actions**: Add to Download, Reject, Wrong Category
- **Status tracking**: pending_review → approved_download → exported
- **Batch export** functionality with CSV generation

### Review Dashboard Data

- Contractors needing review (confidence < 0.80)
- Confidence score distributions
- Processing pipeline status
- Category classification accuracy
- Manual review efficiency metrics

## Phase 4: Data Flow & Processing Logic

### Detailed Processing Steps

1. **Initialization**: Load pending contractors from database
2. **Website Search**:
   - Generate search queries using business name, location, phone
   - Execute searches across multiple search engines
   - Filter results and calculate website confidence scores
   - Store top 3-5 website candidates per contractor

3. **Website Analysis**:
   - Crawl each candidate website using Crawl4AI
   - Extract content using structured schemas
   - Store raw content and structured data
   - Calculate crawl success metrics

4. **LLM Classification**:
   - **First Pass (GPT-4o-mini)**: Classify as home contractor, assign service category
   - **Second Pass (GPT-4o)**: Verify classifications and assess quality
   - Store both analysis results in JSONB fields
   - Calculate final confidence scores

5. **Quality Assessment**:
   - Combine website confidence + classification confidence
   - Apply business rules and consistency checks
   - Determine if manual review is needed
   - Update contractor status accordingly

6. **Manual Review Queue**:
   - Queue low-confidence records for human review
   - Provide analysis summaries and confidence breakdowns
   - Track review decisions and outcomes
   - Update confidence thresholds based on review patterns

7. **Export Processing**:
   - Generate CSV exports for approved contractors
   - Include original fields + enriched data + confidence scores
   - Track export batches and download history
   - Update contractor status to 'exported'

## Phase 5: Configuration & Quality Control

### Key Configuration Parameters

- **Processing**: Batch sizes, concurrent limits, timeout values
- **Confidence Thresholds**: Auto-approval, manual review triggers
- **Rate Limiting**: Search delays, LLM API delays
- **Quality Metrics**: Minimum confidence scores, data completeness requirements

### Success Metrics & Monitoring

- **Processing Accuracy**: >90% approval rate for high-confidence records
- **Efficiency**: <2 minutes average manual review time
- **Quality**: Confidence scores correlate with manual review outcomes
- **Throughput**: Contractors processed per hour
- **Data Completeness**: % of exported records with complete data

### Error Handling & Recovery

- **Retry Logic**: Automatic retries for failed searches/crawls
- **Graceful Degradation**: Continue processing when individual components fail
- **Error Logging**: Comprehensive logging for debugging and monitoring
- **Data Integrity**: Transaction management and rollback capabilities

## Phase 6: Deployment & Operations

### Cursor Background Process Setup

- **Environment Configuration**: Database connections, API keys, processing parameters
- **Process Management**: Start/stop/restart capabilities, status monitoring
- **Logging**: Structured logging with configurable levels
- **Resource Management**: Memory usage, connection pooling, rate limiting

### Monitoring & Maintenance

- **Progress Tracking**: Real-time processing status and completion rates
- **Quality Monitoring**: Confidence score distributions and accuracy trends
- **Performance Metrics**: Processing speed, error rates, resource usage
- **Data Quality Reports**: Export success rates, manual review patterns

This implementation plan provides a complete, scalable system for enriching contractor data using modern LLM technology while maintaining data quality through confidence scoring and manual review workflows.
