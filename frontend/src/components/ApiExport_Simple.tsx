import React, { useState, useEffect } from 'react';
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
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  RestartAlt,
  Send,
  CheckCircle,
  Warning,
  ExpandMore,
} from '@mui/icons-material';
import { scrapingAPI } from '../api';
import { ApiExportConfig, ApiExportJob, ApiExportStats, ExportRequest, ScrapingJob } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ApiExport() {
  const [tabValue, setTabValue] = useState(0);
  const [configs, setConfigs] = useState<ApiExportConfig[]>([]);
  const [exportJobs, setExportJobs] = useState<ApiExportJob[]>([]);
  const [stats, setStats] = useState<ApiExportStats | null>(null);
  const [scrapingJobs, setScrapingJobs] = useState<ScrapingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Config Dialog States
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ApiExportConfig | null>(null);
  const [newConfig, setNewConfig] = useState<Omit<ApiExportConfig, 'id' | 'created_at' | 'updated_at'>>({
    name: '',
    endpoint_url: '',
    bearer_token: '',
    http_method: 'POST',
    batch_size: 100,
    timeout_seconds: 30,
    retry_attempts: 3,
    retry_delay_seconds: 5,
    headers: {},
  });

  // Export Job Dialog States
  const [exportJobDialogOpen, setExportJobDialogOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<string>('');
  const [exportFilter, setExportFilter] = useState<ExportRequest>({
    export_mode: 'api',
    chunk_by_city: false,
  });

  // Test Config States
  const [testingConfig, setTestingConfig] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      // For now, just fetch scraping jobs since backend API export endpoints don't exist yet
      const scrapingJobsRes = await scrapingAPI.listJobs();
      setScrapingJobs(scrapingJobsRes.data);
      
      // Mock data for development
      setConfigs([]);
      setExportJobs([]);
      setStats({
        total_jobs: 0,
        running_jobs: 0,
        completed_jobs: 0,
        failed_jobs: 0,
        total_businesses_exported: 0,
      });
    } catch (err) {
      setError('Failed to fetch export data');
      console.error('Export data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConfig = async () => {
    try {
      console.log('Creating config:', newConfig);
      setConfigDialogOpen(false);
      resetConfigForm();
      alert('API configuration feature coming soon!');
    } catch (err) {
      setError('Failed to create API configuration');
      console.error('Create config error:', err);
    }
  };

  const resetConfigForm = () => {
    setNewConfig({
      name: '',
      endpoint_url: '',
      bearer_token: '',
      http_method: 'POST',
      batch_size: 100,
      timeout_seconds: 30,
      retry_attempts: 3,
      retry_delay_seconds: 5,
      headers: {},
    });
    setEditingConfig(null);
    setTestResult(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'completed': return 'info';
      case 'failed': return 'error';
      case 'cancelled': return 'default';
      case 'paused': return 'warning';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">API Export Management</Typography>
        <Button startIcon={<Refresh />} onClick={fetchData}>
          Refresh
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Coming Soon Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>🚀 API Export Feature Coming Soon!</Typography>
        <Typography>
          This page will allow you to configure API endpoints and automatically export scraped business data 
          to external APIs with bearer token authentication, batch processing, and retry logic.
        </Typography>
        <br />
        <Typography variant="body2" color="text.secondary">
          <strong>Features planned:</strong>
          <br />• Configure multiple API endpoints with authentication
          <br />• Batch export with configurable size and retry logic
          <br />• Real-time monitoring of export jobs
          <br />• Filter exports by job, domain, city, or date range
          <br />• Reset/restart failed exports to different endpoints
        </Typography>
      </Alert>

      {/* Preview of Stats Cards */}
      {stats && (
        <Box display="flex" gap={2} sx={{ mb: 3, flexWrap: 'wrap' }}>
          <Card sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Export Jobs</Typography>
              <Typography variant="h4">{stats.total_jobs}</Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Running</Typography>
              <Typography variant="h4" color="success.main">{stats.running_jobs}</Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Completed</Typography>
              <Typography variant="h4" color="info.main">{stats.completed_jobs}</Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Failed</Typography>
              <Typography variant="h4" color="error.main">{stats.failed_jobs}</Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200, flex: 1 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Businesses Exported</Typography>
              <Typography variant="h4">{stats.total_businesses_exported}</Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      <Card>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="API Configurations" />
          <Tab label="Export Jobs" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* API Configurations Tab */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">API Configurations</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => {
                resetConfigForm();
                setConfigDialogOpen(true);
              }}
            >
              Add Configuration (Preview)
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Endpoint</TableCell>
                  <TableCell>Method</TableCell>
                  <TableCell>Batch Size</TableCell>
                  <TableCell>Timeout</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary">
                      No API configurations found. Backend API endpoints coming soon!
                    </Typography>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Export Jobs Tab */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Export Jobs</Typography>
            <Button
              variant="contained"
              startIcon={<Send />}
              onClick={() => alert('Export job creation coming soon!')}
              disabled={true}
            >
              New Export Job (Preview)
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Configuration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Success Rate</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary">
                      No export jobs found. Backend API endpoints coming soon!
                    </Typography>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Card>

      {/* Config Creation Dialog - Preview */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create API Configuration (Preview)</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Configuration Name"
                value={newConfig.name}
                onChange={(e) => setNewConfig({ ...newConfig, name: e.target.value })}
                placeholder="My API Configuration"
                required
              />
              
              <TextField
                fullWidth
                label="API Endpoint URL"
                value={newConfig.endpoint_url}
                onChange={(e) => setNewConfig({ ...newConfig, endpoint_url: e.target.value })}
                placeholder="https://api.example.com/businesses"
                required
              />
              
              <TextField
                fullWidth
                label="Bearer Token"
                type="password"
                value={newConfig.bearer_token}
                onChange={(e) => setNewConfig({ ...newConfig, bearer_token: e.target.value })}
                placeholder="your-api-token-here"
                required
              />
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControl sx={{ minWidth: 120 }}>
                  <InputLabel>HTTP Method</InputLabel>
                  <Select
                    value={newConfig.http_method}
                    onChange={(e) => setNewConfig({ ...newConfig, http_method: e.target.value as any })}
                  >
                    <MenuItem value="POST">POST</MenuItem>
                    <MenuItem value="PUT">PUT</MenuItem>
                    <MenuItem value="PATCH">PATCH</MenuItem>
                  </Select>
                </FormControl>
                
                <TextField
                  type="number"
                  label="Batch Size"
                  value={newConfig.batch_size}
                  onChange={(e) => setNewConfig({ ...newConfig, batch_size: parseInt(e.target.value) })}
                  inputProps={{ min: 1, max: 1000 }}
                />
                
                <TextField
                  type="number"
                  label="Timeout (seconds)"
                  value={newConfig.timeout_seconds}
                  onChange={(e) => setNewConfig({ ...newConfig, timeout_seconds: parseInt(e.target.value) })}
                  inputProps={{ min: 5, max: 300 }}
                />
                
                <TextField
                  type="number"
                  label="Retry Attempts"
                  value={newConfig.retry_attempts}
                  onChange={(e) => setNewConfig({ ...newConfig, retry_attempts: parseInt(e.target.value) })}
                  inputProps={{ min: 0, max: 10 }}
                />
              </Box>
              
              <Box display="flex" alignItems="center" gap={2}>
                <Button
                  variant="outlined"
                  startIcon={<CheckCircle />}
                  disabled
                >
                  Test API (Coming Soon)
                </Button>
                
                <Alert severity="info" sx={{ flex: 1 }}>
                  API testing functionality will be available once backend endpoints are implemented
                </Alert>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateConfig} variant="contained">
            Preview Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
