import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Stack,
} from '@mui/material';
import {
  TrendingUp,
  Business,
  Schedule,
  Domain,
} from '@mui/icons-material';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { scrapingAPI, businessAPI } from '../api';
import { DashboardStats, ScrapingJob, BusinessStats } from '../types';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

function StatCard({ title, value, icon, color = 'primary' }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="overline">
              {title}
            </Typography>
            <Typography variant="h4" component="h2">
              {value}
            </Typography>
          </Box>
          <Box color={`${color}.main`} display="flex">
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<BusinessStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<ScrapingJob[]>([]);
  const [businessStats, setBusinessStats] = useState<any>(null);
  const [cityData, setCityData] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        jobsResponse,
        businessStatsResponse,
        citiesResponse,
      ] = await Promise.all([
        scrapingAPI.listJobs(0, 5),
        businessAPI.getBusinessStats(),
        businessAPI.getCitiesWithCounts({ min_businesses: 1 }),
      ]);

      // Use business stats as main stats
      setStats(businessStatsResponse.data);
      setRecentJobs(jobsResponse.data);
      setBusinessStats(businessStatsResponse.data);
      
      // Transform cities data for charts
      const cities = citiesResponse.data?.cities || [];
      setCityData(cities.slice(0, 10));
      
      // For now, we don't have category data, so set empty array
      setCategoryData([]);
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
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

  const cityChartData = {
    labels: cityData.map(item => item.city),
    datasets: [
      {
        data: cityData.map(item => item.business_count),
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40',
          '#FF6384',
          '#C9CBCF',
          '#4BC0C0',
          '#FF6384',
        ],
      },
    ],
  };

  const categoryChartData = {
    labels: categoryData.map(item => item.category),
    datasets: [
      {
        label: 'Businesses',
        data: categoryData.map(item => item.count),
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        borderColor: 'rgba(53, 162, 235, 1)',
        borderWidth: 1,
      },
    ],
  };

  if (loading && !stats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Stats Cards */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' },
          gap: 3,
          mb: 3 
        }}
      >
        <StatCard
          title="Total Businesses"
          value={stats?.total_businesses?.toLocaleString() || 0}
          icon={<Business fontSize="large" />}
          color="primary"
        />
        <StatCard
          title="Cities"
          value={stats?.unique_cities || 0}
          icon={<TrendingUp fontSize="large" />}
          color="success"
        />
        <StatCard
          title="Countries"
          value={stats?.unique_countries || 0}
          icon={<Business fontSize="large" />}
          color="info"
        />
        <StatCard
          title="Domains"
          value={stats?.unique_domains || 0}
          icon={<Domain fontSize="large" />}
          color="warning"
        />
      </Box>

      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          gap: 3 
        }}
      >
        {/* Recent Jobs */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Scraping Jobs
            </Typography>
            {recentJobs.length === 0 ? (
              <Typography color="textSecondary">No jobs found</Typography>
            ) : (
              recentJobs.map((job) => (
                <Box key={job._id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="subtitle1">{job.name}</Typography>
                    <Chip 
                      label={job.status || 'pending'} 
                      color={getStatusColor(job.status) as any}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    Progress: {job.businesses_scraped} / {job.total_businesses} businesses
                  </Typography>
                  {job.current_city && (
                    <Typography variant="body2" color="textSecondary">
                      Current: {job.current_city} (Page {job.current_page})
                    </Typography>
                  )}
                </Box>
              ))
            )}
          </CardContent>
        </Card>

        {/* Businesses by City Chart */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Cities
            </Typography>
            {cityData.length > 0 ? (
              <Box height={300}>
                <Doughnut 
                  data={cityChartData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom' as const,
                      },
                    },
                  }}
                />
              </Box>
            ) : (
              <Typography color="textSecondary">No data available</Typography>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Businesses by Category Chart - Full Width */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Top Categories
          </Typography>
          {categoryData.length > 0 ? (
            <Box height={300}>
              <Bar 
                data={categoryChartData}
                    options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false,
                    },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                    },
                  },
                }}
              />
            </Box>
          ) : (
            <Typography color="textSecondary">No data available</Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
