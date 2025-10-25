import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Grid, Alert, Chip,
  Table, TableBody, TableCell, TableHead, TableRow, LinearProgress,
  Dialog, DialogTitle, DialogContent, TextField
} from '@mui/material';
import { Security, Block, Warning, Computer, NetworkCheck } from '@mui/icons-material';
import axios from 'axios';

const LiveSecurityDemo = () => {
  const [attacks, setAttacks] = useState([]);
  const [blockedIPs, setBlockedIPs] = useState([]);
  const [killedProcesses, setKilledProcesses] = useState([]);
  const [stats, setStats] = useState({ blocked: 0, isolated: 0, killed: 0 });
  const [demoUrl, setDemoUrl] = useState('');
  const [urlDialog, setUrlDialog] = useState(false);

  // Simulate real-time attacks for demo
  const simulateAttack = async (type) => {
    const attackTypes = {
      brute_force: {
        ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
        description: 'Multiple failed login attempts detected',
        action: 'IP Blocked + Process Killed',
        severity: 'high'
      },
      phishing: {
        ip: `10.0.0.${Math.floor(Math.random() * 255)}`,
        description: 'Phishing URL accessed',
        action: 'Browser Terminated + IP Isolated',
        severity: 'critical'
      },
      dos: {
        ip: `172.16.0.${Math.floor(Math.random() * 255)}`,
        description: 'DoS attack - High request rate',
        action: 'IP Blocked + Traffic Filtered',
        severity: 'high'
      },
      malware: {
        ip: `203.0.113.${Math.floor(Math.random() * 255)}`,
        description: 'Malicious file execution detected',
        action: 'Process Killed + System Isolated',
        severity: 'critical'
      }
    };

    const attack = attackTypes[type];
    const timestamp = new Date().toISOString();
    
    // Add attack to list
    const newAttack = {
      id: Date.now(),
      type: type.toUpperCase(),
      ...attack,
      timestamp,
      status: 'blocking'
    };
    
    setAttacks(prev => [newAttack, ...prev.slice(0, 9)]);
    
    // Simulate blocking process
    setTimeout(() => {
      setAttacks(prev => prev.map(a => 
        a.id === newAttack.id ? { ...a, status: 'blocked' } : a
      ));
      
      // Add to blocked IPs
      setBlockedIPs(prev => [{
        ip: attack.ip,
        reason: attack.description,
        timestamp,
        remaining: 3600
      }, ...prev.slice(0, 4)]);
      
      // Add killed process
      setKilledProcesses(prev => [{
        process: type === 'phishing' ? 'chrome.exe' : 
                type === 'brute_force' ? 'ssh.exe' : 'malware.exe',
        pid: Math.floor(Math.random() * 9999),
        timestamp,
        reason: attack.description
      }, ...prev.slice(0, 4)]);
      
      // Update stats
      setStats(prev => ({
        blocked: prev.blocked + 1,
        isolated: prev.isolated + (type === 'phishing' ? 1 : 0),
        killed: prev.killed + 1
      }));
    }, 2000);
  };

  // Real phishing scan
  const scanPhishingURL = async () => {
    if (!demoUrl) return;
    
    try {
      const response = await axios.post('http://localhost:5000/api/security/scan-url', {
        url: demoUrl
      });
      
      const result = response.data;
      const newAttack = {
        id: Date.now(),
        type: 'PHISHING SCAN',
        ip: 'Real Scan',
        description: `URL: ${demoUrl} - ${result.is_phishing ? 'THREAT DETECTED' : 'Safe'}`,
        action: result.is_phishing ? 'URL Blocked + Alert Generated' : 'No Action Required',
        severity: result.is_phishing ? 'critical' : 'low',
        timestamp: new Date().toISOString(),
        status: 'completed',
        scanResult: result
      };
      
      setAttacks(prev => [newAttack, ...prev.slice(0, 9)]);
      setUrlDialog(false);
      setDemoUrl('');
    } catch (error) {
      console.error('Scan error:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'blocking': return 'warning';
      case 'blocked': return 'error';
      case 'completed': return 'success';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" color="primary" sx={{ mb: 3, textAlign: 'center' }}>
        🛡️ W.A.R.N Live Security Demo
      </Typography>
      
      {/* Demo Controls */}
      <Card sx={{ mb: 3, bgcolor: '#f5f5f5' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Demo Attack Simulations</Typography>
          <Grid container spacing={2}>
            <Grid item>
              <Button 
                variant="contained" 
                color="error"
                onClick={() => simulateAttack('brute_force')}
              >
                Simulate Brute Force
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="contained" 
                color="warning"
                onClick={() => simulateAttack('phishing')}
              >
                Simulate Phishing
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="contained" 
                color="info"
                onClick={() => simulateAttack('dos')}
              >
                Simulate DoS Attack
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="contained" 
                color="secondary"
                onClick={() => simulateAttack('malware')}
              >
                Simulate Malware
              </Button>
            </Grid>
            <Grid item>
              <Button 
                variant="outlined"
                onClick={() => setUrlDialog(true)}
              >
                Real Phishing Scan
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#ffebee' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Block sx={{ fontSize: 40, color: 'error.main' }} />
              <Typography variant="h3" color="error">{stats.blocked}</Typography>
              <Typography>IPs Blocked</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#fff3e0' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <NetworkCheck sx={{ fontSize: 40, color: 'warning.main' }} />
              <Typography variant="h3" color="warning.main">{stats.isolated}</Typography>
              <Typography>Systems Isolated</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#e8f5e8' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Computer sx={{ fontSize: 40, color: 'success.main' }} />
              <Typography variant="h3" color="success.main">{stats.killed}</Typography>
              <Typography>Processes Terminated</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Live Attack Feed */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                🚨 Live Attack Detection & Response
              </Typography>
              <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                {attacks.map((attack) => (
                  <Alert 
                    key={attack.id}
                    severity={attack.severity === 'critical' ? 'error' : 'warning'}
                    sx={{ mb: 1 }}
                  >
                    <Box>
                      <Typography variant="subtitle2">
                        {attack.type} - {attack.ip}
                      </Typography>
                      <Typography variant="body2">
                        {attack.description}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Chip 
                          label={attack.status.toUpperCase()} 
                          color={getStatusColor(attack.status)}
                          size="small"
                        />
                        <Typography variant="caption" sx={{ ml: 1 }}>
                          Action: {attack.action}
                        </Typography>
                      </Box>
                      {attack.status === 'blocking' && (
                        <LinearProgress sx={{ mt: 1 }} />
                      )}
                      {attack.scanResult && (
                        <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
                          <Typography variant="caption">
                            Risk: {attack.scanResult.risk_level} | 
                            Confidence: {(attack.scanResult.confidence * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Alert>
                ))}
                {attacks.length === 0 && (
                  <Alert severity="success">
                    System Secure - No threats detected
                  </Alert>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Blocked IPs */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                🚫 Blocked IP Addresses
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Reason</TableCell>
                    <TableCell>Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {blockedIPs.map((ip, index) => (
                    <TableRow key={index}>
                      <TableCell>{ip.ip}</TableCell>
                      <TableCell>{ip.reason}</TableCell>
                      <TableCell>{new Date(ip.timestamp).toLocaleTimeString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {blockedIPs.length === 0 && (
                <Typography color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                  No IPs currently blocked
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Killed Processes */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                ⚡ Terminated Processes
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Process</TableCell>
                    <TableCell>PID</TableCell>
                    <TableCell>Reason</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {killedProcesses.map((proc, index) => (
                    <TableRow key={index}>
                      <TableCell>{proc.process}</TableCell>
                      <TableCell>{proc.pid}</TableCell>
                      <TableCell>{proc.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {killedProcesses.length === 0 && (
                <Typography color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
                  No processes terminated
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* URL Scan Dialog */}
      <Dialog open={urlDialog} onClose={() => setUrlDialog(false)}>
        <DialogTitle>Real Phishing URL Scanner</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Enter URL to scan"
            value={demoUrl}
            onChange={(e) => setDemoUrl(e.target.value)}
            placeholder="https://example.com"
            sx={{ mt: 1, mb: 2 }}
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button onClick={() => setDemoUrl('http://phishing-example.com/fake-bank')}>
              Test Phishing URL
            </Button>
            <Button onClick={() => setDemoUrl('https://google.com')}>
              Test Safe URL
            </Button>
          </Box>
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button variant="contained" onClick={scanPhishingURL}>
              Scan URL
            </Button>
            <Button onClick={() => setUrlDialog(false)}>
              Cancel
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default LiveSecurityDemo;