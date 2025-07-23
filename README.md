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
🔍 Website Discovery (Google Search)
    ↓
🛡️ Website Validation (5-Factor Confidence Scoring)
    ↓
🤖 AI Analysis (GPT-4o-mini categorization)
    ↓
📊 Combined Confidence Calculation
    ↓
🎯 Status Assignment (Auto-approve/Manual Review/Reject)
```

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

The system uses a comprehensive **5-factor validation framework** to ensure discovered websites actually belong to the correct contractor. This prevents false matches like pottery websites being matched to painting contractors.

### 5-Factor Validation (0.25 points each, 1.0 maximum)

**Factor 1: Business Name Match (0.25 points)**
- Exact business name found on website = 1.0 score
- Partial matches: 80%+ words = 1.0, 60%+ = 0.6, 40%+ = 0.3
- Removes common suffixes (LLC, INC, CORP) for better matching

**Factor 2: License Number Match (0.25 points)**
- Contractor license number found anywhere on website = 1.0 score
- Strongest validation factor when present
- Handles various formats (with/without asterisks)

**Factor 3: Phone Number Match (0.25 points)**
- Exact 10-digit phone number match = 1.0 score
- Supports multiple formats: (206) 555-1234, 206-555-1234, 206.555.1234
- No partial credit - either matches completely or gets 0.0

**Factor 4: Principal Name Match (0.25 points)**
- Business owner names (rarely available on contractor websites)
- Currently 0.0 - reserved for future enhancement

**Factor 5: Address Match (0.25 points)**
- Exact street number match = 1.0 score
- Partial credit for street name components
- Most effective for contractors with physical storefronts

### Geographic Validation Penalty (-0.20 points)

**CRITICAL ANTI-FRAUD PROTECTION**: Prevents accepting contractors from outside the Puget Sound service area.

**Penalty Applied When:**
- No Puget Sound area codes found (206, 253, 360, 425) **AND**
- No local address references found (Seattle, Tacoma, Bellevue, etc.)

**Multi-Area Service Logic:**
- "Serving Seattle, Tacoma, and Spokane" = ✅ **NO PENALTY** (includes local areas)
- "Serving Spokane and Yakima only" = ❌ **-0.20 PENALTY** (no local presence)

### Website Validation Threshold

**Minimum 0.4 confidence required** (at least 2 factors must match) for website acceptance:
- **≥ 0.4**: Website accepted, proceed to AI analysis
- **< 0.4**: Website rejected, continue searching other results

---

## Combined Confidence Scoring

The system calculates a final confidence score that determines the contractor's processing status.

### Confidence Calculation

**When Website Found & Validated (≥ 0.4 website confidence):**
```
Final Confidence = (Website Confidence × 60%) + (AI Confidence × 40%)
```

**When No Website Found (< 0.4 website confidence):**
- **AI Analysis Skipped** - No further processing
- Final Confidence = 0.0
- Status = "No Website"

### AI Confidence Component

- **Source**: OpenAI GPT-4o-mini analysis of website content
- **Analyzes**: Residential vs commercial focus, service categories, business legitimacy
- **Returns**: 0.0-1.0 confidence score for its categorization
- **Weight**: 40% of final confidence score

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
| **`pending_review`** | 0.6 - 0.79 | **Manual review needed** ⚠️ | Requires human validation |
| **`rejected`** | < 0.6 | **Auto-rejected** ❌ | Low quality, filtered out |
| **`No Website`** | 0.0 | **No validated website** 📋 | Could not verify business |

### Status Workflow Examples

**High Confidence Contractor (Best Plumbing):**
- Website Confidence: 1.0 (4 factors matched)
- AI Confidence: 0.9 (high confidence residential plumbing)
- Final Confidence: (1.0 × 0.6) + (0.9 × 0.4) = **0.96**
- Status: `completed` → `approved_download` ✅

**Medium Confidence Contractor:**
- Website Confidence: 0.6 (2-3 factors matched)
- AI Confidence: 0.7 (medium confidence)  
- Final Confidence: (0.6 × 0.6) + (0.7 × 0.4) = **0.64**
- Status: `completed` → `pending_review` ⚠️

**Low Confidence Contractor:**
- Website Confidence: 0.5 (2 factors matched)
- AI Confidence: 0.4 (low confidence)
- Final Confidence: (0.5 × 0.6) + (0.4 × 0.4) = **0.46**
- Status: `completed` → `rejected` ❌

**No Website Found:**
- Website Confidence: 0.0 (no websites passed 0.4 threshold)
- AI Analysis: Skipped
- Final Confidence: **0.0**
- Status: `completed` → `No Website` 📋

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
- **Plumbing** (faucets, pipes, water heaters)
- **HVAC** (heating, cooling, ventilation)
- **Electrical** (wiring, panels, lighting)
- **Roofing** (installation, repair, gutters)
- **Handyman** (general repairs, maintenance)
- **Flooring** (hardwood, carpet, tile)
- **Painting** (interior, exterior, residential)
- **Landscaping** (lawn care, gardening, outdoor)
- **Windows & Doors** (residential installation)
- **Auto Glass** (windshield repair, mobile service)
- **Concrete** (driveways, patios, foundations)
- **Fencing** (residential, commercial, repair)
- **Kitchen & Bath** (remodeling, fixtures)

### Geographic Coverage
- **Included Areas**: Seattle, Tacoma, Bellevue, Everett, Kent, Renton, Federal Way, Kirkland, Olympia, and surrounding Puget Sound cities
- **Area Codes**: 206, 253, 360, 425
- **Excluded Areas**: Eastern Washington (Spokane, Yakima, Walla Walla, etc.)

## Quick Start

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

---

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

*This system helps identify legitimate residential contractors in the Puget Sound region through intelligent website validation and AI-powered categorization, ensuring high-quality lead generation for home service marketing.*
