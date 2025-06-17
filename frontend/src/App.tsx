import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './components/Dashboard';
import EnhancedJobs from './components/EnhancedJobs';
import JobDetails from './components/JobDetails';
import Businesses from './components/Businesses';
import ApiExport from './components/ApiExport';
import ApiDocs from './components/ApiDocs';
import Layout from './components/Layout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/enhanced-jobs" element={<EnhancedJobs />} />
            <Route path="/jobs/:jobId" element={<JobDetails />} />
            <Route path="/businesses" element={<Businesses />} />
            <Route path="/api-export" element={<ApiExport />} />
            <Route path="/api-docs" element={<ApiDocs />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
