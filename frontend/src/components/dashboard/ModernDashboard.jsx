import React, { useEffect, useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Security,
  Warning,
  TrendingUp,
  Computer,
  Shield,
  BugReport,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const ModernDashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [riskScore, setRiskScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    activeThreats: 0,
    eventsPerHour: 0,
    modelAccuracy: 88.3,
    systemHealth: 'Operational'
  });

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [alertsRes, healthRes, threatsRes] = await Promise.all([
        axios.get('http://localhost:5000/api/alerts/'),
        axios.get('http://localhost:5000/health'),
        axios.get('http://localhost:5000/demo/threats')
      ]);
      
      setAlerts(alertsRes.data.alerts || []);
      setStats(prev => ({
        ...prev,
        activeThreats: threatsRes.data.threats?.length || 0,
        eventsPerHour: alertsRes.data.alerts?.length || 0,
        modelAccuracy: healthRes.data.accuracy ? parseFloat(healthRes.data.accuracy) : 88.3
      }));
      
      // Calculate risk score from threats and alerts
      const threatsCount = threatsRes.data.threats?.length || 0;
      const alertsRisk = alertsRes.data.alerts?.length > 0 
        ? alertsRes.data.alerts.reduce((sum, alert) => sum + (alert.risk_score || 0), 0) / alertsRes.data.alerts.length
        : 0;
      const combinedRisk = threatsCount > 0 ? Math.max(alertsRisk, threatsCount * 25) : alertsRisk;
      setRiskScore(Math.round(combinedRisk));
      setLoading(false);
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      setLoading(false);
    }
  };

  const MetricCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" color={color}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Icon sx={{ fontSize: 40, color: `${color}.main`, opacity: 0.7 }} />
        </Box>
      </CardContent>
    </Card>
  );

  // Generate threat data from real alerts
  const threatData = alerts.length > 0 
    ? alerts.slice(0, 6).map((alert, index) => ({
        time: `${index * 4}:00`,
        threats: alert.risk_score || 0
      }))
    : [];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Security sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
        W.A.R.N Security Operations Center
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Active Threats"
            value={stats.activeThreats}
            icon={Warning}
            color="error"
            subtitle="Real-time detection"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Risk Score"
            value={`${riskScore}%`}
            icon={Shield}
            color="warning"
            subtitle="Current system risk"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Events/Hour"
            value={stats.eventsPerHour.toLocaleString()}
            icon={Computer}
            color="info"
            subtitle="Processing rate"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard
            title="Model Accuracy"
            value={`${stats.modelAccuracy}%`}
            icon={BugReport}
            color="success"
            subtitle="Llama 3.2 3B MITRE"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Threat Detection Timeline
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={threatData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="threats" 
                    stroke="#1976d2" 
                    strokeWidth={3}
                    dot={{ fill: '#1976d2', strokeWidth: 2, r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                {alerts.length > 0 ? (
                  alerts.slice(0, 5).map((alert, index) => (
                    <Alert 
                      key={index} 
                      severity={alert.threat_level === 'high' ? 'error' : 'warning'}
                      sx={{ mb: 1 }}
                    >
                      <Typography variant="body2">
                        {alert.analysis || 'Threat detected'}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {alert.techniques && JSON.parse(alert.techniques).map((tech, i) => (
                          <Chip 
                            key={i} 
                            label={tech} 
                            size="small" 
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    </Alert>
                  ))
                ) : (
                  <Typography color="textSecondary">
                    No recent alerts
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>

          <Card elevation={3} sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  ML Model Status
                </Typography>
                <Chip 
                  label="Llama 3.2 Active" 
                  color="success" 
                  icon={<Security />}
                  sx={{ mt: 1 }}
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Detection Pipeline
                </Typography>
                <Chip 
                  label="Running" 
                  color="success" 
                  sx={{ mt: 1 }}
                />
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Windows Agent
                </Typography>
                <Chip 
                  label="Connected" 
                  color="success" 
                  sx={{ mt: 1 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ModernDashboard;