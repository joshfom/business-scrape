export interface ScrapingJob {
  _id: string;
  name: string;
  domains: string[];
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | null;
  concurrent_requests: number;
  request_delay: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total_cities: number;
  cities_completed: number;
  total_businesses: number;
  businesses_scraped: number;
  current_domain?: string;
  current_city?: string;
  current_page: number;
  errors: string[];
  // New fields for detailed job view
  city_stats?: CityStats[];
  latest_businesses?: BusinessSummary[];
  total_scraped_businesses?: number;
  total_exported_businesses?: number;
}

export interface CityStats {
  city: string;
  total_businesses: number;
  exported_businesses: number;
}

export interface BusinessSummary {
  id: string;
  name: string;
  city: string;
  category: string;
  scraped_at: string;
  exported_at?: string;
  export_mode?: 'json' | 'api';
}

export interface Business {
  _id: string;
  title: string;
  name: string;
  country: string;
  city: string;
  category: string;
  coordinates?: { lat: number; lng: number };
  phone?: string;
  mobile?: string;
  fax?: string;
  website?: string;
  address?: string;
  working_hours?: { [key: string]: string };
  description?: string;
  tags?: string[];
  reviews_count?: number;
  rating?: number;
  established_year?: number;
  employees?: string;
  page_url: string;
  domain: string;
  scraped_at: string;
  exported_at?: string;
  export_mode?: 'json' | 'api';
}

export interface DashboardStats {
  total_jobs: number;
  active_jobs: number;
  total_businesses: number;
  businesses_today: number;
  domains_configured: number;
  last_scrape?: string;
}

export interface CreateJobData {
  name: string;
  domains: string[];
  concurrent_requests: number;
  request_delay: number;
}

export interface ExportRequest {
  job_id?: string;
  domain?: string;
  city?: string;
  category?: string;
  export_mode: 'json' | 'api';
  chunk_by_city: boolean;
}

export interface ApiExportConfig {
  id?: string;
  name: string;
  endpoint_url: string;
  bearer_token: string;
  http_method: 'POST' | 'PUT' | 'PATCH';
  batch_size: number;
  timeout_seconds: number;
  retry_attempts: number;
  retry_delay_seconds: number;
  headers?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
}

export interface ApiExportJob {
  id: string;
  config_id: string;
  config_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  filter_criteria: ExportRequest;
  total_businesses: number;
  processed_businesses: number;
  successful_exports: number;
  failed_exports: number;
  current_batch: number;
  total_batches: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  progress_percentage: number;
}

export interface ApiExportStats {
  total_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_businesses_exported: number;
}

export interface JobStats {
  job_id: string;
  total_businesses: number;
  exported_businesses: number;
  cities: string[];
  domains: string[];
  export_summary: Record<string, any>;
}

export interface AvailableDomains {
  available_domains: DomainInfo[];
  total_domains: number;
  available_count: number;
  active_count: number;
}

export interface DomainInfo {
  domain: string;
  country: string;
}
