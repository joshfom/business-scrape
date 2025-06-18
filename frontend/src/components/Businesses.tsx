import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  Chip,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Download,
  Search,
  Visibility,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { businessAPI } from '../api';
import { Business } from '../types';

export default function Businesses() {
  const [searchParams] = useSearchParams();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    search: '',
    domain: '',
    city: '',
    category: '',
    job_id: searchParams.get('job_id') || '',
  });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [selectedBusiness, setSelectedBusiness] = useState<Business | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [uniqueValues, setUniqueValues] = useState({
    domains: [] as string[],
    cities: [] as string[],
    categories: [] as string[],
  });

  const ITEMS_PER_PAGE = 50;

  useEffect(() => {
    fetchBusinesses();
    fetchUniqueValues();
  }, [page, filters]);

  const fetchBusinesses = async () => {
    try {
      setError(null);
      const params = {
        page: page,
        limit: ITEMS_PER_PAGE,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, value]) => value !== '')
        ),
      };
      
      const response = await businessAPI.listBusinesses(params);
      
      // The API should return a structured response with data and pagination
      const apiResponse = response.data as any;
      
      if (apiResponse && typeof apiResponse === 'object' && apiResponse.data) {
        // New API format with pagination
        setBusinesses(apiResponse.data || []);
        setTotalPages(apiResponse.pagination?.total_pages || 1);
      } else if (Array.isArray(apiResponse)) {
        // Fallback to old format
        setBusinesses(apiResponse);
        setTotalPages(Math.ceil(apiResponse.length / ITEMS_PER_PAGE));
      } else {
        setBusinesses([]);
        setTotalPages(1);
      }
    } catch (err) {
      setError('Failed to fetch businesses');
      console.error('Businesses error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUniqueValues = async () => {
    try {
      // Get domains
      const domainsResponse = await businessAPI.getDomains();
      const domains = domainsResponse.data?.domains || [];
      
      // Get cities
      const citiesResponse = await businessAPI.getCitiesWithCounts();
      const cities = citiesResponse.data?.cities?.map((c: any) => c.city) || [];
      
      // For categories, we'll need to extract them from business data or use a simpler approach
      // For now, we'll leave categories empty as there's no dedicated endpoint
      setUniqueValues({
        domains: domains,
        cities: cities.slice(0, 100), // Limit to first 100 cities for performance
        categories: [], // Will be populated from business data if needed
      });
    } catch (err) {
      console.error('Error fetching unique values:', err);
      // Set empty arrays to prevent map errors
      setUniqueValues({
        domains: [],
        cities: [],
        categories: [],
      });
    }
  };

  const handleExport = async () => {
    try {
      const exportParams = Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== '')
      );
      
      const response = await businessAPI.exportBusinesses(exportParams);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'businesses_export.json');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export businesses');
      console.error('Export error:', err);
    }
  };

  const handleViewDetails = (business: Business) => {
    console.log('Viewing business details:', business); // Debug log
    setSelectedBusiness(business);
    setDetailsOpen(true);
  };

  const handleFilterChange = (filterName: string, value: string) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
    setPage(1); // Reset to first page when filtering
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Businesses</Typography>
        <Button 
          variant="contained" 
          startIcon={<Download />} 
          onClick={handleExport}
        >
          Export Data
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Filters</Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              label="Search"
              variant="outlined"
              size="small"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ minWidth: 200 }}
            />

            {filters.job_id && (
              <TextField
                label="Job ID"
                variant="outlined"
                size="small"
                value={filters.job_id}
                onChange={(e) => handleFilterChange('job_id', e.target.value)}
                sx={{ minWidth: 200 }}
                helperText="Showing data for specific job"
              />
            )}
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Domain</InputLabel>
              <Select
                value={filters.domain}
                onChange={(e) => handleFilterChange('domain', e.target.value)}
                label="Domain"
              >
                <MenuItem value="">All Domains</MenuItem>
                {uniqueValues.domains.map((domain) => (
                  <MenuItem key={domain} value={domain}>
                    {domain.includes('://') ? new URL(domain).hostname : domain}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>City</InputLabel>
              <Select
                value={filters.city}
                onChange={(e) => handleFilterChange('city', e.target.value)}
                label="City"
              >
                <MenuItem value="">All Cities</MenuItem>
                {uniqueValues.cities.slice(0, 50).map((city) => (
                  <MenuItem key={city} value={city}>{city}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                label="Category"
              >
                <MenuItem value="">All Categories</MenuItem>
                {uniqueValues.categories.slice(0, 50).map((category) => (
                  <MenuItem key={category} value={category}>{category}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Results ({businesses.length} businesses)
          </Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Business Name</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Contact</TableCell>
                  <TableCell>Rating</TableCell>
                  <TableCell>Domain</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {businesses.map((business) => (
                  <TableRow key={business._id}>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">{business.name}</Typography>
                        {business.description && (
                          <Typography variant="caption" color="textSecondary">
                            {business.description.substring(0, 100)}...
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={business.category} size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{business.city}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {business.country}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box>
                        {business.phone && (
                          <Typography variant="caption" display="block">
                            📞 {business.phone}
                          </Typography>
                        )}
                        {business.website && (
                          <Link 
                            href={business.website} 
                            target="_blank" 
                            rel="noopener"
                            variant="caption"
                          >
                            🌐 Website
                          </Link>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {business.rating ? (
                        <Box>
                          <Typography variant="body2">⭐ {business.rating}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            ({business.reviews_count} reviews)
                          </Typography>
                        </Box>
                      ) : (
                        <Typography variant="caption" color="textSecondary">
                          No rating
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {business.domain?.includes('://') ? new URL(business.domain).hostname : business.domain}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => handleViewDetails(business)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {businesses.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="textSecondary">
                        No businesses found. Try adjusting your filters.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={2}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Business Details Dialog */}
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <BusinessIcon />
            {selectedBusiness?.name || 'Business Details'}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedBusiness ? (
            <Box sx={{ pt: 1 }}>
              <Typography variant="h6" gutterBottom>Contact Information</Typography>
              <Box mb={2}>
                {selectedBusiness.address && (
                  <Typography><strong>Address:</strong> {selectedBusiness.address}</Typography>
                )}
                {selectedBusiness.phone && (
                  <Typography><strong>Phone:</strong> {selectedBusiness.phone}</Typography>
                )}
                {selectedBusiness.mobile && (
                  <Typography><strong>Mobile:</strong> {selectedBusiness.mobile}</Typography>
                )}
                {selectedBusiness.fax && (
                  <Typography><strong>Fax:</strong> {selectedBusiness.fax}</Typography>
                )}
                {selectedBusiness.website && (
                  <Typography>
                    <strong>Website:</strong>{' '}
                    <Link href={selectedBusiness.website} target="_blank" rel="noopener">
                      {selectedBusiness.website}
                    </Link>
                  </Typography>
                )}
              </Box>

              {selectedBusiness.working_hours && Object.keys(selectedBusiness.working_hours).length > 0 && (
                <Box mb={2}>
                  <Typography variant="h6" gutterBottom>Working Hours</Typography>
                  {Object.entries(selectedBusiness.working_hours).map(([day, hours]) => (
                    <Typography key={day}><strong>{day}:</strong> {hours}</Typography>
                  ))}
                </Box>
              )}

              {selectedBusiness.description && (
                <Box mb={2}>
                  <Typography variant="h6" gutterBottom>Description</Typography>
                  <Typography>{selectedBusiness.description}</Typography>
                </Box>
              )}

              {selectedBusiness.tags && selectedBusiness.tags.length > 0 && (
                <Box mb={2}>
                  <Typography variant="h6" gutterBottom>Tags</Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {selectedBusiness.tags.map((tag, index) => (
                      <Chip key={`${tag}-${index}`} label={tag} size="small" />
                    ))}
                  </Box>
                </Box>
              )}

              <Box mb={2}>
                <Typography variant="h6" gutterBottom>Business Information</Typography>
                <Typography><strong>Category:</strong> {selectedBusiness.category}</Typography>
                <Typography><strong>Location:</strong> {selectedBusiness.city}, {selectedBusiness.country}</Typography>
                {selectedBusiness.established_year && (
                  <Typography><strong>Established:</strong> {selectedBusiness.established_year}</Typography>
                )}
                {selectedBusiness.employees && (
                  <Typography><strong>Employees:</strong> {selectedBusiness.employees}</Typography>
                )}
                {selectedBusiness.rating && (
                  <Typography><strong>Rating:</strong> {selectedBusiness.rating}/5 ({selectedBusiness.reviews_count || 0} reviews)</Typography>
                )}
              </Box>

              <Box mb={2}>
                <Typography variant="h6" gutterBottom>Source Information</Typography>
                <Typography>
                  <strong>Source:</strong>{' '}
                  <Link href={selectedBusiness.page_url} target="_blank" rel="noopener">
                    {selectedBusiness.domain?.includes('://') ? new URL(selectedBusiness.domain).hostname : selectedBusiness.domain}
                  </Link>
                </Typography>
                <Typography><strong>Scraped:</strong> {new Date(selectedBusiness.scraped_at).toLocaleString()}</Typography>
                {selectedBusiness.exported_at && (
                  <Typography><strong>Exported:</strong> {new Date(selectedBusiness.exported_at).toLocaleString()}</Typography>
                )}
              </Box>

              {selectedBusiness.coordinates && (
                <Box mb={2}>
                  <Typography variant="h6" gutterBottom>Location Coordinates</Typography>
                  <Typography><strong>Latitude:</strong> {selectedBusiness.coordinates.lat}</Typography>
                  <Typography><strong>Longitude:</strong> {selectedBusiness.coordinates.lng}</Typography>
                </Box>
              )}
            </Box>
          ) : (
            <Box sx={{ pt: 1 }}>
              <Typography>No business data available</Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
