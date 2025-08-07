"""
Configuration management for contractor enrichment system
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()


class Config:
    """Main configuration class"""
    
    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'contractor_enrichment')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_MIN_CONNECTIONS: int = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
    DB_MAX_CONNECTIONS: int = int(os.getenv('DB_MAX_CONNECTIONS', '20'))
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    GPT4_MINI_MODEL: str = os.getenv('GPT4_MINI_MODEL', 'gpt-4o-mini')
    GPT4_MODEL: str = os.getenv('GPT4_MODEL', 'gpt-4o')
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '4096'))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.2'))
    OPENAI_TIMEOUT: int = int(os.getenv('OPENAI_TIMEOUT', '60'))
    
    # Processing Configuration
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '10'))
    MAX_CONCURRENT_CRAWLS: int = int(os.getenv('MAX_CONCURRENT_CRAWLS', '5'))
    CRAWL_TIMEOUT: int = int(os.getenv('CRAWL_TIMEOUT', '30'))
    RETRY_ATTEMPTS: int = int(os.getenv('RETRY_ATTEMPTS', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
    
    # Confidence Thresholds
    AUTO_APPROVE_THRESHOLD: float = float(os.getenv('AUTO_APPROVE_THRESHOLD', '0.8'))
    MANUAL_REVIEW_THRESHOLD: float = float(os.getenv('MANUAL_REVIEW_THRESHOLD', '0.6'))
    
    # Rate Limiting (seconds between requests)
    SEARCH_DELAY: float = float(os.getenv('SEARCH_DELAY', '3.0'))  # Increased from 1.0 to 3.0 for parallel processing
    LLM_DELAY: float = float(os.getenv('LLM_DELAY', '0.5'))
    
    # Search API Keys (optional)
    GOOGLE_API_KEY: Optional[str] = os.getenv('GOOGLE_SEARCH_API_KEY') or os.getenv('GOOGLE_API_KEY')
    GOOGLE_CSE_ID: Optional[str] = os.getenv('GOOGLE_SEARCH_ENGINE_ID') or os.getenv('GOOGLE_CSE_ID')
    
    # Application Settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    EXPORT_DIR: str = os.getenv('EXPORT_DIR', './exports')
    
    @property
    def database_url(self) -> str:
        """Get the complete database connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate(self) -> bool:
        """Validate required configuration values"""
        required_fields = [
            ('OPENAI_API_KEY', self.OPENAI_API_KEY),
        ]
        
        # Only require DB_PASSWORD if not using localhost with nodakjones user
        if self.DB_HOST != 'localhost' or self.DB_USER != 'nodakjones':
            required_fields.append(('DB_PASSWORD', self.DB_PASSWORD))
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        return True


# Global config instance
config = Config()


# Puget Sound Zip Codes
PUGET_SOUND_ZIP_CODES = {
    98001, 98002, 98003, 98004, 98005, 98006, 98007, 98008, 98010, 98011, 98014, 98019, 98022, 98023, 98024, 98027, 98028, 98029, 98030, 98031, 98032, 98033, 98034, 98038, 98039, 98040, 98042, 98045, 98047, 98052, 98053, 98055, 98056, 98057, 98058, 98059, 98070, 98072, 98074, 98075, 98077, 98092, 98101, 98102, 98103, 98104, 98105, 98106, 98107, 98108, 98109, 98110, 98111, 98112, 98115, 98116, 98117, 98118, 98119, 98121, 98122, 98125, 98126, 98133, 98134, 98136, 98144, 98146, 98148, 98154, 98155, 98158, 98164, 98166, 98168, 98174, 98177, 98178, 98188, 98195, 98198, 98199,
    98303, 98304, 98321, 98323, 98327, 98328, 98329, 98330, 98332, 98333, 98335, 98338, 98344, 98349, 98351, 98352, 98354, 98360, 98371, 98372, 98373, 98374, 98375, 98385, 98387, 98388, 98402, 98403, 98404, 98405, 98406, 98407, 98408, 98409, 98418, 98421, 98422, 98424, 98433, 98439, 98443, 98444, 98445, 98446, 98447, 98465, 98466, 98467, 98498, 98499,
    98012, 98020, 98021, 98026, 98036, 98037, 98043, 98087, 98201, 98203, 98204, 98205, 98208, 98223, 98241, 98251, 98252, 98256, 98258, 98259, 98270, 98271, 98272, 98282, 98287, 98290, 98291, 98292, 98293, 98294, 98296,
    98110, 98310, 98311, 98312, 98314, 98315, 98337, 98340, 98342, 98346, 98353, 98359, 98364, 98366, 98367, 98370, 98378, 98380, 98383, 98384, 98386, 98392, 98393,
    98501, 98502, 98503, 98505, 98506, 98512, 98513, 98516, 98530, 98540, 98576, 98579, 98589, 98597,
    98220, 98221, 98222, 98232, 98233, 98235, 98237, 98238, 98240, 98255, 98257, 98263, 98267, 98273, 98274, 98283, 98284,
    98225, 98226, 98229, 98230, 98231, 98240, 98244, 98247, 98248, 98262, 98264, 98266,
    98239, 98249, 98253, 98260, 98277, 98278,
    98524, 98528, 98546, 98548, 98555, 98584, 98588, 98592,
    98243, 98245, 98250, 98261, 98279, 98286
}


