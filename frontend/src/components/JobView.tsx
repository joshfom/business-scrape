import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Paper,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  ArrowBack,
  Refresh,
} from '@mui/icons-material';
import { scrapingAPI } from '../api';
import { ScrapingJob } from '../types';

export default function JobView() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<ScrapingJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      fetchJob();
      const interval = setInterval(fetchJob, 5000);
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const fetchJob = async () => {
    if (!jobId) return;
    
    try {
      setError(null);
      const response = await scrapingAPI.getJobStatus(jobId);
      setJob(response.data);
    } catch (err) {
      setError('Failed to fetch job details');
      console.error('Job fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleJobAction = async (action: 'start' | 'pause' | 'resume' | 'cancel') => {
    if (!jobId) return;

    try {
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
      fetchJob();
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading job details...</Typography>
      </Box>
    );
  }

  if (!job) {
    return (
      <Box>
        <Alert severity="error">Job not found</Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/jobs')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          {job.name}
        </Typography>
        <Box display="flex" gap={1}>
          <Button startIcon={<Refresh />} onClick={fetchJob}>
            Refresh
          </Button>
          {canStart(job.status) && (
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={() => handleJobAction(job.status === 'paused' ? 'resume' : 'start')}
            >
              {job.status === 'paused' ? 'Resume' : 'Start'}
            </Button>
          )}
          {canPause(job.status) && (
            <Button
              variant="contained"
              color="warning"
              startIcon={<Pause />}
              onClick={() => handleJobAction('pause')}
            >
              Pause
            </Button>
          )}
          {canCancel(job.status) && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<Stop />}
              onClick={() => handleJobAction('cancel')}
            >
              Cancel
            </Button>
          )}
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
          gap: 3 
        }}
      >
        {/* Job Overview */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Job Overview
            </Typography>
            
            <Box display="flex" alignItems="center" mb={2}>
              <Typography variant="body1" sx={{ mr: 2 }}>
                Status:
              </Typography>
              <Chip 
                label={job.status || 'pending'} 
                color={getStatusColor(job.status) as any}
                size="medium"
              />
            </Box>

            <Box mb={3}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Progress: {job.businesses_scraped} / {job.total_businesses} businesses
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={getProgress(job)}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="textSecondary">
                {getProgress(job).toFixed(1)}% complete
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box 
              sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                gap: 2 
              }}
            >
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Domain
                </Typography>
                <Typography variant="body1">
                  {job.domains[0]}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Created
                </Typography>
                <Typography variant="body1">
                  {new Date(job.created_at).toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Concurrent Requests
                </Typography>
                <Typography variant="body1">
                  {job.concurrent_requests}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Request Delay
                </Typography>
                <Typography variant="body1">
                  {job.request_delay}s
                </Typography>
              </Box>
              {job.started_at && (
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Started
                  </Typography>
                  <Typography variant="body1">
                    {new Date(job.started_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
              {job.completed_at && (
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Completed
                  </Typography>
                  <Typography variant="body1">
                    {new Date(job.completed_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Current Status */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Status
            </Typography>
            
            {job.current_city ? (
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Current City
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {job.current_city}
                </Typography>
                
                <Typography variant="body2" color="textSecondary">
                  Current Page
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {job.current_page}
                </Typography>
              </Box>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Job not started yet
              </Typography>
            )}

            <Divider sx={{ my: 2 }} />

            <Typography variant="body2" color="textSecondary">
              Cities Progress
            </Typography>
            <Typography variant="body1">
              {job.cities_completed} / {job.total_cities} cities
            </Typography>
            
            {job.total_cities > 0 && (
              <LinearProgress 
                variant="determinate" 
                value={(job.cities_completed / job.total_cities) * 100}
                sx={{ mt: 1, height: 6, borderRadius: 3 }}
              />
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Errors (if any) */}
      {job.errors && job.errors.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom color="error">
              Errors ({job.errors.length})
            </Typography>
            <Paper sx={{ maxHeight: 200, overflow: 'auto', p: 1 }}>
              <List dense>
                {job.errors.map((error, index) => (
                  <ListItem key={index}>
                    <ListItemText 
                      primary={error}
                      primaryTypographyProps={{ 
                        variant: 'body2',
                        color: 'error'
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
