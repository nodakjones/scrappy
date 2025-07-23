# Technical Specification: Contractor Data Enrichment System

## Technology Stack

- **Database**: PostgreSQL 15+
- **Backend**: Python 3.11+ (background process, no web framework)
- **LLM APIs**:
  - GPT-4o-mini for website discovery and initial analysis
  - GPT-4o for verification and quality metrics
- **Web Scraping**: Crawl4AI
- **Task Queue**: Python asyncio with simple queue management
- **Deployment**: Cursor background process

## Database Schema & Data Model

### Core Tables Structure

**1. contractors table (Main entity)**

- **Primary keys**: id (serial), uuid (UUID)
- **Original input data** (21 fields from CSV):
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

**2. Supporting Tables**

- mailer_categories (service categories)
- website_searches (search attempt logging)
- website_crawls (crawling attempt logging)
- manual_review_queue (review management)
- export_batches (export tracking)
- processing_logs (detailed processing audit)

### Database Indexes & Performance

- Standard indexes on: business_name, processing_status, confidence_score, city/state
- GIN indexes for: services_offered arrays, JSONB fields (gpt analysis data)
- Text search indexes using pg_trgm for fuzzy name matching
- Conditional indexes for manual_review_needed, marked_for_download flags

## Environment Configuration

### Required Environment Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=contractor_enrichment
DB_USER=postgres
DB_PASSWORD=your_password_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
GPT4_MINI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.2

# Google Search Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Processing Configuration
BATCH_SIZE=10
MAX_CONCURRENT_CRAWLS=5
CRAWL_TIMEOUT=30

# Confidence Thresholds
AUTO_APPROVE_THRESHOLD=0.8
MANUAL_REVIEW_THRESHOLD=0.6

# Rate Limiting (seconds between requests)
SEARCH_DELAY=1.0
LLM_DELAY=0.5
```

## Implementation Architecture

### Project Structure

```
contractor_enrichment/
├── data/
│   └── contractors.csv              # Initial contractor data
├── sql/
│   ├── 01_create_schema.sql         # Database schema creation
│   ├── 02_create_indexes.sql        # Performance indexes
│   └── 03_insert_categories.sql     # Load mailer categories
├── src/
│   ├── main.py                      # Main application entry point
│   ├── config.py                    # Configuration management
│   ├── database/
│   │   ├── connection.py            # Database connection pool
│   │   ├── models.py                # Data models
│   │   └── queries.py               # SQL queries
│   ├── processors/
│   │   ├── website_discovery.py     # Website search logic
│   │   ├── web_scraper.py           # Crawl4AI wrapper
│   │   ├── llm_analyzer.py          # GPT API integration
│   │   └── quality_checker.py       # Quality verification
│   └── services/
│       ├── contractor_service.py    # Business logic
│       └── export_service.py        # CSV export
├── scripts/
│   ├── setup_database.py           # Database initialization
│   ├── import_data.py               # Data import utilities
│   └── run_processing.py           # Main processing script
├── tests/
├── exports/                         # Output directory
├── logs/                           # Application logs
└── requirements.txt
```

### Required Dependencies

```
asyncpg>=0.29.0
crawl4ai>=0.2.0
openai>=1.0.0
python-dotenv>=1.0.0
aiohttp>=3.8.0
pandas>=2.0.0
psutil>=5.9.0
beautifulsoup4>=4.12.0
```

## Website Discovery Implementation

### Search Configuration

**Query Generation Templates:**
```python
QUERY_TEMPLATES = [
    '"{business_name}" {city} {state} contractor',  # Primary query
    '"{business_name}" {city} {state}',             # Secondary without "contractor"
    '"{business_name}" {phone}',                    # Phone-based search
    '"{business_name}" contractor {state}'          # State-level fallback
]
```

**Excluded Domains:**
```python
EXCLUDED_DOMAINS = [
    'yelp.com', 'bbb.org', 'angieslist.com', 'angi.com', 'homeadvisor.com',
    'thumbtack.com', 'yellowpages.com', 'facebook.com', 'linkedin.com',
    'google.com/maps', 'zillow.com', 'buildzoom.com'
]
```

### 7-Step Processing Implementation

**Step 1: Google Custom Search API Query**
```python
# Build search query with contractor information
query = f'"{contractor.business_name}" {contractor.city} {contractor.state} contractor'
params = {
    'key': GOOGLE_API_KEY,
    'cx': SEARCH_ENGINE_ID, 
    'q': query,
    'num': 10  # Maximum 10 results per query
}
search_results = google_custom_search_api.get(params)
```

**Step 2: Directory & Listing Website Filtering**
```python
filtered_results = []
for result in search_results:
    url = result.get('link', '')
    if not any(excluded in url.lower() for excluded in EXCLUDED_DOMAINS):
        if not any(pattern in url.lower() for pattern in ['search?', 'results?', 'find?']):
            filtered_results.append(result)