# Query Generation Templates (in priority order)
QUERY_TEMPLATES = [
    '"{business_name}" {city} {state} contractor',  # Primary query
    '"{business_name}" {city} {state}',             # Secondary without "contractor"
    '"{business_name}" {phone}',                    # Phone-based search
    '"{business_name}" contractor {state}'          # State-level fallback
]

# Result Filtering Rules
EXCLUDED_DOMAINS = {
    'facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com',
    'yelp.com', 'yellowpages.com', 'whitepages.com', 'bbb.org',
    'angi.com', 'homeadvisor.com', 'thumbtack.com', 'google.com',
    'bing.com', 'yahoo.com', 'directories.com', 'mapquest.com',
    'taskrabbit.com', 'birdeye.com', 'rcrwa.com', 'redfin.com', 'zillow.com',
    'data.wa.gov', 'data.gov', 'census.gov', 'irs.gov', 'usps.com',
    'uscis.gov', 'ssa.gov', 'medicare.gov', 'va.gov', 'fbi.gov',
    'whitehouse.gov', 'congress.gov', 'supremecourt.gov', 'federalreserve.gov',
    'buildzoom.com', 'houzz.com', 'porch.com', 'thumbtack.com', 'angi.com',
    'homeadvisor.com', 'nextdoor.com', 'neighborhoodscout.com', 'manta.com',
    'superpages.com', 'whitepages.com', 'yellowpages.com', 'citysearch.com',
    'opengovwa.com', 'bestplumbers.com', 'procore.com', 'reddit.com', 'issuu.com',
    # News outlets and media sites
    'spokanejournal.com', 'seattletimes.com', 'seattlepi.com', 'king5.com',
    'komonews.com', 'q13fox.com', 'kiro7.com', 'myballard.com', 'westseattleblog.com',
    'capitolhillseattle.com', 'centraldistrictnews.com', 'eastlakeavenue.com',
    'fremontuniverse.com', 'greenlakeseattle.com', 'magnoliavoice.com',
    'phinneywood.com', 'queenanneview.com', 'southlakeunion.com', 'wallingfordseattle.com',
    # Government data and API endpoints
    'hub.arcgis.com', 'arcgis.com', 'data.wa.gov', 'data.gov', 'census.gov',
    'geodata.gov', 'geoplatform.gov', 'nationalmap.gov', 'usgs.gov',
    # Additional problematic domains from test results
    '19thnews.org', 'investmentsandwealth.org', 'aandacarpets-bedford.co.uk',
    'aaconstruct.com.au', 'aa-construction-llc.com', 'aeagc.com',
    'aandacarpets-bedford.co.uk', 'aahomebuilders.com', 'aainc.co.jp',
    'aapropertyuk.com', 'abconcretepumping.com', 'abfabricators.com',
    'abflooringllc.com', 'abhomeimprovementsni.co.uk', 'ab-lawncare.net',
    'aandbsheetmetal.com', 'abtransportation.com', 'abtreeconroe.com',
    'acllc.com', 'aandcconcrete.com', 'ac1construction.co.uk',
    'a-celectric.com', 'aandcglass.com', 'ac-heatingandcooling.com.au',
    'acmechanical.ca', 'abelectricalonline.co.uk', 'drillerdb.com',
    'wausaudailyherald.com', 'fayranches.com', 'gutter-cleaning-services.cmac.ws',
    # New excluded domains
    'bizapedia.com', 'kitsapbuilds.com', 'procore.com', 'bizprofile.net', 
    'ibew48.com', 'rocketreach.co', 'thebluebook.com', 'washingtonbids.com', 
    'gigharborchamber.net'
}

