import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  FormGroup,
  TextField,
  Alert,
  IconButton,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  ArrowBack,
  Download,
  Refresh,
  PlayArrow,
  Pause,
  Stop,
  GetApp,
  CheckCircle,
  Schedule,
} from '@mui/icons-material';
import { scrapingAPI, businessAPI } from '../api';
import { ScrapingJob, CityStats, BusinessSummary, ExportRequest, JobStats } from '../types';

const JobDetails: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  
  const [job, setJob] = useState<ScrapingJob | null>(null);
  const [jobStats, setJobStats] = useState<JobStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportDialog, setExportDialog] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [exportRequest, setExportRequest] = useState<ExportRequest>({
    export_mode: 'json',
    chunk_by_city: false,
  });

  const loadJobDetails = useCallback(async () => {
    try {
      setLoading(true);
      const response = await scrapingAPI.getJobDetails(jobId!);
      setJob(response.data);
    } catch (err) {
      setError('Failed to load job details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const loadJobStats = useCallback(async () => {
    try {
      const response = await scrapingAPI.getJobStats(jobId!);
      setJobStats(response.data);
    } catch (err) {
      console.error('Failed to load job stats:', err);
    }
  }, [jobId]);

  useEffect(() => {
    if (jobId) {
      loadJobDetails();
      loadJobStats();
    }
  }, [jobId, loadJobDetails, loadJobStats]);

  const handleJobAction = async (action: 'start' | 'pause' | 'cancel') => {
    try {
      if (action === 'start') {
        await scrapingAPI.startJob(jobId!);
      } else if (action === 'pause') {
        await scrapingAPI.pauseJob(jobId!);
      } else if (action === 'cancel') {
        await scrapingAPI.cancelJob(jobId!);
      }
      await loadJobDetails();
    } catch (err) {
      console.error(`Failed to ${action} job:`, err);
    }
  };

  const handleExport = async () => {
    try {
      setExportLoading(true);
      const exportData = {
        ...exportRequest,
        job_id: jobId,
      };
      
      // Export the businesses
      const response = await businessAPI.exportJobBusinesses(jobId!, exportData);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const filename = exportRequest.chunk_by_city 
        ? `job_${jobId}_businesses_by_city.zip`
        : `job_${jobId}_export_${exportRequest.export_mode}.json`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      // Mark as exported
      await businessAPI.markBusinessesExported(exportData);
      
      setExportDialog(false);
      await loadJobStats(); // Refresh stats
    } catch (err) {
      console.error('Export failed:', err);
      setError('Export failed. Please try again.');
    } finally {
      setExportLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getProgressPercentage = () => {
    if (!job) return 0;
    if (job.total_businesses === 0) return 0;
    return (job.businesses_scraped / job.total_businesses) * 100;
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>Loading job details...</Typography>
      </Container>
    );
  }

  if (error || !job) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error || 'Job not found'}</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/jobs')} sx={{ mt: 2 }}>
          Back to Jobs
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/jobs')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4" component="h1">
            {job.name}
          </Typography>
          <Chip 
            label={job.status} 
            color={getStatusColor(job.status || 'pending')} 
            variant="outlined"
          />
        </Box>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadJobDetails}>
              <Refresh />
            </IconButton>
          </Tooltip>
          
          {job.status === 'pending' || job.status === 'paused' ? (
            <Button
              startIcon={<PlayArrow />}
              variant="contained"
              color="primary"
              onClick={() => handleJobAction('start')}
            >
              Start
            </Button>
          ) : null}
          
          {job.status === 'running' ? (
            <Button
              startIcon={<Pause />}
              variant="outlined"
              color="warning"
              onClick={() => handleJobAction('pause')}
            >
              Pause
            </Button>
          ) : null}
          
          {['running', 'paused'].includes(job.status || '') ? (
            <Button
              startIcon={<Stop />}
              variant="outlined"
              color="error"
              onClick={() => handleJobAction('cancel')}
            >
              Cancel
            </Button>
          ) : null}
        </Box>
      </Box>

      <Stack spacing={3}>
        {/* Job Overview */}
        <Box display="flex" gap={3} flexWrap="wrap">
          <Box flex={2} minWidth="400px">
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job Overview
                </Typography>
                
                <Box display="flex" flexWrap="wrap" gap={2}>
                  <Box flex="1 1 150px">
                    <Typography variant="body2" color="textSecondary">
                      Domain
                    </Typography>
                    <Typography variant="body1">
                      {job.domains[0]}
                    </Typography>
                  </Box>
                  
                  <Box flex="1 1 150px">
                    <Typography variant="body2" color="textSecondary">
                      Created
                    </Typography>
                    <Typography variant="body1">
                      {new Date(job.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                  
                  <Box flex="1 1 150px">
                    <Typography variant="body2" color="textSecondary">
                      Cities
                    </Typography>
                    <Typography variant="body1">
                      {job.cities_completed} / {job.total_cities}
                    </Typography>
                  </Box>
                  
                  <Box flex="1 1 150px">
                    <Typography variant="body2" color="textSecondary">
                      Current Page
                    </Typography>
                    <Typography variant="body1">
                      {job.current_page}
                    </Typography>
                  </Box>
                </Box>

                {/* Progress */}
                <Box mt={3}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="textSecondary">
                      Scraping Progress
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {job.businesses_scraped} / {job.total_businesses} businesses
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={getProgressPercentage()} 
                    sx={{ mt: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    {getProgressPercentage().toFixed(1)}% complete
                  </Typography>
                </Box>

                {/* Current Status */}
                {job.status === 'running' && (
                  <Box mt={2}>
                    <Typography variant="body2" color="textSecondary">
                      Currently scraping: <strong>{job.current_city}</strong>
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>

          {/* Export Card */}
          <Box flex={1} minWidth="300px">
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Export
                </Typography>
                
                {jobStats && (
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary">
                      Total Businesses: <strong>{jobStats.total_businesses}</strong>
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Exported: <strong>{jobStats.exported_businesses}</strong>
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Remaining: <strong>{jobStats.total_businesses - jobStats.exported_businesses}</strong>
                    </Typography>
                  </Box>
                )}
                
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<Download />}
                  onClick={() => setExportDialog(true)}
                  disabled={!jobStats || jobStats.total_businesses === 0}
                >
                  Export Data
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* City Statistics */}
        {job.city_stats && job.city_stats.length > 0 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cities Progress
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>City</TableCell>
                      <TableCell align="right">Total Businesses</TableCell>
                      <TableCell align="right">Exported</TableCell>
                      <TableCell align="right">Remaining</TableCell>
                      <TableCell align="center">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {job.city_stats.map((city: CityStats) => (
                      <TableRow key={city.city}>
                        <TableCell>{city.city}</TableCell>
                        <TableCell align="right">{city.total_businesses}</TableCell>
                        <TableCell align="right">{city.exported_businesses}</TableCell>
                        <TableCell align="right">
                          {city.total_businesses - city.exported_businesses}
                        </TableCell>
                        <TableCell align="center">
                          {city.exported_businesses === city.total_businesses ? (
                            <CheckCircle color="success" />
                          ) : (
                            <Schedule color="action" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {/* Latest Businesses */}
        {job.latest_businesses && job.latest_businesses.length > 0 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Latest Scraped Businesses
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Business Name</TableCell>
                      <TableCell>City</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Scraped At</TableCell>
                      <TableCell align="center">Export Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {job.latest_businesses.map((business: BusinessSummary) => (
                      <TableRow key={business.id}>
                        <TableCell>{business.name}</TableCell>
                        <TableCell>{business.city}</TableCell>
                        <TableCell>{business.category}</TableCell>
                        <TableCell>
                          {new Date(business.scraped_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell align="center">
                          {business.exported_at ? (
                            <Chip 
                              label={business.export_mode || 'exported'} 
                              color="success" 
                              size="small"
                            />
                          ) : (
                            <Chip 
                              label="pending" 
                              color="default" 
                              size="small"
                            />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}
      </Stack>

      {/* Export Dialog */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Export Job Data</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl component="fieldset" fullWidth sx={{ mb: 3 }}>
              <FormLabel component="legend">Export Mode</FormLabel>
              <RadioGroup
                value={exportRequest.export_mode}
                onChange={(e) => setExportRequest(prev => ({ ...prev, export_mode: e.target.value as 'json' | 'api' }))}
              >
                <FormControlLabel value="json" control={<Radio />} label="JSON File Download" />
                <FormControlLabel value="api" control={<Radio />} label="API Export (for live server)" />
              </RadioGroup>
            </FormControl>

            <FormGroup sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportRequest.chunk_by_city}
                    onChange={(e) => setExportRequest(prev => ({ ...prev, chunk_by_city: e.target.checked }))}
                  />
                }
                label="Chunk by City (separate file per city)"
              />
            </FormGroup>

            {exportRequest.chunk_by_city && (
              <Alert severity="info" sx={{ mb: 2 }}>
                This will create a ZIP file containing separate JSON files for each city.
              </Alert>
            )}

            <TextField
              fullWidth
              label="Filter by City (optional)"
              value={exportRequest.city || ''}
              onChange={(e) => setExportRequest(prev => ({ ...prev, city: e.target.value }))}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Filter by Category (optional)"
              value={exportRequest.category || ''}
              onChange={(e) => setExportRequest(prev => ({ ...prev, category: e.target.value }))}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)} disabled={exportLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleExport} 
            variant="contained" 
            disabled={exportLoading}
            startIcon={<GetApp />}
          >
            {exportLoading ? 'Exporting...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default JobDetails;
