# Contractor Data Enrichment System

*An AI-powered system for automatically validating, categorizing, and enriching contractor business data*

---

## Overview

The Contractor Data Enrichment System processes contractor license data to identify legitimate residential service providers in the Puget Sound region. The system validates contractors by finding and analyzing their business websites, then uses AI to categorize their services and determine if they serve residential customers.

**Key Features:**
- **Website Discovery**: Finds legitimate business websites using Google Search
- **Anti-Fraud Validation**: 5-factor confidence scoring prevents wrong business matches  
- **Geographic Filtering**: Focuses on Puget Sound region contractors (excludes eastern WA)
- **AI Categorization**: Analyzes websites to determine residential vs commercial focus
- **Quality Control**: Automated confidence scoring with manual review workflow

---

## Processing Workflow

### High-Level Process

```
📥 Import Contractor Data
    ↓
🔍 Website Discovery (Google Search + Clearbit API)
    ↓
🕷️ Comprehensive Crawling (Multi-page analysis)
    ↓
🛡️ Website Validation (5-Factor Confidence Scoring)
    ↓
🤖 AI Analysis (GPT-4o-mini categorization)
    ↓
📊 AI Confidence Direct Assignment
    ↓
🎯 Status Assignment (Auto-approve/Manual Review/Reject)
```

### Enhanced Discovery Features

**Simplified Search Queries**: The system uses 3 focused search strategies:
1. `"{full business name}" {city} {state}` - Exact business name with location
2. `"{simple business name}" {city} {state}` - Business name without LLC/INC with location  
3. `"{simple business name}" {state}` - Business name without LLC/INC with state only

**Business Name Simplification**: Removes common business designations (LLC, INC, CORP) while preserving important descriptive words like "CONSTRUCTION", "ELECTRIC", "REMODELING".

**Consolidated Logging**: Google search results are logged in a single, comprehensive entry showing the query, status, response keys, and result summary instead of multiple separate debug entries.

**Comprehensive Domain Filtering**: Excludes government sites (`.gov`, `.org`, `.codes`), directory sites, and social media platforms to focus on legitimate business websites.

### Detailed Steps

1. **Data Import**: Load contractor CSV data into PostgreSQL database
2. **Website Search**: Use Google Custom Search to find potential business websites
3. **Website Filtering**: Remove directories, social media, and listing sites
4. **Website Validation**: Apply 5-factor confidence scoring to ensure correct business
5. **AI Analysis**: Use OpenAI GPT-4o-mini to analyze website content and categorize business
6. **Quality Assessment**: Combine website and AI confidence scores
7. **Status Assignment**: Auto-approve high confidence, flag low confidence for manual review

---

## Website Confidence Scoring System

The system uses a **two-stage validation process** to ensure discovered websites actually belong to the correct contractor and are legitimate residential service providers.

### Stage 1: Website Validation (6-Factor System)

**Purpose**: Determine if the discovered website belongs to the correct contractor business.

**6-Factor Validation (0.20 points each, 1.2 maximum)**

**Factor 1: Business Name Match (0.20 points)**
- Exact business name found on website = 1.0 score
- Partial matches: 80%+ words = 1.0, 60%+ = 0.6, 40%+ = 0.3
- Removes common suffixes (LLC, INC, CORP) for better matching

**Factor 2: License Number Match (0.20 points)**
- Contractor license number found anywhere on website = 1.0 score
- Strongest validation factor when present
- Handles various formats (with/without asterisks)

**Factor 3: Phone Number Match (0.20 points)**
- **Normalized Matching**: Removes all non-digits (dashes, parentheses, periods, spaces) from both database and website content
- **Full String Match**: Matches the entire normalized phone number string (e.g., "2065551234")
- **Pattern Matching**: Looks for phone numbers with labels (Phone:, Tel:, Call:, Contact:)
- **Supports Multiple Formats**: (206) 555-1234, 206-555-1234, 206.555.1234, 2065551234
- **Minimum Length**: Requires at least 10 digits for valid phone number matching
- **Case Insensitive**: Converts both database and website content to lowercase for matching

