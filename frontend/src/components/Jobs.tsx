import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Alert,
  Fab,
  Tooltip,
  Autocomplete,
  CircularProgress,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Add,
  Refresh,
  Delete,
  Visibility,
  Search,
  Dashboard,
  FilterList,
  DataUsage,
} from '@mui/icons-material';
import { scrapingAPI } from '../api';
import { ScrapingJob, CreateJobData, DomainInfo } from '../types';

export default function Jobs() {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<ScrapingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [availableDomains, setAvailableDomains] = useState<DomainInfo[]>([]);
  const [domainsLoading, setDomainsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [newJob, setNewJob] = useState<CreateJobData>({
    name: '',
    domains: [],
    concurrent_requests: 5,
    request_delay: 1.0,
  });

  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
    fetchAvailableDomains();
    const interval = setInterval(() => {
      fetchJobs();
      fetchAvailableDomains();
    }, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Filter jobs based on search term and status
  useEffect(() => {
    let filtered = jobs;

    if (searchTerm) {
      filtered = filtered.filter(job => 
        job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.domains.some(domain => domain.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (job.current_city && job.current_city.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(job => (job.status || 'pending') === statusFilter);
    }

    setFilteredJobs(filtered);
  }, [jobs, searchTerm, statusFilter]);

  const fetchJobs = async () => {
    try {
      setError(null);
      const response = await scrapingAPI.listJobs();
      setJobs(response.data);
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error('Jobs error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableDomains = async () => {
    try {
      setDomainsLoading(true);
      const response = await scrapingAPI.getAvailableDomains();
      setAvailableDomains(response.data.available_domains);
    } catch (err) {
      console.error('Failed to fetch available domains:', err);
      // Fallback to empty array if API fails
      setAvailableDomains([]);
    } finally {
      setDomainsLoading(false);
    }
  };

  const handleCreateJob = async () => {
    try {
      if (!newJob.name || newJob.domains.length === 0) {
        setError('Please fill in all required fields');
        return;
      }

      await scrapingAPI.createJob(newJob);
      setCreateDialogOpen(false);
      setNewJob({
        name: '',
        domains: [],
        concurrent_requests: 5,
        request_delay: 1.0,
      });
      fetchJobs();
      fetchAvailableDomains(); // Refresh available domains after creating job
    } catch (err) {
      setError('Failed to create job');
      console.error('Create job error:', err);
    }
  };

  const handleJobAction = async (jobId: string, action: 'start' | 'pause' | 'resume' | 'cancel') => {
    try {
      setError(null);
      switch (action) {
        case 'start':
          await scrapingAPI.startJob(jobId);
          break;
        case 'pause':
          await scrapingAPI.pauseJob(jobId);
          break;
        case 'resume':
          await scrapingAPI.resumeJob(jobId);
          break;
        case 'cancel':
          await scrapingAPI.cancelJob(jobId);
          break;
      }
      fetchJobs();
      fetchAvailableDomains(); // Refresh available domains after job action
    } catch (err) {
      setError(`Failed to ${action} job`);
      console.error(`${action} job error:`, err);
    }
  };

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'running': return 'success';
      case 'completed': return 'info';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      case 'paused': return 'warning';
      case 'pending': return 'default';
      case null:
      case undefined: return 'default';
      default: return 'default';
    }
  };

  const getProgress = (job: ScrapingJob) => {
    if (job.total_businesses === 0) return 0;
    return (job.businesses_scraped / job.total_businesses) * 100;
  };

  const canStart = (status: string | null) => status === 'pending' || status === 'paused' || status === null;
  const canPause = (status: string | null) => status === 'running';
  const canCancel = (status: string | null) => ['pending', 'running', 'paused'].includes(status as string) || status === null;

  // Create display options for the Autocomplete
  const domainOptions = availableDomains.map((domainObj: DomainInfo) => ({
    label: `${domainObj.domain} (${domainObj.country})`,
    value: domainObj.domain,
    country: domainObj.country
  }));

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Scraping Jobs</Typography>
        <Box>
          <Button 
            variant="contained" 
            color="secondary"
            startIcon={<Dashboard />} 
            onClick={() => navigate('/enhanced-jobs')}
            sx={{ mr: 2 }}
          >
            Enhanced Jobs
          </Button>
          <Button startIcon={<Refresh />} onClick={fetchJobs} sx={{ mr: 1 }}>
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Add />} 
            onClick={() => {
              setCreateDialogOpen(true);
              fetchAvailableDomains(); // Refresh domains when opening dialog
            }}
          >
            New Job
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Search and Filter Controls */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <Box flex={1} minWidth="300px">
              <TextField
                fullWidth
                placeholder="Search by job name, domain, or city..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            <Box minWidth="200px">
              <FormControl fullWidth>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status Filter"
                  onChange={(e) => setStatusFilter(e.target.value)}
                  startAdornment={
                    <InputAdornment position="start">
                      <FilterList />
                    </InputAdornment>
                  }
                >
                  <MenuItem value="all">All Statuses</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="running">Running</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="paused">Paused</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                {filteredJobs.length} of {jobs.length} jobs
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Domain</TableCell>
                  <TableCell>Current Location</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredJobs.map((job) => (
                  <TableRow key={job._id}>
                    <TableCell>
                      <Typography variant="subtitle2">{job.name}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {job.concurrent_requests} concurrent • {job.request_delay}s delay
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={job.status || 'pending'} 
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ minWidth: 120 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={getProgress(job)} 
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="caption">
                          {job.businesses_scraped} / {job.total_businesses} businesses
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.domains.length > 0 ? job.domains[0].replace('https://', '') : 'No domain'}
                      </Typography>
                      {job.domains.length > 1 && (
                        <Typography variant="caption" color="textSecondary">
                          +{job.domains.length - 1} more
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.current_city || 'Not started'}
                      </Typography>
                      {job.current_page > 1 && (
                        <Typography variant="caption" color="textSecondary">
                          Page {job.current_page}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(job.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1} flexWrap="wrap" alignItems="center">
                        <Tooltip title="View Job Details">
                          <IconButton 
                            size="small"
                            onClick={() => navigate(`/jobs/${job._id}`)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="View Scraped Data">
                          <Button 
                            size="small"
                            variant="outlined"
                            color="primary"
                            startIcon={<DataUsage />}
                            onClick={() => navigate(`/businesses?job_id=${job._id}`)}
                            sx={{ mr: 1 }}
                          >
                            View Data
                          </Button>
                        </Tooltip>
                        
                        {canStart(job.status) && (
                          <Tooltip title={job.status === 'paused' ? 'Resume' : 'Start'}>
                            <IconButton 
                              size="small" 
                              color="success"
                              onClick={() => handleJobAction(job._id, job.status === 'paused' ? 'resume' : 'start')}
                            >
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        {canPause(job.status) && (
                          <Tooltip title="Pause">
                            <IconButton 
                              size="small" 
                              color="warning"
                              onClick={() => handleJobAction(job._id, 'pause')}
                            >
                              <Pause />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        {canCancel(job.status) && (
                          <Tooltip title="Cancel">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => handleJobAction(job._id, 'cancel')}
                            >
                              <Stop />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredJobs.length === 0 && jobs.length > 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="textSecondary">
                        No jobs match your search criteria.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {jobs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="textSecondary">
                        No jobs found. Create your first scraping job!
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create Job Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Scraping Job</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Job Name"
              value={newJob.name}
              onChange={(e) => setNewJob({ ...newJob, name: e.target.value })}
              sx={{ mb: 2 }}
              required
            />
            
            <Autocomplete
              fullWidth
              sx={{ mb: 2 }}
              options={domainOptions}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.value === value.value}
              value={domainOptions.find(option => option.value === newJob.domains[0]) || null}
              onChange={(_, value) => setNewJob({ ...newJob, domains: value ? [value.value] : [] })}
              loading={domainsLoading}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Domain to Scrape"
                  placeholder="Search by country or domain..."
                  required
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <React.Fragment>
                        {domainsLoading ? <CircularProgress color="inherit" size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </React.Fragment>
                    ),
                  }}
                />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {option.value}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.country}
                    </Typography>
                  </Box>
                </Box>
              )}
              noOptionsText={
                domainsLoading 
                  ? "Loading domains..." 
                  : "No available domains (all may be in use)"
              }
              clearOnBlur
              selectOnFocus
              handleHomeEndKeys
            />

            <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
              {availableDomains.length} domains available for scraping
            </Typography>

            <TextField
              fullWidth
              type="number"
              label="Concurrent Requests"
              value={newJob.concurrent_requests}
              onChange={(e) => setNewJob({ ...newJob, concurrent_requests: parseInt(e.target.value) })}
              sx={{ mb: 2 }}
              inputProps={{ min: 1, max: 20 }}
            />

            <TextField
              fullWidth
              type="number"
              label="Request Delay (seconds)"
              value={newJob.request_delay}
              onChange={(e) => setNewJob({ ...newJob, request_delay: parseFloat(e.target.value) })}
              inputProps={{ min: 0.1, max: 10, step: 0.1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateJob} variant="contained" disabled={domainsLoading}>
            Create Job
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