```

**Step 3: Website Content Crawling**
```python
for result in filtered_results:
    url = result.get('link')
    try:
        response = await aiohttp_session.get(url, timeout=30)
        if response.status == 200:
            html_content = await response.text()
            
            # Extract meaningful content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script, style, nav, footer elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            website_content = {
                'title': soup.title.string if soup.title else '',
                'full_text': soup.get_text().upper(),
                'meta_description': soup.find('meta', {'name': 'description'})
            }
    except Exception as e:
        continue  # Skip failed crawls, try next result
```

**Step 4: 5-Factor + Geographic Confidence Scoring**
```python
def calculate_confidence_score(website_content, contractor):
    website_text = website_content.get('full_text', '').upper()
    
    # Factor 1: Business Name Match (0.25 points)
    name_score = score_name_match(website_text, contractor.business_name)
    
    # Factor 2: License Number Match (0.25 points)
    license_score = score_license_match(website_text, contractor.license_number)
    
    # Factor 3: Phone Number Match (0.25 points)  
    phone_score = score_phone_match(website_text, contractor.phone_number)
    
    # Factor 4: Principal Name Match (0.25 points) - Currently 0.0
    principal_score = 0.0
    
    # Factor 5: Address Match (0.25 points)
    address_score = score_address_match(website_text, contractor.address)
    
    # Calculate base confidence
    base_confidence = (name_score + license_score + phone_score + 
                      principal_score + address_score) * 0.25
    
    # Apply geographical penalty if needed
    geographic_penalty = calculate_geographic_penalty(website_text)
    
    final_confidence = min(base_confidence + geographic_penalty, 1.0)
    return final_confidence
```

**Step 5: Confidence Threshold Validation**
```python
for website_result in filtered_results:
    crawled_content = crawl_website(website_result['link'])
    if crawled_content:
        confidence = calculate_confidence_score(crawled_content, contractor)
        
        if confidence >= 0.4:  # Minimum threshold met
            validated_website = {
                'url': website_result['link'],
                'content': crawled_content,
                'confidence': confidence
            }
            break  # Stop searching, use first valid website
        else:
            continue  # Try next website
```

**Step 6: Free Enrichment Fallback**
```python
if not validated_website:
    # Try Clearbit API (free tier)
    clearbit_domain = await try_clearbit_enrichment(contractor.business_name)
    if clearbit_domain:
        clearbit_url = f"https://{clearbit_domain}"
        crawled_content = crawl_website(clearbit_url)
        if crawled_content:
            confidence = calculate_confidence_score(crawled_content, contractor)
            if confidence >= 0.6:  # Higher threshold for guessed domains
                validated_website = {'url': clearbit_url, 'content': crawled_content}
```

**Step 7: AI Analysis Decision**
```python
if validated_website:
    ai_analysis = await analyze_with_openai_gpt4_mini(
        contractor_data=contractor,
        website_content=validated_website['content'],
        search_results=search_results
    )
    
    # Combine website confidence (60%) + AI classification confidence (40%)
    final_confidence = (validated_website['confidence'] * 0.6) + (ai_analysis['confidence'] * 0.4)
    
    await update_contractor_database(contractor.id, {
        'website_url': validated_website['url'],
        'website_confidence': validated_website['confidence'],
        'classification_confidence': ai_analysis['confidence'],
        'confidence_score': final_confidence,
        'processing_status': 'completed' if final_confidence >= 0.8 else 'manual_review'
    })
else:
    await update_contractor_database(contractor.id, {
        'website_url': None,
        'confidence_score': 0.0,
        'processing_status': 'completed',
        'category': 'No Website',
        'skipped_reason': 'No validated website found'
    })
```

## Geographic Validation Implementation

### Area Code Detection
```python
# Puget Sound region area codes (excluding 509 eastern WA)
wa_area_codes = ['206', '253', '360', '425']

# Check multiple phone number formats
patterns = [
    f'\\({area_code}\\)',      # (206)
    f'{area_code}-',           # 206-
    f'{area_code}\\.', 	       # 206.
    f' {area_code} ',          # space 206 space
    f'{area_code}\\d{{7}}',    # 2065551234 (10-digit)
]
```

### Local City Detection
```python
# Puget Sound region cities and references
washington_indicators = [
    'WASHINGTON', 'WA ', ' WA,', ' WA.', 'WASHINGTON STATE',
    'SEATTLE', 'TACOMA', 'BELLEVUE', 'EVERETT', 'KENT', 'RENTON',
    'FEDERAL WAY', 'KIRKLAND', 'BELLINGHAM', 'KENNEWICK', 'AUBURN',
    'MARYSVILLE', 'LAKEWOOD', 'REDMOND', 'SHORELINE', 'RICHLAND', 'OLYMPIA',
    'LACEY', 'EDMONDS', 'BURIEN', 'BOTHELL', 'LYNNWOOD', 'LONGVIEW',
    'WENATCHEE', 'MOUNT VERNON', 'CENTRALIA', 'ANACORTES', 'UNIVERSITY PLACE', 
    'MUKILTEO', 'TUKWILA', 'BREMERTON', 'CHEHALIS', 'PORT ORCHARD',
    'MAPLE VALLEY', 'OAK HARBOR', 'FERNDALE', 'MOUNTLAKE TERRACE',
    'PUGET SOUND', 'KING COUNTY', 'PIERCE COUNTY', 'SNOHOMISH COUNTY',
    'SERVING SEATTLE', 'SERVING TACOMA', 'SERVING BELLEVUE',
    'SEATTLE AREA', 'TACOMA AREA', 'GREATER SEATTLE',
    'PACIFIC NORTHWEST', 'PNW ', 'NORTHWESTERN', 'WA LICENSE'
]
```

### Penalty Application
```python
def calculate_geographic_penalty(website_text):
    # Apply -0.20 penalty if NEITHER area codes NOR local references found
    if not area_code_found and not local_reference_found:
        return -0.20  # Geographic penalty
    else:
        return 0.0   # No penalty
