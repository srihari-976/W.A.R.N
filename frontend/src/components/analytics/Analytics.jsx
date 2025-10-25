import React from 'react';
import { Container, Typography, Box, Card, CardContent, Grid, Chip } from '@mui/material';
import { Assessment, TrendingUp, Security, Computer } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const Analytics = () => {
  const threatData = [
    { month: 'Jan', threats: 45, blocked: 43 },
    { month: 'Feb', threats: 52, blocked: 50 },
    { month: 'Mar', threats: 38, blocked: 36 },
    { month: 'Apr', threats: 61, blocked: 59 },
    { month: 'May', threats: 73, blocked: 71 },
    { month: 'Jun', threats: 29, blocked: 28 }
  ];

  const performanceData = [
    { time: '00:00', cpu: 45, memory: 62, network: 23 },
    { time: '04:00', cpu: 52, memory: 58, network: 31 },
    { time: '08:00', cpu: 78, memory: 71, network: 45 },
    { time: '12:00', cpu: 85, memory: 79, network: 52 },
    { time: '16:00', cpu: 72, memory: 68, network: 38 },
    { time: '20:00', cpu: 58, memory: 55, network: 29 }
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
          Security Analytics
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Comprehensive security metrics and performance analysis
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">Detection Rate</Typography>
                  <Typography variant="h4" color="success.main" sx={{ fontWeight: 600 }}>
                    98.7%
                  </Typography>
                  <Typography variant="caption" color="success.main">+2.1% this month</Typography>
                </Box>
                <Security sx={{ fontSize: 48, color: 'success.main', opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">Response Time</Typography>
                  <Typography variant="h4" color="info.main" sx={{ fontWeight: 600 }}>
                    1.2s
                  </Typography>
                  <Typography variant="caption" color="info.main">Average response</Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 48, color: 'info.main', opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">False Positives</Typography>
                  <Typography variant="h4" color="warning.main" sx={{ fontWeight: 600 }}>
                    0.3%
                  </Typography>
                  <Typography variant="caption" color="warning.main">Industry leading</Typography>
                </Box>
                <Assessment sx={{ fontSize: 48, color: 'warning.main', opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">Uptime</Typography>
                  <Typography variant="h4" color="success.main" sx={{ fontWeight: 600 }}>
                    99.9%
                  </Typography>
                  <Typography variant="caption" color="success.main">30-day average</Typography>
                </Box>
                <Computer sx={{ fontSize: 48, color: 'success.main', opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Threat Detection Trends
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={threatData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="month" stroke="#666" style={{ fontSize: '14px' }} />
                  <YAxis stroke="#666" />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                    }}
                  />
                  <Bar dataKey="threats" fill="#f57c00" name="Threats Detected" />
                  <Bar dataKey="blocked" fill="#388e3c" name="Threats Blocked" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                System Performance
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={performanceData}>
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
                  <Line type="monotone" dataKey="cpu" stroke="#1976d2" strokeWidth={2} name="CPU %" />
                  <Line type="monotone" dataKey="memory" stroke="#d32f2f" strokeWidth={2} name="Memory %" />
                  <Line type="monotone" dataKey="network" stroke="#388e3c" strokeWidth={2} name="Network %" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Security Insights
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                <Chip label="MITRE ATT&CK Coverage: 95%" color="success" />
                <Chip label="ML Model Accuracy: 98.7%" color="primary" />
                <Chip label="Zero-Day Detection: Active" color="info" />
                <Chip label="Behavioral Analysis: Enabled" color="warning" />
              </Box>
              <Typography color="textSecondary">
                The W.A.R.N system demonstrates exceptional performance with industry-leading detection rates 
                and minimal false positives. Our AI-powered threat detection continues to evolve and adapt 
                to emerging security challenges.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Analytics;