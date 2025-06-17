import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  PlayArrow as TryIcon,
  Api as ApiIcon,
} from '@mui/icons-material';

// Simple code block component
const CodeBlock = ({ children, language }: { children: string; language?: string }) => (
  <Box
    component="pre"
    sx={{
      backgroundColor: '#1e1e1e',
      color: '#d4d4d4',
      padding: 2,
      borderRadius: 1,
      overflow: 'auto',
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
      fontSize: '0.875rem',
      margin: 0,
      whiteSpace: 'pre-wrap'
    }}
  >
    <code>{children}</code>
  </Box>
);

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
      id={`api-tabpanel-${index}`}
      aria-labelledby={`api-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const API_BASE_URL = window.location.origin;

export default function ApiDocs() {
  const [value, setValue] = useState(0);
  const [tryEndpointOpen, setTryEndpointOpen] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState<any>(null);
  const [testResult, setTestResult] = useState<string>('');
  const [testLoading, setTestLoading] = useState(false);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const testEndpoint = async () => {
    if (!selectedEndpoint) return;
    
    setTestLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}${selectedEndpoint.path}`);
      const data = await response.json();
      setTestResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setTestResult(`Error: ${error}`);
    } finally {
      setTestLoading(false);
    }
  };

  const endpoints = [
    {
      name: 'Get All Businesses (File Data)',
      path: '/api/file/businesses',
      method: 'GET',
      description: 'Retrieve a paginated list of all businesses with optional filtering from file-based data (100K+ records)',
      parameters: [
        { name: 'page', type: 'integer', required: false, default: '1', description: 'Page number for pagination' },
        { name: 'limit', type: 'integer', required: false, default: '50', description: 'Number of items per page (max 1000)' },
        { name: 'domain', type: 'string', required: false, default: '', description: 'Filter by domain name' },
        { name: 'city', type: 'string', required: false, default: '', description: 'Filter by city name' },
        { name: 'category', type: 'string', required: false, default: '', description: 'Filter by category' },
        { name: 'search', type: 'string', required: false, default: '', description: 'Search in business name, description, category' },
        { name: 'sort_by', type: 'string', required: false, default: 'name', description: 'Sort by field (name, city, domain, category, scraped_at)' },
        { name: 'sort_order', type: 'string', required: false, default: 'asc', description: 'Sort order (asc, desc)' },
      ],
      example: {
        request: `curl -X GET "${API_BASE_URL}/api/file/businesses?page=1&limit=10&domain=yello.ae&sort_by=name"`,
        response: `{
  "businesses": [
    {
      "id": "biz_001234",
      "name": "ABC Company",
      "description": "Leading provider of services",
      "phone": "+971-4-123-4567",
      "email": "info@abccompany.com",
      "website": "https://abccompany.com",
      "address": "Dubai, UAE",
      "city": "Dubai",
      "domain": "yello.ae",
      "category": "Business Services",
      "scraped_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 20054,
  "page": 1,
  "limit": 10,
  "total_pages": 2006,
  "has_next": true,
  "has_prev": false,
  "filters_applied": {
    "domain": "yello.ae",
    "city": null,
    "category": null,
    "search": null,
    "sort_by": "name",
    "sort_order": "asc"
  }
}`
      }
    },
    {
      name: 'Get Business Statistics (File Data)',
      path: '/api/file/stats',
      method: 'GET',
      description: 'Get comprehensive statistics about the file-based business database',
      parameters: [],
      example: {
        request: `curl -X GET "${API_BASE_URL}/api/file/stats"`,
        response: `{
  "total_businesses": 100000,
  "total_domains": 5,
  "total_cities": 25,
  "total_categories": 15,
  "businesses_by_domain": {
    "yello.ae": 20054,
    "surinamyp.com": 19885,
    "businesslist.co.ke": 19966,
    "businesslist.com.ng": 20225,
    "brazilyello.com": 19870
  },
  "top_cities": {
    "Dubai": 4104,
    "São Paulo": 4060,
    "Lagos": 4037
  },
  "top_categories": {
    "Consulting": 6799,
    "Retail": 6796,
    "Media": 6753
  },
  "data_source": "file-based",
  "last_updated": "2024-01-15T10:30:00Z"
}`
      }
    },
    {
      name: 'Get Domains (File Data)',
      path: '/api/file/domains',
      method: 'GET',
      description: 'Get a list of all available domains with business counts from file data',
      parameters: [],
      example: {
        request: `curl -X GET "${API_BASE_URL}/api/file/domains"`,
        response: `{
  "domains": [
    {
      "domain": "yello.ae",
      "business_count": 20054,
      "last_scraped": "2024-01-15T08:30:00Z"
    },
    {
      "domain": "surinamyp.com",
      "business_count": 19885,
      "last_scraped": "2024-01-14T15:20:00Z"
    }
  ]
}`
      }
    },
    {
      name: 'Get Cities (File Data)',
      path: '/api/file/cities',
      method: 'GET',
      description: 'Get a list of all cities with business counts, optionally filtered by domain',
      parameters: [
        { name: 'domain', type: 'string', required: false, default: '', description: 'Filter cities by domain' },
      ],
      example: {
        request: `curl -X GET "${API_BASE_URL}/api/file/cities?domain=yello.ae"`,
        response: `{
  "cities": [
    {
      "city": "Dubai",
      "domain": "yello.ae",
      "business_count": 4104
    },
    {
      "city": "Abu Dhabi",
      "domain": "yello.ae",
      "business_count": 3250
    }
  ]
}`
      }
    },
    {
      name: 'Get Categories (File Data)',
      path: '/api/file/categories',
      method: 'GET',
      description: 'Get a list of all business categories with counts, optionally filtered by domain',
      parameters: [
        { name: 'domain', type: 'string', required: false, default: '', description: 'Filter categories by domain' },
      ],
      example: {
        request: `curl -X GET "${API_BASE_URL}/api/file/categories?domain=yello.ae"`,
        response: `{
  "categories": [
    {
      "category": "Business Services",
      "business_count": 2150
    },
    {
      "category": "Technology",
      "business_count": 1890
    }
  ]
}`
      }
    }
  ];

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        <ApiIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        API Documentation
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Public API Access:</strong> These endpoints are publicly accessible and don't require authentication. 
        Rate limiting is applied to ensure fair usage.
      </Alert>

      <Tabs value={value} onChange={handleChange} aria-label="api documentation tabs">
        <Tab label="Endpoints" />
        <Tab label="Code Examples" />
        <Tab label="Data Schema" />
      </Tabs>

      <Box sx={{ p: 3 }}>
        {value === 0 && (
          <>
            <Typography variant="h6" gutterBottom>Available Endpoints</Typography>
            {endpoints.map((endpoint, index) => (
              <Accordion key={index} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip 
                      label={endpoint.method} 
                      color="primary" 
                      size="small"
                      sx={{ minWidth: '60px' }}
                    />
                    <Typography variant="subtitle1">{endpoint.name}</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <Box>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {endpoint.description}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <Typography variant="body2">
                          <strong>{endpoint.method}</strong> {endpoint.path}
                        </Typography>
                        <IconButton 
                          size="small" 
                          onClick={() => copyToClipboard(`${API_BASE_URL}${endpoint.path}`)}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>

                    {endpoint.parameters.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>Parameters</Typography>
                        <TableContainer component={Paper} variant="outlined">
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Required</TableCell>
                                <TableCell>Default</TableCell>
                                <TableCell>Description</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {endpoint.parameters.map((param, paramIndex) => (
                                <TableRow key={paramIndex}>
                                  <TableCell><code>{param.name}</code></TableCell>
                                  <TableCell>{param.type}</TableCell>
                                  <TableCell>{param.required ? 'Yes' : 'No'}</TableCell>
                                  <TableCell>{param.default || '-'}</TableCell>
                                  <TableCell>{param.description}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}

                    <Box>
                      <Typography variant="subtitle2" gutterBottom>Example Request</Typography>
                      <CodeBlock language="bash">
                        {endpoint.example.request}
                      </CodeBlock>
                    </Box>

                    <Box>
                      <Typography variant="subtitle2" gutterBottom>Example Response</Typography>
                      <CodeBlock language="json">
                        {endpoint.example.response}
                      </CodeBlock>
                    </Box>

                    <Box>
                      <Button
                        variant="outlined"
                        startIcon={<TryIcon />}
                        onClick={() => {
                          setSelectedEndpoint(endpoint);
                          setTryEndpointOpen(true);
                        }}
                      >
                        Try This Endpoint
                      </Button>
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {value === 1 && (
          <>
            <Typography variant="h6" gutterBottom>Code Examples</Typography>
            <Alert severity="success" sx={{ mb: 2 }}>
              Copy and paste these examples into your favorite programming environment.
            </Alert>
          </>
        )}

        {value === 2 && (
          <>
            <Typography variant="h6" gutterBottom>Data Schema</Typography>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Business Object</Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  The main business data structure returned by the API
                </Typography>
                
                <CodeBlock language="json">
{`{
  "id": "string",              // Unique business identifier
  "name": "string",            // Business name
  "description": "string",     // Business description
  "phone": "string",           // Phone number
  "email": "string",           // Email address
  "website": "string",         // Website URL
  "address": "string",         // Full address
  "city": "string",            // City name
  "domain": "string",          // Source domain
  "category": "string",        // Business category
  "scraped_at": "datetime"     // ISO 8601 timestamp
}`}
                </CodeBlock>
              </CardContent>
            </Card>
          </>
        )}
      </Box>

      {/* Try Endpoint Dialog */}
      <Dialog 
        open={tryEndpointOpen} 
        onClose={() => setTryEndpointOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Try Endpoint: {selectedEndpoint?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {selectedEndpoint?.method} {selectedEndpoint?.path}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {selectedEndpoint?.description}
            </Typography>
          </Box>
          
          <Button
            variant="contained"
            onClick={testEndpoint}
            disabled={testLoading}
            sx={{ mb: 2 }}
          >
            {testLoading ? 'Testing...' : 'Send Request'}
          </Button>
          
          {testResult && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>Response:</Typography>
              <CodeBlock language="json">
                {testResult}
              </CodeBlock>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTryEndpointOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}