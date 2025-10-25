import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Grid, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, IconButton, Menu, MenuItem, Alert, Paper, Container
} from '@mui/material';
import { MoreVert, Security, Block, Delete, Lock, TrendingUp } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const ThreatControl = () => {
  const [threats, setThreats] = useState([]);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedThreat, setSelectedThreat] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [threatsRes, statsRes, eventsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/demo/threats`),
        axios.get(`${API_BASE_URL}/demo/stats`),
        axios.get(`${API_BASE_URL}/demo/security-events`)
      ]);
      
      setThreats(threatsRes.data.threats || []);
      setLogs(eventsRes.data.events || []);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleAction = async (threatId, action) => {
    try {
      if (threatId.startsWith('user_')) {
        // Handle user-based threats
        const username = threatId.replace('user_', '');
        if (action === 'unblock_user') {
          await axios.post(`${API_BASE_URL}/demo/manual-action`, { 
            action: 'unblock_user', 
            username: username 
          });
        }
      } else {
        // Handle IP-based threats
        const ip = threatId.replace('threat_', '');
        
        if (action === 'unblock') {
          await axios.post(`${API_BASE_URL}/demo/manual-action`, { 
            action: 'unblock_ip', 
            ip: ip 
          });
        } else if (action === 'quarantine') {
          await axios.post(`${API_BASE_URL}/demo/manual-action`, { 
            action: 'quarantine_system', 
            ip: ip 
          });
        } else if (action === 'unblock_user') {
          const threat = threats.find(t => t.id === threatId);
          await axios.post(`${API_BASE_URL}/demo/manual-action`, { 
            action: 'unblock_user', 
            username: threat?.username 
          });
        } else {
          await axios.post(`${API_BASE_URL}/demo/threats/${threatId}/action`, { action });
        }
      }
      fetchData();
      setAnchorEl(null);
    } catch (error) {
      console.error('Error performing action:', error);
    }
  };

  const handleMenuClick = (event, threat) => {
    setAnchorEl(event.currentTarget);
    setSelectedThreat(threat);
  };

  return (
    <Container maxWidth="lg">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
          Threat Control Center
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Monitor and manage security threats in real-time
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="textSecondary" variant="body2">Active Threats</Typography>
              <Typography variant="h3" color="error" sx={{ fontWeight: 600 }}>
                {stats.current_threats || 0}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp sx={{ fontSize: 16, color: 'error.main', mr: 0.5 }} />
                <Typography variant="caption" color="error">High Priority</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="textSecondary" variant="body2">Total Attempts</Typography>
              <Typography variant="h3" color="warning.main" sx={{ fontWeight: 600 }}>
                {stats.total_attempts || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">Login attempts blocked</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="textSecondary" variant="body2">Processes Killed</Typography>
              <Typography variant="h3" color="info.main" sx={{ fontWeight: 600 }}>
                {stats.processes_killed || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">Malicious processes terminated</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="textSecondary" variant="body2">System Status</Typography>
              <Typography variant="h5" color="success.main" sx={{ fontWeight: 600 }}>
                Secure
              </Typography>
              <Typography variant="caption" color="success.main">All systems operational</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Threats Graph */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Threat Timeline (24H)
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={stats.hourly_threats || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="hour" stroke="#666" style={{ fontSize: '14px' }} />
                  <YAxis stroke="#666" />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                    }}
                  />
                  <Line type="monotone" dataKey="threats" stroke="#d32f2f" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Live Logs */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Activity Log
              </Typography>
              <Box sx={{ height: 400, overflow: 'auto' }}>
                {logs.map((log, index) => {
                  const severity = log.severity === 'critical' ? 'error' : 
                                 log.severity === 'high' ? 'warning' : 'info';
                  return (
                    <Alert 
                      key={index} 
                      severity={severity}
                      sx={{ mb: 1, fontSize: '0.8rem' }}
                    >
                      <Typography variant="caption">
                        [{new Date(log.timestamp).toLocaleTimeString()}] 
                        {log.ip || 'System'} - {log.action || log.type}
                      </Typography>
                      {log.security_actions && (
                        <Box sx={{ mt: 0.5 }}>
                          {log.security_actions.map((action, i) => (
                            <Typography key={i} variant="caption" display="block" sx={{ ml: 1 }}>
                              • {action}
                            </Typography>
                          ))}
                        </Box>
                      )}
                      {log.description && (
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          {log.description}
                        </Typography>
                      )}
                    </Alert>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Threat Management Table */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Active Threats Management
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>IP Address</TableCell>
                      <TableCell>Username</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Time Remaining</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {threats.map((threat) => (
                      <TableRow key={threat.id}>
                        <TableCell>{threat.ip}</TableCell>
                        <TableCell>{threat.username}</TableCell>
                        <TableCell>
                          <Chip 
                            label={threat.status === 'quarantined' ? 'Quarantined' : 
                                   threat.status === 'ip_blocked' ? 'IP Blocked' : 'Blocked'} 
                            color={threat.status === 'quarantined' ? 'warning' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={threat.severity} 
                            color={threat.severity === 'high' ? 'error' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {Math.floor(threat.remaining_time / 60)}m {threat.remaining_time % 60}s
                        </TableCell>
                        <TableCell>
                          <IconButton 
                            onClick={(e) => handleMenuClick(e, threat)}
                            size="small"
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              {threats.length === 0 && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  No active threats - System secure
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => handleAction(selectedThreat?.id, 'quarantine')}>
          <Lock sx={{ mr: 1 }} /> Quarantine System
        </MenuItem>
        <MenuItem onClick={() => handleAction(selectedThreat?.id, 'unblock')}>
          <Security sx={{ mr: 1 }} /> Unblock IP
        </MenuItem>
        <MenuItem onClick={() => handleAction(selectedThreat?.id, 'unblock_user')}>
          <Security sx={{ mr: 1 }} /> Unblock User
        </MenuItem>
        <MenuItem onClick={() => handleAction(selectedThreat?.id, 'terminate')}>
          <Delete sx={{ mr: 1 }} /> Terminate Processes
        </MenuItem>
      </Menu>
    </Container>
  );
};

export default ThreatControl;