**Factor 4: Principal Name Match (0.20 points)**
- **Case Insensitive Matching**: Converts both database and website content to lowercase
- **Word Boundary Matching**: Uses regex word boundaries to avoid partial matches
- **Individual Word Matching**: Matches individual words from principal name (minimum 3 characters)
- **Handles Variations**: Middle initials, suffixes, different formatting
- **Context Aware**: Looks for names in "About Us", contact sections, owner information

**Factor 5: Address Match (0.20 points)**
- Exact street number match = 1.0 score
- Partial credit for street name components
- Most effective for contractors with physical storefronts

**Factor 6: Domain Name Business Word Match (0.20 points)**
- **Business Word Extraction**: Extracts significant words from business name (filters out LLC, INC, CORP, etc.)
- **Domain Matching**: Counts how many business name words appear in the website domain
- **Scoring**: Each matched word = 0.10 points, maximum 0.20 points (2 words)
- **Examples**: 
  - "360 POWER LLC" → "powercore360.com" = 0.20 (matches "360", "power")
  - "365 PLUMBING LLC" → "365plumbingseattle.com" = 0.20 (matches "365", "plumbing")
  - "3 BRIDGES ELECTRIC" → "3bridgeselectric.com" = 0.20 (matches "3", "bridges", "electric")

### Geographic Validation (During Discovery)

**CRITICAL ANTI-FRAUD PROTECTION**: Geographic validation happens during the website discovery phase, not as a penalty in the 5-factor validation.

**Websites are filtered out during discovery if:**
- No Puget Sound area codes found (206, 253, 360, 425) **AND**
- No local address references found (Seattle, Tacoma, Bellevue, etc.)

**Multi-Area Service Logic:**
- "Serving Seattle, Tacoma, and Spokane" = ✅ **ACCEPTED** (includes local areas)
- "Serving Spokane and Yakima only" = ❌ **FILTERED OUT** (no local presence)

**Implementation Note**: Geographic validation is implemented in the website discovery methods (`enhanced_website_discovery`, `search_google_api`, etc.) to filter out non-local websites before they reach the 5-factor validation stage. The system also uses business name variations and consolidated logging for improved search accuracy.

### Website Validation Threshold

**Minimum 0.4 confidence required** (at least 2 factors must match) for website acceptance:
- **≥ 0.4**: Website accepted, proceed to AI analysis
- **< 0.4**: Website rejected, continue searching other results

### Stage 2: AI Business Classification

**Purpose**: Analyze website content to determine business type, service categories, and residential focus.

**AI Analysis Components:**
- **Residential Focus Analysis** (40% weight): Keywords like "residential", "home", "family"
- **Contractor Service Analysis** (30% weight): Keywords like "plumbing", "electrical", "hvac"
- **Business Legitimacy Analysis** (20% weight): Keywords like "licensed", "insured", "certified"
- **Business Name Relevance** (10% weight): Business name appears in content

**AI Confidence Score**: 0.0-1.0 based on content analysis

---

## Combined Confidence Scoring

The system calculates a final confidence score that determines the contractor's processing status using a **two-stage validation process**.

### Confidence Calculation Process

**Stage 1: Website Discovery & Validation**
1. **Website Discovery**: Find potential websites using Google Search, Clearbit API
2. **Website Validation**: Apply 5-factor validation system (business name, license, phone, principal, address)
3. **Website Confidence**: 0.0-1.0 based on 5-factor validation results

**Stage 2: AI Classification (Only if Website Confidence ≥ 0.25)**
1. **AI Analysis**: Analyze website content for business categorization using comprehensive crawling
2. **Classification Confidence**: 0.0-1.0 based on AI analysis of residential focus, service types, legitimacy