```

## AI Analysis Implementation

### OpenAI Integration

**GPT-4o-mini Analysis Prompt:**
```python
prompt = f"""
Analyze this contractor business and provide categorization:

Business: {context['business_name']}
Location: {context['location']}
License Type: {context['license_type']}
Phone: {context['phone']}

Website Content:
{json.dumps(context['website_content'], indent=2)}

Please provide a JSON response with:
1. "category" - USE SPECIFIC CATEGORIES: Plumbing, HVAC, Electrical, Roofing, Handyman, etc.
2. "subcategory" - specific service type
3. "confidence" - confidence score 0-1
4. "website" - business website if found
5. "description" - brief business description
6. "services" - array of main services offered
7. "verified" - true if search results confirm real business
8. "is_residential" - true if primarily serves homeowners

IMPORTANT: For "is_residential", use EVIDENCE-BASED analysis:
- IF website content available, analyze for market indicators
- Mark "true" for: "homeowners", "residential services", "home repair"
- Mark "false" for: "commercial clients", "business services", "industrial"
- If uncertain, mark as null

Respond with valid JSON only.
"""

response = openai_client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4096,
    temperature=0.2
)
```

## Performance Configuration

### Resource Management for Virtual Server

```python
# Concurrent Processing Limits
MAX_CONCURRENT_SEARCHES = 3      # Limit simultaneous searches
MAX_CONCURRENT_CRAWLS = 2        # Limit simultaneous crawls  
MAX_CONCURRENT_LLM_CALLS = 2     # Limit simultaneous LLM API calls
BATCH_SIZE = 25                  # Process 25 contractors per batch

# Rate Limiting
SEARCH_DELAY = 1.2              # 1.2 seconds between searches
CRAWL_DELAY = 2.0               # 2 seconds between crawls
LLM_DELAY = 1.0                 # 1 second between LLM calls
BATCH_PROCESSING_DELAY = 5.0    # 5 seconds between batches

# Error Recovery
MAX_RETRIES = 2                 # Reduce retries to save resources
EXPONENTIAL_BACKOFF = True      # Increase delays on errors
CIRCUIT_BREAKER_THRESHOLD = 5   # Stop processing after 5 consecutive errors
```

## Database Operations

### Manual Review Queries

**Query contractors ready for manual review:**
```sql
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
```

**Approve contractor:**
```sql
UPDATE contractors 
SET review_status = 'approved', 
    reviewed_at = CURRENT_TIMESTAMP,
    reviewed_by = 'admin_user'
WHERE id = $contractor_id;
```

**Processing status overview:**
```sql
SELECT 
    processing_status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence,
    MIN(confidence_score) as min_confidence,
    MAX(confidence_score) as max_confidence
FROM contractors 
GROUP BY processing_status
ORDER BY processing_status;
```

## Data Import Process

### CSV Import Implementation

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

## Error Handling & Recovery

### Comprehensive Error Handling

- API rate limits and timeouts with exponential backoff
- Database connection failures with automatic reconnection
- Website crawling failures (403, 404, timeouts) with retry logic
- LLM API errors and token limits with graceful degradation
- Memory monitoring and cleanup for resource-constrained environment
- Graceful shutdown on SIGTERM/SIGINT signals
- Process state persistence for resume capability

### Logging & Monitoring

- Structured JSON logging with rotation to prevent disk fill
- Processing progress tracking with periodic status updates
- Memory and CPU usage monitoring with alerts
- Error categorization with automatic circuit breakers
- Daily summary reports via email/webhook
- Performance metrics: avg processing time, success rates

## Deployment & Operations

### Database Setup

```sql
-- Create PostgreSQL Database
CREATE DATABASE contractor_enrichment;
CREATE USER contractor_app WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE contractor_enrichment TO contractor_app;

-- Enable required extensions
\c contractor_enrichment;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
GRANT ALL ON SCHEMA public TO contractor_app;
```

### System Installation

```bash
# 1. Clone repository and install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.template .env
# Edit .env with your API keys and database credentials

# 3. Initialize database
python scripts/setup_database.py

# 4. Import contractor data
python scripts/import_data.py --file data/contractors.csv

# 5. Start processing
python scripts/run_processing.py
```

### Monitoring & Maintenance

- Progress tracking: Real-time processing status and completion rates
- Quality monitoring: Confidence score distributions and accuracy trends
- Performance metrics: Processing speed, error rates, resource usage
- Data quality reports: Export success rates, manual review patterns