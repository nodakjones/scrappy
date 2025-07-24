"""
Configuration management for contractor enrichment system
"""
import os
from typing import Optional
from dotenv import load_dotenv

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
    SEARCH_DELAY: float = float(os.getenv('SEARCH_DELAY', '1.0'))
    LLM_DELAY: float = float(os.getenv('LLM_DELAY', '0.5'))
    
    # Search API Keys (optional)
    SERPAPI_KEY: Optional[str] = os.getenv('SERPAPI_KEY')
    BING_SEARCH_API_KEY: Optional[str] = os.getenv('BING_SEARCH_API_KEY')
    
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
            ('DB_PASSWORD', self.DB_PASSWORD),
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        return True


# Global config instance
config = Config()


# SerpAPI Configuration
SERPAPI_CONFIG = {
    'results_per_search': 10,  # Get top 10 results per query
    'max_queries_per_contractor': 4,  # Limit queries to prevent API overuse
    'timeout': 15,  # 15 second timeout per search
    'rate_limit': 1.0,  # 1 second between searches (SerpAPI allows 1 req/sec free)
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
    'bing.com', 'yahoo.com', 'directories.com',
    
    # Industry Association Domains
    'phccwa.org',  # Plumbing-Heating-Cooling Contractors of Washington
    'phccnational.org',  # PHCC National
    'neca.org',  # National Electrical Contractors Association
    'nrca.net',  # National Roofing Contractors Association
    'abc.org',  # Associated Builders and Contractors
    'nahb.org',  # National Association of Home Builders
    'nari.org',  # National Association of the Remodeling Industry
    'contractorsassociation.org',  # Generic contractor associations
    'buildersassociation.org',  # Generic builders associations
    'washingtonstatecontractors.org',  # Washington State specific
    'oregoncontractors.org',  # Oregon specific
    'idahocontractors.org',  # Idaho specific
}

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