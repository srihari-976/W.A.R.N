import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Grid, 
  Alert, Chip, LinearProgress, Container, Paper
} from '@mui/material';
import { Security, PlayArrow, Stop, Shield } from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const BruteForceDemo = () => {
  const [status, setStatus] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationLog, setSimulationLog] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/brute-force-status`);
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching brute force status:', error);
    }
  };

  const simulateAttack = async () => {
    setIsSimulating(true);
    setLoading(true);
    setSimulationLog([]);

    try {
      const addLog = (message, type = 'info') => {
        setSimulationLog(prev => [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          message,
          type
        }]);
      };

      addLog('🚨 Initiating brute force simulation', 'warning');
      addLog('Target: admin@192.168.1.100', 'info');
      
      for (let i = 1; i <= 3; i++) {
        addLog(`Attempt ${i}/3: Trying password "password${i}"`, 'info');
        
        try {
          await axios.post(`${API_BASE_URL}/login`, {
            username: 'admin',
            password: `wrong_password_${i}`,
            process: `ssh_client_${i}`
          });
        } catch (error) {
          if (error.response?.status === 429) {
            addLog('🛡️ Brute force detected! IP blocked', 'error');
            addLog('🔪 Suspicious processes terminated', 'error');
            break;
          } else {
            addLog(`❌ Login failed (${error.response?.data?.attempts_remaining || 0} attempts remaining)`, 'warning');
          }
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      await axios.post(`${API_BASE_URL}/auth/simulate-attack`, {
        ip: '192.168.1.100',
        username: 'admin'
      });

      addLog('✅ Simulation complete - Threat neutralized', 'success');
      await fetchStatus();
      
    } catch (error) {
      console.error('Simulation error:', error);
      setSimulationLog(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        message: '❌ Simulation failed',
        type: 'error'
      }]);
    } finally {
      setLoading(false);
      setIsSimulating(false);
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'success': return 'success';
      default: return 'info';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" color="primary" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center' }}>
          <Security sx={{ mr: 2 }} />
          Brute Force Protection Demo
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Automated threat response system demonstration
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Protection Status
              </Typography>
              
              {status ? (
                <Box>
                  <Box sx={{ mb: 2 }}>
                    <Chip label="Active" color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2" color="textSecondary" component="span">
                      Max attempts: {status.max_attempts} | Block duration: {status.block_duration}s
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                      Statistics:
                    </Typography>
                    <Typography variant="body2">Monitored IPs: {status.stats?.total_ips_monitored || 0}</Typography>
                    <Typography variant="body2">Blocked IPs: {status.stats?.blocked_ips || 0}</Typography>
                    <Typography variant="body2">Recent attempts: {status.stats?.recent_attempts || 0}</Typography>
                  </Box>

                  {Object.keys(status.blocked_ips || {}).length > 0 && (
                    <Box>
                      <Typography variant="body2" color="error" sx={{ mb: 1 }}>
                        Blocked IPs:
                      </Typography>
                      {Object.entries(status.blocked_ips).map(([ip, info]) => (
                        <Chip
                          key={ip}
                          label={`${ip} (${info.remaining_seconds}s)`}
                          color="error"
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              ) : (
                <LinearProgress />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Attack Simulation
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography color="textSecondary" sx={{ mb: 2 }}>
                  Simulate a brute force attack to demonstrate automated protection:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  <Chip label="3 failed login attempts" size="small" variant="outlined" />
                  <Chip label="IP blocking activation" size="small" variant="outlined" />
                  <Chip label="Process termination" size="small" variant="outlined" />
                </Box>
              </Box>

              <Button
                variant="contained"
                onClick={simulateAttack}
                disabled={isSimulating || loading}
                startIcon={isSimulating ? <Stop /> : <PlayArrow />}
                sx={{ mb: 2 }}
              >
                {isSimulating ? 'Simulating...' : 'Start Simulation'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
                Simulation Log
              </Typography>
              
              <Paper variant="outlined" sx={{ p: 2, height: 300, overflow: 'auto', backgroundColor: '#fafafa' }}>
                {simulationLog.length > 0 ? (
                  simulationLog.map((log, index) => (
                    <Alert
                      key={index}
                      severity={getLogColor(log.type)}
                      sx={{ mb: 1, fontSize: '0.9rem' }}
                    >
                      [{log.timestamp}] {log.message}
                    </Alert>
                  ))
                ) : (
                  <Typography color="textSecondary" sx={{ textAlign: 'center', mt: 10 }}>
                    Click "Start Simulation" to begin demonstration
                  </Typography>
                )}
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default BruteForceDemo;