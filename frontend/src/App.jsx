import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { enterpriseTheme } from './theme/enterpriseTheme';
import Layout from './components/layout/Layout';
import Dashboard from './components/dashboard/Dashboard';
import SecurityDashboard from './components/security/SecurityDashboard';
import BruteForceDemo from './components/security/BruteForceDemo';
import InstagramDemo from './components/demo/InstagramDemo';
import ThreatControl from './components/demo/ThreatControl';
import LiveSecurityDemo from './components/demo/LiveSecurityDemo';
import Analytics from './components/analytics/Analytics';
import LoginForm from './components/LoginForm';

function App() {
  return (
    <ThemeProvider theme={enterpriseTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/security" element={<SecurityDashboard />} />
            <Route path="/brute-force-demo" element={<BruteForceDemo />} />
            <Route path="/instagram-demo" element={<InstagramDemo />} />
            <Route path="/threat-control" element={<ThreatControl />} />
            <Route path="/live-demo" element={<LiveSecurityDemo />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/login" element={<LoginForm onLoginSuccess={() => window.location.href = '/'} />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
