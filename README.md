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
- Business owner names found in "About Us" or contact sections
- Matches against primary_principal_name field from contractor data

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
- Status = "rejected" (auto-rejected due to no validated website)

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
| **`rejected`** | < 0.6 | **Auto-rejected** ❌ | Low quality or no website found |

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

*This system helps identify legitimate residential contractors in the Puget Sound region through intelligent website validation and AI-powered categorization, ensuring high-quality lead generation for home service marketing.*
