"""
Data models for contractor enrichment system
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import sys
import os

# Add src to path for imports  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


@dataclass
class Contractor:
    """Contractor data model"""
    
    # Database fields
    id: Optional[int] = None
    uuid: Optional[str] = None
    
    # Original contractor data (from CSV)
    business_name: str = ""
    contractor_license_number: Optional[str] = None
    contractor_license_type_code: Optional[str] = None
    contractor_license_type_code_desc: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    phone_number: Optional[str] = None
    license_effective_date: Optional[datetime] = None
    license_expiration_date: Optional[datetime] = None
    business_type_code: Optional[str] = None
    business_type_code_desc: Optional[str] = None
    specialty_code1: Optional[str] = None
    specialty_code1_desc: Optional[str] = None
    specialty_code2: Optional[str] = None
    specialty_code2_desc: Optional[str] = None
    ubi: Optional[str] = None
    primary_principal_name: Optional[str] = None
    status_code: Optional[str] = None
    contractor_license_status: Optional[str] = None
    contractor_license_suspend_date: Optional[datetime] = None
    
    # Enriched data fields
    is_home_contractor: Optional[bool] = None
    mailer_category: Optional[str] = None
    priority_category: bool = False
    website_url: Optional[str] = None
    website_status: Optional[str] = None
    business_description: Optional[str] = None
    tagline: Optional[str] = None
    established_year: Optional[int] = None
    years_in_business: Optional[int] = None
    services_offered: Optional[List[str]] = None
    service_categories: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    additional_licenses: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    insurance_types: Optional[List[str]] = None
    website_email: Optional[str] = None
    website_phone: Optional[str] = None
    physical_address: Optional[str] = None
    social_media_urls: Optional[Dict[str, str]] = None
    residential_focus: Optional[bool] = None
    commercial_focus: Optional[bool] = None
    emergency_services: Optional[bool] = None
    free_estimates: Optional[bool] = None
    warranty_offered: Optional[bool] = None
    
    # Processing and quality fields
    confidence_score: Optional[float] = None
    classification_confidence: Optional[float] = None
    website_confidence: Optional[float] = None
    processing_status: str = 'pending'
    last_processed: Optional[datetime] = None
    error_message: Optional[str] = None
    manual_review_needed: bool = False
    manual_review_reason: Optional[str] = None
    
    # Manual review workflow fields
    review_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    manual_review_outcome: Optional[str] = None
    marked_for_download: bool = False
    marked_for_download_at: Optional[datetime] = None
    exported_at: Optional[datetime] = None
    export_batch_id: Optional[int] = None
    
    # Analysis storage
    gpt4mini_analysis: Optional[Dict[str, Any]] = None
    gpt4_verification: Optional[Dict[str, Any]] = None
    data_sources: Optional[Dict[str, Any]] = None
    website_content_hash: Optional[str] = None
    processing_attempts: int = 0
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                result[key] = None
            elif isinstance(value, datetime):
                result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = json.dumps(value) if value else None
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contractor':
        """Create instance from dictionary"""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance


@dataclass
class MailerCategory:
    """Mailer category data model"""
    
    record_id: Optional[int] = None
    category_name: str = ""
    priority: bool = False
    afb_name: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    typical_services: Optional[List[str]] = None
    active: bool = True
    sort_order: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class WebsiteSearch:
    """Website search attempt model"""
    
    id: Optional[int] = None
    contractor_id: int = 0
    search_query: Optional[str] = None
    search_method: Optional[str] = None
    results_found: int = 0
    search_results: Optional[Dict[str, Any]] = None
    attempted_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class WebsiteCrawl:
    """Website crawl attempt model"""
    
    id: Optional[int] = None
    contractor_id: int = 0
    url: str = ""
    crawl_status: Optional[str] = None
    response_code: Optional[int] = None
    content_length: Optional[int] = None
    crawl_duration_seconds: Optional[float] = None
    content_hash: Optional[str] = None
    raw_content: Optional[str] = None
    structured_content: Optional[Dict[str, Any]] = None
    attempted_at: Optional[datetime] = None


@dataclass
class ProcessingLog:
    """Processing log entry model"""
    
    id: Optional[int] = None
    contractor_id: int = 0
    processing_step: str = ""
    step_status: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None