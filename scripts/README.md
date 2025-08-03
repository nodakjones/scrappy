# Scripts Documentation

This directory contains all the scripts for the Contractor Data Enrichment System, organized by functionality.

## 📁 Script Categories

### 🔄 Core Processing Scripts

#### `run_processing.py`
**Purpose**: Main contractor processing pipeline
**Usage**: 
```bash
docker-compose exec app python scripts/run_processing.py --count 100 --batch-size 10
```
**Features**:
- Batch processing of contractors
- Configurable batch sizes
- Progress tracking and logging
- Error handling and retry logic

#### `test_specific_contractor.py`
**Purpose**: Test processing of individual contractors
**Usage**:
```bash
docker-compose exec app python scripts/test_specific_contractor.py --contractor "425 CONSTRUCTION"
```
**Features**:
- Detailed processing output
- AI analysis results
- Confidence breakdown
- Content preview

#### `test_contractor_batch.py`
**Purpose**: Test batch processing of contractors with formatted results
**Usage**:
```bash
docker-compose exec app python scripts/test_contractor_batch.py
```
**Features**:
- Processes 10 pending contractors
- Displays results in formatted table
- Shows business name, website, category, confidence, and city
- Includes summary statistics and category distribution

### 📊 Analysis & Debugging Scripts

#### `content_analysis.py`
**Purpose**: Comprehensive content analysis with crawl statistics
**Usage**:
```bash
docker-compose exec app python scripts/content_analysis.py --contractor "425 CONSTRUCTION"
```
**Output**:
- Pages crawled and navigation links found
- Content length breakdown
- AI analysis content preview
- Cost estimation

#### `navigation_debug.py`
**Purpose**: Detailed navigation link extraction debugging
**Usage**:
```bash
docker-compose exec app python scripts/navigation_debug.py --contractor "4D ELECTRIC"
```
**Output**:
- HTML content analysis
- CSS selector testing
- Navigation link extraction results
- Detailed debugging information

### 📥📤 Data Management Scripts

#### `import_data.py`
**Purpose**: Import contractor data from CSV
**Usage**:
```bash
docker-compose exec app python scripts/import_data.py
```
**Features**:
- CSV data import
- Data validation
- Duplicate handling
- Progress tracking

#### `export_contractors.py`
**Purpose**: Export processed contractor results
**Usage**:
```bash
docker-compose exec app python scripts/export_contractors.py
```
**Features**:
- Multiple export formats
- Filtering options
- Timestamped files
- Summary statistics

#### `deduplicate_exports.py`
**Purpose**: Remove duplicate contractor records
**Usage**:
```bash
docker-compose exec app python scripts/deduplicate_exports.py
```
**Features**:
- Smart address matching
- Confidence-based deduplication
- Export file generation
- Duplicate analysis

#### `deduplicate_exports_smart_address.py`
**Purpose**: Advanced deduplication with smart address matching
**Usage**:
```bash
docker-compose exec app python scripts/deduplicate_exports_smart_address.py
```
**Features**:
- Address normalization
- Fuzzy matching
- Confidence scoring
- Detailed reporting

### 🛠️ Setup & Maintenance Scripts

#### `setup_database.py`
**Purpose**: Initialize database schema and data
**Usage**:
```bash
docker-compose exec app python scripts/setup_database.py
```
**Features**:
- Schema creation
- Index optimization
- Category data import
- Database validation

#### `docker_setup.py`
**Purpose**: Docker environment setup and configuration
**Usage**:
```bash
docker-compose exec app python scripts/docker_setup.py
```
**Features**:
- Environment validation
- Service health checks
- Configuration testing
- Setup verification

### 🔍 Enhanced Discovery Scripts

#### `enhanced_discovery.py`
**Purpose**: Advanced website discovery features
**Usage**:
```bash
docker-compose exec app python scripts/enhanced_discovery.py
```
**Features**:
- Multi-source discovery
- Geographic filtering
- Quality scoring
- Discovery optimization

#### `re_export_processed.py`
**Purpose**: Re-export processed contractor data
**Usage**:
```bash
docker-compose exec app python scripts/re_export_processed.py
```
**Features**:
- Selective re-export
- Status filtering
- Format options
- Batch processing

## 🚀 Quick Start Examples

### Basic Processing
```bash
# Process 100 contractors
docker-compose exec app python scripts/run_processing.py --count 100

# Test a specific contractor
docker-compose exec app python scripts/test_specific_contractor.py --contractor "ABC PLUMBING"
```

### Analysis & Debugging
```bash
# Analyze content for a contractor
docker-compose exec app python scripts/content_analysis.py --contractor "425 CONSTRUCTION"

# Debug navigation extraction
docker-compose exec app python scripts/navigation_debug.py --contractor "4D ELECTRIC"
```

### Data Management
```bash
# Import new contractor data
docker-compose exec app python scripts/import_data.py

# Export processed results
docker-compose exec app python scripts/export_contractors.py

# Remove duplicates
docker-compose exec app python scripts/deduplicate_exports.py
```

## 📈 Performance Monitoring

### Content Analysis Metrics
- **Pages Crawled**: Number of pages successfully crawled
- **Navigation Links**: Number of navigation links found
- **Content Length**: Total characters extracted
- **AI Tokens**: Estimated OpenAI tokens used
- **Cost**: Estimated processing cost per contractor

### Processing Statistics
- **Batch Size**: Number of contractors processed per batch
- **Success Rate**: Percentage of successful processing
- **Error Rate**: Percentage of failed processing
- **Average Confidence**: Mean confidence score across batch

## 🔧 Troubleshooting

### Common Issues

**Navigation Links Not Found**:
```bash
# Debug navigation extraction
docker-compose exec app python scripts/navigation_debug.py --contractor "CONTRACTOR_NAME"
```

**Low Content Quality**:
```bash
# Analyze content extraction
docker-compose exec app python scripts/content_analysis.py --contractor "CONTRACTOR_NAME"
```

**Processing Errors**:
```bash
# Test individual contractor
docker-compose exec app python scripts/test_specific_contractor.py --contractor "CONTRACTOR_NAME"
```

### Debugging Tips

1. **Use Content Analysis**: Check if websites are being crawled properly
2. **Navigation Debug**: Verify navigation link extraction is working
3. **Individual Testing**: Test specific contractors to isolate issues
4. **Log Analysis**: Check processing logs for detailed error information

## 📋 Script Dependencies

### Required Packages
- `aiohttp`: Async HTTP client for website crawling
- `beautifulsoup4`: HTML parsing for navigation extraction
- `openai`: AI analysis integration
- `asyncpg`: PostgreSQL async driver
- `pandas`: Data manipulation and CSV handling

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI analysis
- `GOOGLE_SEARCH_API_KEY`: Google Custom Search API key
- `GOOGLE_SEARCH_ENGINE_ID`: Google Custom Search Engine ID

## 🎯 Best Practices

### Processing
- Use appropriate batch sizes (10-50 contractors)
- Monitor processing logs for errors
- Check confidence scores for quality assessment

### Analysis
- Use content analysis for quality verification
- Debug navigation issues with navigation debug script
- Test individual contractors for troubleshooting

### Data Management
- Regularly export and backup processed data
- Use deduplication scripts to maintain data quality
- Monitor export file sizes and processing times 