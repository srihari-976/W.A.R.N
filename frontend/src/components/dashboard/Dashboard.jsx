import React, { useEffect, useState, useCallback } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Chip, LinearProgress, Alert, Container, Paper
} from '@mui/material';
import { Security, Warning, Computer, Shield, Visibility, NetworkCheck, Block, TrendingUp } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../utils/axiosInstance.jsx';
import { alertService } from '../../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [riskScores, setRiskScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    activeThreats: 0,
    avgRiskScore: 0,
    eventsProcessed: 0,
    modelAccuracy: 88.3
  });

  const fetchRealData = useCallback(async () => {
    try {
      const [alertsRes, riskRes, healthRes, threatsRes] = await Promise.all([
        axiosInstance.get('/api/alerts/'),
        axiosInstance.get('/api/risk/scores'),
        axiosInstance.get('/health'),
        axiosInstance.get('/demo/threats')
      ]);
      
      const alertsData = alertsRes.data.alerts || [];
      const riskData = riskRes.data.risk_scores || [];
      const threatsData = threatsRes.data.threats || [];
      
      setAlerts(alertsData);
      setRiskScores(riskData);
      
      // Use threats data for active threats count
      setStats({
        activeThreats: threatsData.length,
        avgRiskScore: riskRes.data.average_score || 0,
        eventsProcessed: alertsData.length,
        modelAccuracy: 88.3
      });
      
      setError(null);
    } catch (err) {
      console.error('API Error:', err);
      setError('Failed to connect to W.A.R.N backend');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleResolveAlert = async (id) => {
    try {
      await alertService.updateStatus(id, 'resolved');
      fetchRealData();
    } catch (e) {
      console.error('Failed to update alert status', e);
    }
  };

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 5000);
    return () => clearInterval(interval);
  }, [fetchRealData]);



  const MetricCard = ({ title, value, icon: Icon, color, subtitle, trend }) => (
    <Card elevation={2}>
      <CardContent sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" variant="body2" sx={{ mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="h4" color={color} sx={{ fontWeight: 600, mb: 0.5 }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  {trend}
                </Typography>
              </Box>
            )}
          </Box>
          <Icon sx={{ fontSize: 48, color: `${color}.main`, opacity: 0.8 }} />
        </Box>
      </CardContent>
    </Card>
  );

  const chartData = riskScores.length > 0 
    ? riskScores.slice(0, 10).map((score, index) => ({
        time: `${index * 2}:00`,
        risk: score.score
      }))
    : [];

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" alignItems="center" sx={{ mt: 8 }}>
          <Typography variant="h5" color="primary" sx={{ mb: 3 }}>
            Loading W.A.R.N Security Platform...
          </Typography>
          <LinearProgress sx={{ width: '300px' }} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mt: 4 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
          Security Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Real-time threat monitoring and risk assessment powered by AI
        </Typography>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Active Threats"
            value={stats.activeThreats}
            icon={Warning}
            color="error"
            subtitle="Live Detection"
            trend={stats.activeThreats > 0 ? "High Alert" : "Secure"}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Risk Score"
            value={`${Math.round(stats.avgRiskScore)}%`}
            icon={Shield}
            color="warning"
            subtitle="Current Assessment"
            trend="+2.3% from yesterday"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Events Processed"
            value={stats.eventsProcessed.toLocaleString()}
            icon={Computer}
            color="info"
            subtitle="Total Analyzed"
            trend="+15% this week"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Model Accuracy"
            value={`${stats.modelAccuracy}%`}
            icon={Visibility}
            color="success"
            subtitle="Llama 3.2 MITRE"
            trend="Optimal Performance"
          />
        </Grid>
      </Grid>

      {/* Security Features */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                  <Block sx={{ mr: 1 }} />
                  Brute Force Protection
                </Typography>
                <Chip label="Active" color="success" />
              </Box>
              <Typography color="textSecondary" sx={{ mb: 2 }}>
                Automated system monitors login attempts and terminates suspicious processes after 3 failed attempts.
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label="Max Attempts: 3" size="small" color="warning" variant="outlined" />
                <Chip label="Auto Process Kill" size="small" color="error" variant="outlined" />
                <Chip label="IP Blocking" size="small" color="info" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Alerts */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" color="primary" sx={{ mb: 3 }}>
                Risk Score Timeline
              </Typography>
              <ResponsiveContainer width="100%" height={450}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1976d2" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#1976d2" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="time" stroke="#666" style={{ fontSize: '14px' }} />
                  <YAxis stroke="#666" />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="risk" 
                    stroke="#1976d2" 
                    strokeWidth={2}
                    fill="url(#riskGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Recent Alerts
              </Typography>
              <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
                {alerts.length > 0 ? (
                  alerts.slice(0, 5).map((alert, index) => (
                    <Alert 
                      key={index}
                      severity={alert.threat_level === 'high' ? 'error' : 'warning'}
                      sx={{ mb: 1, display: 'flex', flexDirection: 'column' }}
                      action={
                        alert.status !== 'resolved' ? (
                          <Chip
                            label="Mark Resolved"
                            color="success"
                            onClick={() => handleResolveAlert(alert.id)}
                            size="small"
                            variant="outlined"
                          />
                        ) : (
                          <Chip label="Resolved" color="success" size="small" />
                        )
                      }
                    >
                      <Typography variant="body2">
                        Risk: {alert.risk_score}% - {alert.analysis || 'Threat detected'}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {alert.techniques && (() => {
                          try {
                            const list = typeof alert.techniques === 'string' ? JSON.parse(alert.techniques) : alert.techniques;
                            return (list || []).map((tech, i) => (
                              <Chip 
                                key={i} 
                                label={tech} 
                                size="small" 
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }} 
                              />
                            ));
                          } catch {
                            return null;
                          }
                        })()}
                      </Box>
                    </Alert>
                  ))
                ) : (
                  <Alert severity="success">
                    System secure - No active threats detected
                  </Alert>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip 
                label="Instagram Demo" 
                clickable
                onClick={() => navigate('/instagram-demo')}
                color="secondary"
                variant="outlined"
              />
              <Chip 
                label="Threat Control" 
                clickable
                onClick={() => navigate('/threat-control')}
                color="primary"
                variant="outlined"
              />
              <Chip 
                label="Brute Force Demo" 
                clickable
                onClick={() => navigate('/brute-force-demo')}
                color="warning"
                variant="outlined"
              />
              <Chip 
                label="Live Security Demo" 
                clickable
                onClick={() => navigate('/live-demo')}
                color="error"
                variant="outlined"
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;