**Final Combined Formula:**
```
When Website Confidence ≥ 0.25:
    Final Confidence = AI Classification Confidence (direct use)

When Website Confidence < 0.25:
    Final Confidence = Website Confidence (AI analysis skipped)
```

### Example Scenarios

**High Confidence Contractor (4D Electric):**
- Website Discovery: Found `4delectric.com`
- Website Validation: 2 factors match (business name, phone)
- Website Confidence: 0.5 (2 factors × 0.25 each)
- AI Analysis: High residential focus, comprehensive electrical services
- AI Confidence: 0.9
- Final Confidence: **0.9** (AI confidence used directly)
- Status: `approved_download` ✅

**Medium Confidence Contractor (425 Construction):**
- Website Discovery: Found `425constructionllc.com`
- Website Validation: 1 factor match (business name)
- Website Confidence: 0.25 (1 factor × 0.25)
- AI Analysis: General contractor focus, limited service details
- AI Confidence: 0.6
- Final Confidence: **0.6** (AI confidence used directly)
- Status: `pending_review` ⚠️

**Low Confidence Contractor:**
- Website Discovery: Found `handymantips.org`
- Website Validation: 0 factors match (wrong business)
- Website Confidence: 0.0 (no factors match)
- AI Analysis: **SKIPPED** (website confidence < 0.25)
- Final Confidence: **0.0**
- Status: `rejected` ❌

**No Website Found:**
- Website Discovery: No websites found
- Website Validation: **SKIPPED** (no website)
- Website Confidence: 0.0
- AI Analysis: **SKIPPED** (no website)
- Final Confidence: **0.0**
- Status: `rejected` ❌

---

## Record Status System

Each contractor record has two key status fields that track processing progress:

### Processing Status

| Status | Description | Next Action |
|--------|-------------|-------------|
| **`pending`** | Awaiting processing | System will process automatically |
| **`processing`** | Currently being processed | Wait for completion |
| **`completed`** | Processing finished | Check review_status for outcome |
| **`error`** | Processing failed | Manual intervention required |

### Review Status (for completed records)

| Review Status | Final Confidence | Description | Action Required |
|---------------|------------------|-------------|-----------------|
| **`approved_download`** | ≥ 0.8 | **Auto-approved** ✅ | Ready for export |
| **`pending_review`** | 0.4 - 0.79 | **Manual review needed** ⚠️ | Requires human validation |
| **`rejected`** | < 0.4 | **Auto-rejected** ❌ | Low quality or no website found |

### Status Workflow Examples

**High Confidence Contractor (4D Electric):**
- Website Confidence: 0.5 (2 factors matched)
- AI Confidence: 0.9 (high confidence electrical services)
- Final Confidence: **0.9** (AI confidence used directly)
- Status: `completed` → `approved_download` ✅

**Medium Confidence Contractor (425 Construction):**
- Website Confidence: 0.4 (2 factors matched)
- AI Confidence: 0.6 (medium confidence general contractor)
- Final Confidence: **0.6** (AI confidence used directly)
- Status: `completed` → `pending_review` ⚠️

**Low Confidence Contractor:**
- Website Confidence: 0.4 (2 factors matched)
- AI Confidence: 0.4 (low confidence)
- Final Confidence: **0.4** (AI confidence used directly)
- Status: `completed` → `pending_review` ⚠️

**No Website Found:**
- Website Confidence: 0.0 (no websites passed 0.4 threshold)
- AI Analysis: Skipped
- Final Confidence: **0.0**
- Status: `completed` → `rejected` ❌

---

## Manual Review Process

Contractors with `pending_review` status require manual validation before final approval.

### Review Workflow

1. **Query pending records**: Find contractors with `review_status = 'pending_review'`
2. **Review contractor details**: Examine confidence breakdown, website, and AI analysis
3. **Make decision**:
   - **Approve**: Set `review_status = 'approved'` for export
   - **Reject**: Set `review_status = 'rejected'` to filter out
   - **Modify category**: Update service category and approve

