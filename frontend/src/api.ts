import axios from 'axios';
import { ScrapingJob, Business, DashboardStats, CreateJobData, ExportRequest, JobStats, AvailableDomains, ApiExportConfig, ApiExportJob, ApiExportStats } from './types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Scraping API
export const scrapingAPI = {
  createJob: (data: CreateJobData) => 
    api.post<{ job_id: string; message: string }>('/scraping/jobs', data),
  
  startJob: (jobId: string) => 
    api.post(`/scraping/jobs/${jobId}/start`),
  
  pauseJob: (jobId: string) => 
    api.post(`/scraping/jobs/${jobId}/pause`),
  
  resumeJob: (jobId: string) => 
    api.post(`/scraping/jobs/${jobId}/resume`),
  
  cancelJob: (jobId: string) => 
    api.post(`/scraping/jobs/${jobId}/cancel`),
  
  getJobStatus: (jobId: string) => 
    api.get<ScrapingJob>(`/scraping/jobs/${jobId}/status`),
  
  listJobs: (skip = 0, limit = 20) => 
    api.get<ScrapingJob[]>(`/scraping/jobs?skip=${skip}&limit=${limit}`),
  
  getStats: () => 
    api.get<DashboardStats>('/public/stats'),
  
  // Available domains
  getAvailableDomains: () =>
    api.get<AvailableDomains>('/scraping/available-domains'),
  
  // Job details
  getJobDetails: (jobId: string) =>
    api.get<ScrapingJob>(`/scraping/jobs/${jobId}/details`),
  
  getJobStats: (jobId: string) =>
    api.get<JobStats>(`/public/businesses/jobs/${jobId}/stats`),
  
  // Network resilience
  pauseAllJobs: () => 
    api.post('/scraping/jobs/pause-all'),
  
  resumeAllJobs: () => 
    api.post('/scraping/jobs/resume-all'),
  
  resumeNetworkPausedJobs: () => 
    api.post('/scraping/jobs/resume-network-paused'),
  
  getStatusSummary: () => 
    api.get('/scraping/jobs/status-summary'),

  // New enhanced job management endpoints
  seedJobs: (overwrite: boolean = false) =>
    api.post(`/scraping/seed-jobs?overwrite=${overwrite}`),
  
  getCountriesSummary: () =>
    api.get('/scraping/countries-summary'),
  
  getSeededJobsStatus: () =>
    api.get('/scraping/seeded-jobs-status'),
  
  searchJobs: (params: {
    domain?: string;
    status?: string;
    region?: string;
    country?: string;
    sort_by?: string;
    sort_order?: string;
    skip?: number;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    return api.get(`/scraping/jobs/search?${queryParams.toString()}`);
  },
  
  updateJobSettings: (jobId: string, settings: {
    concurrent_requests?: number;
    request_delay?: number;
  }) =>
    api.put(`/scraping/jobs/${jobId}/settings`, settings),
};

// Businesses API
export const businessAPI = {
  listBusinesses: (params: {
    page?: number;
    limit?: number;
    domain?: string;
    city?: string;
    category?: string;
    search?: string;
    job_id?: string;
  } = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    return api.get(`/public/businesses?${queryParams.toString()}`);
  },
  
  getBusiness: (businessId: string) => 
    api.get<Business>(`/public/businesses/${businessId}`),
  
  getBusinessStats: () => 
    api.get('/public/stats'),
  
  // Get cities with business counts
  getCitiesWithCounts: (params: { country?: string; min_businesses?: number } = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    return api.get(`/public/cities?${queryParams.toString()}`);
  },
  
  // Get available domains
  getDomains: () =>
    api.get('/public/domains'),

  exportBusinesses: (params: {
    domain?: string;
    city?: string;
    category?: string;
  } = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value);
      }
    });
    return api.get(`/public/businesses/export/json?${queryParams.toString()}`, {
      responseType: 'blob'
    });
  },

  exportBusinessesEnhanced: (params: {
    sort_by?: string;
    sort_order?: string;
    region?: string;
    country?: string;
    domain?: string;
    format?: string;
  } = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value);
      }
    });
    return api.get(`/public/businesses/export/enhanced?${queryParams.toString()}`, {
      responseType: 'blob'
    });
  },

  // Export functions
  exportJobBusinesses: (jobId: string, exportRequest: ExportRequest) =>
    api.post(`/public/businesses/export/job/${jobId}`, exportRequest, { responseType: 'blob' }),
  
  markBusinessesExported: (exportRequest: ExportRequest) =>
    api.post('/public/businesses/mark-exported', exportRequest),
};

// API Export Management (Simplified)
export const apiExportAPI = {
  // Job management
  createExportJob: (jobData: {
    endpoint_url: string;
    auth_token?: string;
    request_method?: string;
    batch_size?: number;
    rate_limit_delay?: number;
    fields?: string[];
    filters?: any;
    auto_start?: boolean;
  }) =>
    api.post('/api-export/jobs', jobData),
  
  listExportJobs: (skip = 0, limit = 20) =>
    api.get(`/api-export/jobs?skip=${skip}&limit=${limit}`),
  
  getExportJob: (jobId: string) =>
    api.get(`/api-export/jobs/${jobId}`),
  
  startExportJob: (jobId: string) =>
    api.post(`/api-export/jobs/${jobId}/start`),
  
  stopExportJob: (jobId: string) =>
    api.post(`/api-export/jobs/${jobId}/stop`),
  
  deleteExportJob: (jobId: string) =>
    api.delete(`/api-export/jobs/${jobId}`),
  
  // Health check
  healthCheck: () =>
    api.get('/api-export/health'),
};
