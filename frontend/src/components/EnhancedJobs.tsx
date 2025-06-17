import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Alert,
  Snackbar,
  Tooltip,
  LinearProgress,
  Pagination,
  Stack,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Refresh,
  FilterList,
  CloudDownload,
  Visibility,
  Assignment,
  RestartAlt,
} from '@mui/icons-material';
import { scrapingAPI } from '../api';

interface JobSearchFilters {
  domain: string;
  status: string;
  region: string;
  country: string;
  sort_by: string;
  sort_order: string;
}

interface JobSettingsData {
  concurrent_requests: number;
  request_delay: number;
}

interface SeededJobsStatus {
  regions: Array<{
    name: string;
    total_jobs: number;
    completed: number;
    running: number;
    pending: number;
    failed: number;
    cancelled: number;
    paused: number;
    jobs: any[];
  }>;
  total_seeded_jobs: number;
  jobs: any[];
}

export default function EnhancedJobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [seededJobsStatus, setSeededJobsStatus] = useState<SeededJobsStatus | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  // Filter state
  const [filters, setFilters] = useState<JobSearchFilters>({
    domain: '',
    status: '',
    region: '',
    country: '',
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  // Job settings dialog
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [jobSettings, setJobSettings] = useState<JobSettingsData>({
    concurrent_requests: 5,
    request_delay: 1.0,
  });

  // Seeding state
  const [seedingInProgress, setSeedingInProgress] = useState(false);

  const itemsPerPage = 20;

  useEffect(() => {
    fetchJobs();
    fetchSeededJobsStatus();
    const interval = setInterval(() => {
      fetchJobs();
      fetchSeededJobsStatus();
    }, 10000);
    return () => clearInterval(interval);
  }, [filters, currentPage]);

  const fetchJobs = async () => {
    try {
      setError(null);
      const skip = (currentPage - 1) * itemsPerPage;
      const response = await scrapingAPI.searchJobs({
        ...filters,
        skip,
        limit: itemsPerPage,
      });
      setJobs(response.data.jobs);
      setTotalCount(response.data.total_count);
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error('Jobs error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSeededJobsStatus = async () => {
    try {
      const response = await scrapingAPI.getSeededJobsStatus();
      setSeededJobsStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch seeded jobs status:', err);
    }
  };

  const handleSeedJobs = async (overwrite: boolean = false) => {
    try {
      setSeedingInProgress(true);
      const response = await scrapingAPI.seedJobs(overwrite);
      setSnackbarMessage(
        `Job seeding completed! Created: ${response.data.results.jobs_created}, Skipped: ${response.data.results.jobs_skipped}`
      );
      setSnackbarOpen(true);
      fetchJobs();
      fetchSeededJobsStatus();
    } catch (err) {
      setError('Failed to seed jobs');
      console.error('Seeding error:', err);
    } finally {
      setSeedingInProgress(false);
    }
  };

  const handleJobAction = async (jobId: string, action: string) => {
    try {
      switch (action) {
        case 'start':
          await scrapingAPI.startJob(jobId);
          break;
        case 'pause':
          await scrapingAPI.pauseJob(jobId);
          break;
        case 'cancel':
          await scrapingAPI.cancelJob(jobId);
          break;
        case 'resume':
          await scrapingAPI.resumeJob(jobId);
          break;
        case 'force_start':
          // Force start: pause first, then start to reset any stuck states
          try {
            await scrapingAPI.pauseJob(jobId);
            // Small delay to ensure pause is processed
            setTimeout(async () => {
              await scrapingAPI.startJob(jobId);
              setSnackbarMessage('Job force started successfully');
              setSnackbarOpen(true);
              fetchJobs();
            }, 1000);
            return; // Early return to avoid duplicate messages
          } catch (err) {
            // If pause fails, try direct start
            await scrapingAPI.startJob(jobId);
          }
          break;
      }
      setSnackbarMessage(`Job ${action} action completed`);
      setSnackbarOpen(true);
      fetchJobs();
    } catch (err) {
      setError(`Failed to ${action} job`);
      console.error(`${action} error:`, err);
    }
  };

  const handleUpdateJobSettings = async () => {
    if (!selectedJobId) return;
    
    try {
      await scrapingAPI.updateJobSettings(selectedJobId, jobSettings);
      setSnackbarMessage('Job settings updated successfully');
      setSnackbarOpen(true);
      setSettingsDialogOpen(false);
      fetchJobs();
    } catch (err) {
      setError('Failed to update job settings');
      console.error('Settings update error:', err);
    }
  };

  const openSettingsDialog = (job: any) => {
    setSelectedJobId(job._id);
    setJobSettings({
      concurrent_requests: job.concurrent_requests || 5,
      request_delay: job.request_delay || 1.0,
    });
    setSettingsDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'paused': return 'warning';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      default: return 'info';
    }
  };

  const renderJobActions = (job: any) => {
    const canStart = ['pending', 'paused'].includes(job.status);
    const canPause = job.status === 'running';
    const canResume = job.status === 'paused';
    const canCancel = ['pending', 'running', 'paused'].includes(job.status);
    const canForceStart = ['running', 'paused', 'failed'].includes(job.status);

    return (
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {canStart && (
          <Tooltip title="Start Job">
            <IconButton
              size="small"
              color="primary"
              onClick={() => handleJobAction(job._id, 'start')}
            >
              <PlayArrow />
            </IconButton>
          </Tooltip>
        )}
        {canPause && (
          <Tooltip title="Pause Job">
            <IconButton
              size="small"
              color="warning"
              onClick={() => handleJobAction(job._id, 'pause')}
            >
              <Pause />
            </IconButton>
          </Tooltip>
        )}
        {canResume && (
          <Tooltip title="Resume Job">
            <IconButton
              size="small"
              color="primary"
              onClick={() => handleJobAction(job._id, 'resume')}
            >
              <PlayArrow />
            </IconButton>
          </Tooltip>
        )}
        {canForceStart && (
          <Tooltip title="Force Start (Reset & Restart)">
            <IconButton
              size="small"
              color="secondary"
              onClick={() => handleJobAction(job._id, 'force_start')}
            >
              <RestartAlt />
            </IconButton>
          </Tooltip>
        )}
        {canCancel && (
          <Tooltip title="Cancel Job">
            <IconButton
              size="small"
              color="error"
              onClick={() => handleJobAction(job._id, 'cancel')}
            >
              <Stop />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="View Job Details">
          <IconButton
            size="small"
            onClick={() => navigate(`/jobs/${job._id}`)}
          >
            <Assignment />
          </IconButton>
        </Tooltip>
        <Tooltip title="View Scraped Data">
          <IconButton
            size="small"
            onClick={() => navigate(`/businesses?job_id=${job._id}`)}
          >
            <Visibility />
          </IconButton>
        </Tooltip>
        <Tooltip title="Job Settings">
          <IconButton
            size="small"
            onClick={() => openSettingsDialog(job)}
          >
            <Settings />
          </IconButton>
        </Tooltip>
      </Box>
    );
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Management
      </Typography>

      {/* Seeded Jobs Overview */}
      {seededJobsStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Countries Overview
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Seeded Jobs: {seededJobsStatus.total_seeded_jobs}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {seededJobsStatus.regions.map((region) => (
                  <Chip
                    key={region.name}
                    label={`${region.name}: ${region.total_jobs}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          onClick={() => handleSeedJobs(false)}
          disabled={seedingInProgress}
          startIcon={<CloudDownload />}
        >
          {seedingInProgress ? 'Seeding...' : 'Seed New Jobs'}
        </Button>
        <Button
          variant="outlined"
          onClick={() => handleSeedJobs(true)}
          disabled={seedingInProgress}
          color="warning"
        >
          Reseed All Jobs (Overwrites)
        </Button>
        <Button
          variant="outlined"
          onClick={() => fetchJobs()}
          startIcon={<Refresh />}
        >
          Refresh
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <FilterList sx={{ mr: 1, verticalAlign: 'middle' }} />
            Filters & Search
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ gap: 2 }}>
            <TextField
              label="Domain"
              value={filters.domain}
              onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
              size="small"
              sx={{ minWidth: 200 }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                label="Status"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="paused">Paused</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Region"
              value={filters.region}
              onChange={(e) => setFilters({ ...filters, region: e.target.value })}
              size="small"
              sx={{ minWidth: 150 }}
            />
            <TextField
              label="Country"
              value={filters.country}
              onChange={(e) => setFilters({ ...filters, country: e.target.value })}
              size="small"
              sx={{ minWidth: 150 }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={filters.sort_by}
                onChange={(e) => setFilters({ ...filters, sort_by: e.target.value })}
                label="Sort By"
              >
                <MenuItem value="created_at">Created Date</MenuItem>
                <MenuItem value="country">Country</MenuItem>
                <MenuItem value="region">Region</MenuItem>
                <MenuItem value="status">Status</MenuItem>
                <MenuItem value="businesses_scraped">Businesses Scraped</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Order</InputLabel>
              <Select
                value={filters.sort_order}
                onChange={(e) => setFilters({ ...filters, sort_order: e.target.value })}
                label="Order"
              >
                <MenuItem value="desc">Desc</MenuItem>
                <MenuItem value="asc">Asc</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      {/* Jobs Table */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Country/Region</TableCell>
                  <TableCell>Domain</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Settings</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job._id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {job.country || 'Unknown'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {job.region || 'Unknown'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.domains?.[0] || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" display="block">
                        Cities: {job.cities_completed}/{job.total_cities}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Businesses: {job.businesses_scraped}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" display="block">
                        Concurrency: {job.concurrent_requests}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Delay: {job.request_delay}s
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {renderJobActions(job)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={(_, page) => setCurrentPage(page)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* Job Settings Dialog */}
      <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)}>
        <DialogTitle>Job Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography gutterBottom>
              Concurrent Requests: {jobSettings.concurrent_requests}
            </Typography>
            <Slider
              value={jobSettings.concurrent_requests}
              onChange={(_, value) =>
                setJobSettings({ ...jobSettings, concurrent_requests: value as number })
              }
              min={1}
              max={20}
              marks
              valueLabelDisplay="auto"
            />
            
            <Typography gutterBottom sx={{ mt: 3 }}>
              Request Delay: {jobSettings.request_delay}s
            </Typography>
            <Slider
              value={jobSettings.request_delay}
              onChange={(_, value) =>
                setJobSettings({ ...jobSettings, request_delay: value as number })
              }
              min={0.1}
              max={10}
              step={0.1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateJobSettings} variant="contained">
            Update Settings
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
}