### Review Queries

**Find contractors needing review:**
```sql
SELECT business_name, website_url, confidence_score, mailer_category
FROM contractors 
WHERE processing_status = 'completed' 
  AND review_status = 'pending_review'
ORDER BY confidence_score DESC;
```

**Approve contractor:**
```sql
UPDATE contractors 
SET review_status = 'approved', 
    reviewed_by = 'admin_user',
    reviewed_at = CURRENT_TIMESTAMP
WHERE id = [contractor_id];
```

---

## Data Sources & Coverage

### Input Data
- **Source**: Washington State contractor license database (CSV format)
- **Coverage**: Puget Sound region focus (excludes eastern Washington)
- **Filtering**: Active licenses only (excludes expired, re-licensed, inactive)

### Service Categories

**Complete Taxonomy**: 194 total categories (30 priority + 164 standard) from CRM data

**Priority Categories** (30 High-Value Residential Services):
*See complete list in [Service Categories](#service-categories) section above*

---

## Comprehensive Website Crawling

The system now uses **comprehensive website crawling** to provide much more detailed content analysis for AI classification.

### Enhanced Crawling Features

**Multi-Page Analysis**: 
- Crawls main page + navigation pages (up to 5 additional pages)
- Focuses on content-rich pages with keywords: "service", "offering", "about", "contact", "capabilities", "location"
- Filters out non-content pages (admin, login, cart, etc.)

**Content Quality Improvements**:
- **Before**: 1,400-2,700 characters (single page)
- **After**: 5,000-25,000 characters (multiple pages)
- **AI Content Limit**: 10,000 characters for cost efficiency
- **Quality**: 4-5x more comprehensive content for better AI analysis

### Crawling Process

1. **Main Page Crawl**: Extract raw HTML for navigation analysis
2. **Navigation Extraction**: Find links using comprehensive CSS selectors
3. **Content Filtering**: Prioritize pages with service/about/contact keywords
4. **Multi-Page Crawling**: Crawl up to 5 additional pages with 0.5s delays
5. **Content Combination**: Merge all page content for comprehensive analysis
6. **AI Analysis**: Send up to 10K characters to OpenAI for classification

### Example Results

**425 Construction LLC**:
- **Pages Crawled**: 4 (main + 3 additional)
- **Content**: 5,157 characters (4x more than before)
- **AI Tokens**: 1,289 tokens
- **Cost**: $0.0006 per analysis

**4D Electric LLC**:
- **Pages Crawled**: 6 (main + 5 additional)
- **Content**: 10,000 characters (capped for efficiency)
- **AI Tokens**: 2,500 tokens
- **Cost**: $0.0013 per analysis

---

## Scripts & Tools

The system includes a comprehensive set of scripts for processing, analysis, and debugging.

### Core Processing Scripts

**Main Processing Pipeline**:
```bash
# Run batch processing
docker-compose exec app python scripts/run_processing.py --count 100 --batch-size 10

# Test specific contractor
docker-compose exec app python scripts/test_specific_contractor.py --contractor "425 CONSTRUCTION"
```

### Analysis & Debugging Scripts

**Content Analysis**:
```bash
# Comprehensive content analysis with crawl statistics
docker-compose exec app python scripts/content_analysis.py --contractor "425 CONSTRUCTION"
```

**Navigation Debugging**:
```bash
# Detailed navigation link extraction debugging
docker-compose exec app python scripts/navigation_debug.py --contractor "4D ELECTRIC"
```

### Data Management Scripts

**Import/Export**:
```bash
# Import contractor data
docker-compose exec app python scripts/import_data.py

# Export processed results
docker-compose exec app python scripts/export_contractors.py

# Deduplicate exports
docker-compose exec app python scripts/deduplicate_exports.py
```

**Setup & Maintenance**:
```bash
# Database setup
docker-compose exec app python scripts/setup_database.py

# Docker environment setup
docker-compose exec app python scripts/docker_setup.py
```

### Script Categories

| Category | Scripts | Purpose |
|----------|---------|---------|
| **Processing** | `run_processing.py`, `test_specific_contractor.py` | Main contractor processing pipeline |
| **Analysis** | `content_analysis.py`, `navigation_debug.py` | Content analysis and debugging |
| **Data Management** | `import_data.py`, `export_contractors.py`, `deduplicate_exports.py` | Data import/export operations |
| **Setup** | `setup_database.py`, `docker_setup.py` | System initialization |
| **Enhanced Discovery** | `enhanced_discovery.py`, `re_export_processed.py` | Advanced discovery features |

---

## Service Categories

The system categorizes contractors into 194 different service categories, with 30 priority categories for high-value residential services.

### Priority Categories (30 High-Value Residential Services)

1. **Heating and Cooling** - AC repair, furnace installation, duct cleaning, heat pump service, HVAC maintenance
2. **Plumbing** - Drain cleaning, water heater repair, pipe repair, leak detection, bathroom fixtures
3. **Sprinklers** - Sprinkler installation, irrigation repair, watering system design, sprinkler maintenance
4. **Blinds** - Blind installation, custom window treatments, shade repair, shutter installation
5. **Window/Door** - Window replacement, door installation, glass repair, entry door replacement
6. **Awning/Patio/Carport** - Awning installation, patio covers, carport construction, outdoor shade structures
7. **Bathroom/Kitchen Remodel** - Bathroom renovation, kitchen remodel, countertop installation, cabinet upgrade
8. **Storage & Closets** - Closet organization, storage solutions, custom shelving, pantry systems
9. **Decks & Patios** - Deck construction, patio installation, outdoor living spaces, deck repair
10. **Electrician** - Electrical repairs, panel upgrades, outlet installation, lighting installation
11. **Fence** - Fence installation, gate installation, privacy fencing, fence repair
12. **Fireplace** - Fireplace installation, chimney cleaning, gas fireplace repair, hearth construction
13. **Garage Floors** - Epoxy garage floors, garage floor coating, concrete floor finishing, floor resurfacing
14. **Gutters** - Gutter installation, gutter cleaning, downspout repair, gutter guards
15. **Handyman** - General repairs, home maintenance, fixture installation, odd jobs
16. **Junk Removal** - Junk hauling, debris removal, estate cleanout, construction cleanup
17. **Landscaping** - Landscape design, lawn maintenance, garden installation, yard cleanup
18. **Lighting** - Light fixture installation, outdoor lighting design, LED upgrades, landscape lighting
19. **Tree Service** - Tree removal, tree trimming, stump grinding, tree pruning
20. **Window Cleaning** - Residential window cleaning, pressure washing windows, glass cleaning service
21. **Window/Glass Repair** - Window glass replacement, screen repair, window hardware repair, glass restoration
22. **House Cleaning** - Regular house cleaning, deep cleaning, move-in cleaning, post-construction cleanup
23. **Garage Doors** - Garage door installation, opener repair, garage door maintenance, door replacement
24. **Solar** - Solar panel installation, solar system design, solar maintenance, energy storage
25. **Duct Cleaning** - Air duct cleaning, HVAC system cleaning, dryer vent cleaning, ventilation maintenance
26. **Carpet Cleaning** - Professional carpet cleaning, upholstery cleaning, stain removal, steam cleaning
27. **Closets** - Custom closet systems, closet organization, walk-in closets, storage design
28. **Concrete** - Concrete driveways, patio construction, sidewalk installation, foundation work
29. **Foundations** - Foundation repair, basement waterproofing, crawl space encapsulation, structural work
30. **Exterior Cleaning** - House pressure washing, driveway cleaning, deck cleaning, exterior surface cleaning

**Standard Categories** (164 Additional Services - Complete Taxonomy):
Includes comprehensive coverage of all business types from your CRM:
- **Home Improvement**: Flooring, Roofing, Painting, Siding, Skylights, Doors, Cabinets, Countertops, ADU Contractors, etc.
- **Home Services**: Appliance Repair, Pest Control, Pressure Washing, Mold Remediation, Septic, BBQ Cleaning, etc.
- **Professional Services**: Legal, Financial Planning, Real Estate, Insurance, Marketing, Consulting, Accounting, etc.
- **Personal Services**: Healthcare, Dental, Fitness, Beauty, Education, Photography, Massage, Life Coaching, etc.
- **Retail & Commerce**: Auto Sales, Furniture, Appliances, Sporting Goods, Clothing, Mattress, Jewelry, etc.
- **Experience & Travel**: Dining, Entertainment, Hotels, Travel Planning, Recreation, Golf, Events, etc.

**System Processing Focus**: 
- **Primary targeting**: 30 priority categories (highest ROI residential services)
- **Complete classification**: All 194 categories for comprehensive contractor taxonomy
- **AI categorization**: Uses full database for accurate business type identification

### Geographic Coverage
- **Included Areas**: Seattle, Tacoma, Bellevue, Everett, Kent, Renton, Federal Way, Kirkland, Olympia, and surrounding Puget Sound cities
- **Area Codes**: 206, 253, 360, 425
- **Excluded Areas**: Eastern Washington (Spokane, Yakima, Walla Walla, etc.)

## Quick Start

### Check Google API Quota Status

Before processing, always check your current quota usage:

```bash
docker-compose exec app python scripts/check_quota_status.py
```

This will show:
- Actual queries used today (from logs)
- Remaining daily quota
- Processing capacity recommendations
- Suggested batch sizes

### Prerequisites
- PostgreSQL 15+ database
- Python 3.11+ with required packages
- Google Custom Search API key
- OpenAI API key (GPT-4o-mini access)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and database credentials
   ```

3. **Initialize database:**
   ```bash
   python scripts/setup_database.py
   ```

4. **Import contractor data:**
   ```bash
   python scripts/import_data.py --file data/contractors.csv
   ```

5. **Start processing:**
   ```bash
   python scripts/run_processing.py
   ```

6. **Export ready contractors:**
   ```bash
   python scripts/export_contractors.py --exported-by "your_name"
   ```

### Monitor Progress

**Check processing status:**
```sql
SELECT processing_status, COUNT(*) 
FROM contractors 
GROUP BY processing_status;
```

**View high-confidence results:**
```sql
SELECT business_name, website_url, confidence_score, mailer_category
FROM contractors 
WHERE review_status = 'approved_download'
ORDER BY confidence_score DESC;
```

### Monitor API Quota

**Check current quota usage:**
```bash
docker-compose exec app python scripts/check_quota_status.py
```

**View quota usage in logs:**
```bash
docker-compose exec app grep "Google API Query:" logs/processing.log | wc -l
```

**Check today's usage:**
```bash
docker-compose exec app grep "$(date +%Y-%m-%d).*Google API Query:" logs/processing.log | wc -l
```

---

## Recent System Improvements

### Enhanced Website Discovery
- **Business Name Variations**: Automatically generates multiple search queries by removing common business designations (LLC, INC, CORP) while preserving important descriptive words like "CONSTRUCTION", "ELECTRIC", "REMODELING"
- **Consolidated Logging**: Google search results are logged in single, comprehensive entries showing query, status, response keys, and result summary
- **Comprehensive Domain Filtering**: Excludes government sites (`.gov`, `.org`, `.codes`), directory sites, and social media platforms

### Improved Validation System
- **5-Factor Validation**: Business name, license number, phone number, principal name, and address matching
- **Geographic Validation**: Applied during discovery phase, not as a penalty in confidence calculation
- **Enhanced Phone Matching**: Full string normalization and case-insensitive matching

### Architecture Simplification
- **Unified Service**: Consolidated `ContractorService` (formerly `EnhancedContractorService`)
- **Removed Redundancy**: Eliminated separate `website_discovery_service.py` file
- **Streamlined Processing**: Integrated discovery, validation, and AI analysis in single service

## Technical Implementation

For detailed technical information including:
- Database schema and SQL queries
- Website discovery algorithms  
- AI analysis prompts and integration
- Performance optimization settings
- Error handling and monitoring
- Deployment configurations

**See: [TECHNICAL_SPECIFICATION.md](TECHNICAL_SPECIFICATION.md)**

---

## Export Tracking System

The system tracks all exports to prevent duplicate downloads and maintain audit trails. 

**Exported Statuses**: Both `approved_download` (auto-approved) and `pending_review` (manual review needed) contractors are exported together.

### Export Commands

```bash
# Export all ready contractors - both approved_download AND pending_review statuses
python scripts/export_contractors.py --exported-by "user_name"

# Export only previously unexported contractors (approved_download + pending_review)
python scripts/export_contractors.py --unexported-only --exported-by "user_name"

# Track an existing CSV file retroactively
python scripts/export_contractors.py --track-existing exports/file.csv --exported-by "user_name"

# Show export summary and statistics
python scripts/export_contractors.py --summary
```

### Export Database Fields

Each exported contractor gets marked with:
- `exported_at` - Timestamp of export
- `export_batch_id` - Links to export_batches table
- `marked_for_download` - Boolean flag (TRUE)
- `marked_for_download_at` - When marked for download

### Export Batches Table

Tracks each export operation:
- `batch_id` - Unique identifier
- `export_date` - When export occurred
- `exported_by` - Who performed the export
- `contractor_count` - Number of contractors in batch
- `file_path` - Path to generated CSV file

---

## 🚨 Troubleshooting

### Common Issues
1. **429 Rate Limit Errors**: Daily quota exceeded, wait until tomorrow
2. **API Key Issues**: Check Google API and OpenAI configuration
3. **Database Connection**: Verify PostgreSQL is running
4. **Processing Errors**: Check logs with `check_logs.py`

### Quota Management
The system automatically detects when the daily Google API quota (10,000 queries) is exceeded and gracefully stops processing.

**Quota Detection Strategy:**
- **Consecutive 429 errors**: 3+ consecutive 429 errors trigger quota exceeded detection
- **Automatic shutdown**: Processing stops immediately when quota exceeded
- **Daily reset**: Quota resets at midnight each day
- **Progress preservation**: Partially processed batches are saved

**Check Quota Status:**
```bash
# Check current quota usage and recommendations
docker-compose exec app python scripts/check_quota_status.py
```

**Quota Management Commands:**
```bash
# Check if quota exceeded before processing
docker-compose exec app python scripts/check_quota_status.py

# Process with quota monitoring (automatically stops if exceeded)
docker-compose exec app python scripts/run_parallel_test.py

# Check processing status after quota exceeded
docker-compose exec app python scripts/check_results.py
```

### Monitoring
```bash
# Check for errors
docker-compose exec app python scripts/check_logs.py

# Test API status
docker-compose exec app python scripts/test_google_api.py

# View recent processing
docker-compose exec app python scripts/show_processed_puget_sound.py
```

### Daily Processing (Recommended)
```bash
# Process 5000 ACTIVE Puget Sound contractors (daily batch)
docker-compose exec app python scripts/run_parallel_test.py

# Process with custom limits
docker-compose exec app python scripts/run_parallel_test.py --limit 1000 --processes 2

# Test with small batch
docker-compose exec app python scripts/run_parallel_test.py --limit 100 --processes 1
```

*This system helps identify legitimate residential contractors in the Puget Sound region through intelligent website validation and AI-powered categorization, ensuring high-quality lead generation for home service marketing.*
