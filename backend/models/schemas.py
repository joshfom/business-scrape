from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportMode(str, Enum):
    JSON = "json"
    API = "api"

class BusinessData(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    name: str
    country: str
    city: str
    category: str
    coordinates: Optional[Dict[str, float]] = None  # {lat: float, lng: float}
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    working_hours: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    reviews_count: Optional[int] = None
    rating: Optional[float] = None
    established_year: Optional[int] = None
    employees: Optional[str] = None
    page_url: str
    domain: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    exported_at: Optional[datetime] = None
    export_mode: Optional[ExportMode] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScrapingJob(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    domains: List[str]
    status: ScrapingStatus = ScrapingStatus.PENDING
    concurrent_requests: int = 5
    request_delay: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_cities: int = 0
    cities_completed: int = 0
    total_businesses: int = 0
    businesses_scraped: int = 0
    current_domain: Optional[str] = None
    current_city: Optional[str] = None
    current_page: int = 1
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScrapingJobCreate(BaseModel):
    name: str
    domains: List[str]
    concurrent_requests: int = 5
    request_delay: float = 1.0

class ScrapingProgress(BaseModel):
    job_id: str
    domain: str
    city: str
    page: int
    businesses_found: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class CityData(BaseModel):
    name: str
    url: str
    business_count: int
    domain: str

class DashboardStats(BaseModel):
    total_jobs: int
    active_jobs: int
    total_businesses: int
    businesses_today: int
    domains_configured: int
    last_scrape: Optional[datetime] = None

class ExportRequest(BaseModel):
    job_id: Optional[str] = None
    domain: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    export_mode: ExportMode = ExportMode.JSON
    chunk_by_city: bool = False

class JobStats(BaseModel):
    job_id: str
    total_businesses: int
    exported_businesses: int
    cities: List[str]
    domains: List[str]
    export_summary: Dict[str, Any] = Field(default_factory=dict)

# API Export Schemas

class ApiExportStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ApiExportConfig(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    endpoint_url: str
    bearer_token: str
    batch_size: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    mapping_config: Dict[str, str] = Field(default_factory=dict)  # Maps our fields to API fields
    filters: Dict[str, Any] = Field(default_factory=dict)  # Filters to apply to data
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ApiExportConfigCreate(BaseModel):
    name: str
    endpoint_url: str
    bearer_token: str
    batch_size: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    mapping_config: Dict[str, str] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class ApiExportConfigUpdate(BaseModel):
    name: Optional[str] = None
    endpoint_url: Optional[str] = None
    bearer_token: Optional[str] = None
    batch_size: Optional[int] = None
    timeout: Optional[int] = None
    retry_attempts: Optional[int] = None
    retry_delay: Optional[int] = None
    mapping_config: Optional[Dict[str, str]] = None
    filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ApiExportJob(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    config_id: str
    status: ApiExportStatus = ApiExportStatus.PENDING
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ApiExportJobCreate(BaseModel):
    endpoint_url: str
    auth_token: Optional[str] = None
    request_method: str = "POST"
    batch_size: int = 100
    rate_limit_delay: float = 0.0
    fields: List[str] = Field(default_factory=list)
    filters: Optional[Dict[str, Any]] = None
    auto_start: bool = False

class ApiExportJobResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    config: Dict[str, Any]
    status: ApiExportStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_records: int = 0
    exported_records: int = 0
    failed_records: int = 0
    error_message: Optional[str] = None
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ApiExportLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    job_id: str
    batch_number: int
    records_count: int
    success: bool
    response_status: Optional[int] = None
    response_message: Optional[str] = None
    error_details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ApiExportStats(BaseModel):
    total_configs: int
    active_configs: int
    total_jobs: int
    jobs_today: int
    total_exported_records: int
    recent_jobs: List[ApiExportJob] = Field(default_factory=list)

class ConnectionTestRequest(BaseModel):
    endpoint_url: str
    bearer_token: str