# Domain patterns to exclude (wildcards)
EXCLUDED_DOMAIN_PATTERNS = {
    '*.gov',  # Government websites
    '*.org',  # Non-profit organizations
    '*.codes',  # Code hosting sites
    '*.co.uk',  # UK businesses
}

def is_valid_website_domain(url: str) -> bool:
    """Check if URL is a valid business website (not directory/social)"""
    if not url:
        return False
    
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()
    
    # Check for excluded domains (exact match or subdomain)
    for excluded in EXCLUDED_DOMAINS:
        if domain == excluded or domain.endswith('.' + excluded):
            return False
    
    # Check for excluded domain patterns
    if domain.endswith('.codes') or domain.endswith('.org') or domain.endswith('.gov'):
        return False
    
    # Check for member, chamber, or directory in domain name
    if 'member' in domain or 'chamber' in domain or 'directory' in domain:
        return False
    
    # Check for news article patterns in URL path
    news_patterns = [
        '/articles/', '/news/', '/story/', '/article/', '/business-licenses',
        '/business-directory/', '/company-profiles', '/business-profiles',
        '/property-details/', '/real-estate/', '/homes/', '/apartments/',
        '/api/download/', '/api/items/', '/csv?', '/data/', '/datasets/',
        '/business-licenses-may-9', '/business-licenses-june-', '/business-licenses-july-',
        '/business-licenses-august-', '/business-licenses-september-', '/business-licenses-october-',
        '/business-licenses-november-', '/business-licenses-december-'
    ]
    
    for pattern in news_patterns:
        if pattern in path:
            return False
    
    # Check for government data API patterns
    gov_data_patterns = [
        '/api/download/', '/api/items/', '/csv?', '/data/', '/datasets/',
        'redirect=true', 'layers=', 'where=1=1', 'items/', 'download/v1/'
    ]
    
    for pattern in gov_data_patterns:
        if pattern in url.lower():
            return False
    
    return True

# Puget Sound Area Cities and Area Codes for Local Business Validation
PUGET_SOUND_CITIES = {
    'seattle', 'bellevue', 'redmond', 'kirkland', 'sammamish', 'issaquah', 'snoqualmie',
    'north bend', 'fall city', 'carnation', 'duvall', 'monroe', 'snohomish',
    'arlington', 'stanwood', 'camano island', 'oak harbor', 'coupeville', 'langley',
    'freeland', 'clinton', 'mukilteo', 'edmonds', 'lynnwood', 'mill creek',
    'brier', 'mountlake terrace', 'shoreline', 'lake forest park', 'kenmore',
    'bothell', 'woodinville', 'tacoma', 'lakewood', 'federal way', 'auburn',
    'renton', 'kent', 'mercer island', 'newcastle', 'sammamish', 'issaquah',
    'snoqualmie', 'north bend', 'fall city', 'carnation', 'duvall', 'monroe',
    'snohomish', 'arlington', 'stanwood', 'camano island', 'oak harbor', 'coupeville',
    'langley', 'freeland', 'clinton', 'mukilteo', 'edmonds', 'lynnwood', 'mill creek',
    'brier', 'mountlake terrace', 'shoreline', 'lake forest park', 'kenmore',
    'bothell', 'woodinville', 'tacoma', 'lakewood', 'federal way', 'auburn',
    'renton', 'kent', 'mercer island', 'newcastle', 'sammamish', 'issaquah',
    'snoqualmie', 'north bend', 'fall city', 'carnation', 'duvall', 'monroe',
    'snohomish', 'arlington', 'stanwood', 'camano island', 'oak harbor', 'coupeville',
    'langley', 'freeland', 'clinton', 'mukilteo', 'edmonds', 'lynnwood', 'mill creek',
    'brier', 'mountlake terrace', 'shoreline', 'lake forest park', 'kenmore'
}

