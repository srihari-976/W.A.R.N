import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Chip,
  Button, TextField, Dialog, DialogTitle, DialogContent,
  List, ListItem, ListItemText, IconButton, Alert
} from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import BlockIcon from '@mui/icons-material/Block';
import WarningIcon from '@mui/icons-material/Warning';
import LinkIcon from '@mui/icons-material/Link';
import LockIcon from '@mui/icons-material/Lock';
import DeleteIcon from '@mui/icons-material/Delete';
import { securityService } from '../../services/api';

const SecurityDashboard = () => {
  const [urlToScan, setUrlToScan] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [blockedIPs, setBlockedIPs] = useState([]);
  const [lockedAccounts, setLockedAccounts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load blocked IPs and locked accounts
  const loadSecurityData = async () => {
    try {
      const [ipsRes, accountsRes] = await Promise.all([
        securityService.getBlockedIPs(),
        securityService.getLockedAccounts()
      ]);
      
      setBlockedIPs(ipsRes.data.blocked_ips || []);
      setLockedAccounts(accountsRes.data.locked_accounts || []);
    } catch (error) {
      console.error('Error loading security data:', error);
    }
  };

  useEffect(() => {
    loadSecurityData();
    const interval = setInterval(loadSecurityData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // URL Phishing Scanner
  const handleScanURL = async () => {
    if (!urlToScan) return;
    
    setLoading(true);
    try {
      const response = await securityService.scanURL(urlToScan);
      setScanResult(response.data);
    } catch (error) {
      console.error('Error scanning URL:', error);
      setScanResult({
        error: 'Failed to scan URL',
        is_phishing: false
      });
    } finally {
      setLoading(false);
    }
  };

  // Manual IP Unblock
  const handleUnblockIP = async (ip) => {
    try {
      await securityService.unblockIP(ip);
      loadSecurityData();
    } catch (error) {
      console.error('Error unblocking IP:', error);
    }
  };

  // Manual Account Unlock
  const handleUnlockAccount = async (username) => {
    try {
      await securityService.unlockAccount(username);
      loadSecurityData();
    } catch (error) {
      console.error('Error unlocking account:', error);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <SecurityIcon sx={{ mr: 2 }} />
        W.A.R.N Security Dashboard
      </Typography>
      
      {/* URL Phishing Scanner */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <LinkIcon sx={{ mr: 1 }} />
            Phishing URL Scanner
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              placeholder="Enter URL to scan (e.g., https://example.com)"
              value={urlToScan}
              onChange={(e) => setUrlToScan(e.target.value)}
            />
            <Button 
              variant="contained" 
              onClick={handleScanURL}
              disabled={loading}
            >
              {loading ? 'Scanning...' : 'Scan URL'}
            </Button>
          </Box>
          
          {scanResult && (
            <Card 
              variant="outlined" 
              sx={{ 
                p: 2, 
                bgcolor: scanResult.is_phishing ? '#fee' : '#efe',
                border: `2px solid ${scanResult.is_phishing ? '#f44336' : '#4caf50'}`
              }}
            >
              <Typography variant="h6">
                {scanResult.is_phishing ? '⚠️ PHISHING DETECTED' : '✅ URL is Safe'}
              </Typography>
              <Typography>Risk Level: 
                <Chip 
                  label={scanResult.risk_level} 
                  color={getRiskColor(scanResult.risk_level)}
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Typography>
              <Typography>Confidence: {(scanResult.confidence * 100).toFixed(1)}%</Typography>
              
              {scanResult.threat_indicators && scanResult.threat_indicators.length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2 }}>Threat Indicators:</Typography>
                  <List dense>
                    {scanResult.threat_indicators.map((indicator, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={indicator} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </Card>
          )}
        </CardContent>
      </Card>
      
      {/* Blocked IPs and Locked Accounts Management */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <BlockIcon sx={{ mr: 1 }} />
                Blocked IP Addresses ({blockedIPs.length})
              </Typography>
              
              {blockedIPs.length === 0 ? (
                <Alert severity="success">No IPs currently blocked</Alert>
              ) : (
                <List>
                  {blockedIPs.map((ip, index) => (
                    <ListItem 
                      key={index}
                      secondaryAction={
                        <IconButton 
                          onClick={() => handleUnblockIP(ip.address)}
                          color="primary"
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText 
                        primary={ip.address}
                        secondary={`Blocked: ${ip.reason} - ${ip.attempts} attempts`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <LockIcon sx={{ mr: 1 }} />
                Locked Accounts ({lockedAccounts.length})
              </Typography>
              
              {lockedAccounts.length === 0 ? (
                <Alert severity="success">No accounts currently locked</Alert>
              ) : (
                <List>
                  {lockedAccounts.map((account, index) => (
                    <ListItem 
                      key={index}
                      secondaryAction={
                        <Button 
                          onClick={() => handleUnlockAccount(account.username)}
                          color="primary"
                          size="small"
                        >
                          Unlock
                        </Button>
                      }
                    >
                      <ListItemText 
                        primary={account.username}
                        secondary={`Locked: ${account.reason}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Demo Actions */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Security Demos
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button 
              variant="outlined" 
              color="warning"
              onClick={() => window.open('/instagram_login.html', '_blank')}
            >
              Instagram Login Demo
            </Button>
            <Button 
              variant="outlined" 
              color="error"
              onClick={() => setUrlToScan('http://phishing-example.com/fake-bank-login')}
            >
              Test Phishing URL
            </Button>
            <Button 
              variant="outlined" 
              color="info"
              onClick={() => setUrlToScan('https://google.com')}
            >
              Test Safe URL
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SecurityDashboard;