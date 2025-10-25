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
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './useAuth';

function App() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={enterpriseTheme}>
        <CssBaseline />
        <LoginForm onLoginSuccess={() => window.location.reload()} />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={enterpriseTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/security" element={<ProtectedRoute><SecurityDashboard /></ProtectedRoute>} />
            <Route path="/brute-force-demo" element={<ProtectedRoute><BruteForceDemo /></ProtectedRoute>} />
            <Route path="/instagram-demo" element={<ProtectedRoute><InstagramDemo /></ProtectedRoute>} />
            <Route path="/threat-control" element={<ProtectedRoute><ThreatControl /></ProtectedRoute>} />
            <Route path="/live-demo" element={<ProtectedRoute><LiveSecurityDemo /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/login" element={<LoginForm onLoginSuccess={() => window.location.href = '/'} />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;