PUGET_SOUND_AREA_CODES = {
    '206',  # Seattle
    '253',  # Tacoma
    '360',  # Vancouver, Bellingham
    '425',  # Bellevue, Redmond
    '564'   # New Washington area code
}

def is_local_business_validation(contractor_city: str, contractor_state: str, contractor_phone: str, website_content: str) -> Dict[str, Any]:
    """Comprehensive local business validation using city lists and area codes"""
    validation_result = {
        'is_local': False,
        'city_match': False,
        'area_code_match': False,
        'local_keywords': 0,
        'details': {}
    }
    
    if not contractor_city or not contractor_state:
        return validation_result
    
    # 1. City Validation
    contractor_city_lower = contractor_city.lower().strip()
    validation_result['city_match'] = contractor_city_lower in PUGET_SOUND_CITIES
    validation_result['details']['city'] = contractor_city_lower
    validation_result['details']['city_found'] = validation_result['city_match']
    
    # 2. Area Code Validation
    if contractor_phone:
        # Extract area code from phone number
        phone_digits = re.sub(r'[^\d]', '', contractor_phone)
        if len(phone_digits) >= 10:
            area_code = phone_digits[:3]
            validation_result['area_code_match'] = area_code in PUGET_SOUND_AREA_CODES
            validation_result['details']['area_code'] = area_code
            validation_result['details']['area_code_found'] = validation_result['area_code_match']
    
    # 3. Local Keywords in Website Content
    if website_content:
        local_keywords = [
            'local', 'locally owned', 'family owned', 'community', 'neighborhood',
            'serving', 'service area', 'coverage area', 'licensed in', 'licensed for',
            'washington', 'wa', 'seattle', 'spokane', 'tacoma', 'vancouver', 'bellevue'
        ]
        content_lower = website_content.lower()
        validation_result['local_keywords'] = sum(1 for keyword in local_keywords if keyword in content_lower)
    
    # 4. Determine if local business
    validation_result['is_local'] = (
        validation_result['city_match'] and 
        validation_result['area_code_match'] and 
        validation_result['local_keywords'] >= 1
    )
    
    return validation_result

# Resource Management for Virtual Server
PERFORMANCE_CONFIG = {
    'MAX_CONCURRENT_SEARCHES': 3,      # Limit simultaneous searches
    'MAX_CONCURRENT_CRAWLS': 2,        # Limit simultaneous crawls  
    'MAX_CONCURRENT_LLM_CALLS': 2,     # Limit simultaneous LLM API calls
    'BATCH_SIZE': 25,                  # Process 25 contractors per batch
    'MEMORY_LIMIT_MB': 1024,           # Monitor memory usage
    'DB_CONNECTION_POOL': 5,           # Smaller connection pool
    
    # Rate Limiting (to prevent server overload)
    'SEARCH_DELAY': 1.2,              # 1.2 seconds between searches
    'CRAWL_DELAY': 2.0,               # 2 seconds between crawls
    'LLM_DELAY': 1.0,                 # 1 second between LLM calls
    'BATCH_PROCESSING_DELAY': 5.0,    # 5 seconds between batches
    
    # Error Recovery
    'MAX_RETRIES': 2,                 # Reduce retries to save resources
    'EXPONENTIAL_BACKOFF': True,      # Increase delays on errors
    'CIRCUIT_BREAKER_THRESHOLD': 5,   # Stop processing after 5 consecutive errors
}