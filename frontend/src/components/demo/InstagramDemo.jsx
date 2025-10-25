import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Chip, LinearProgress } from '@mui/material';
import { Security, Block, Computer } from '@mui/icons-material';
import axios from 'axios';

const InstagramDemo = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [blocked, setBlocked] = useState(false);
  const [message, setMessage] = useState('');
  const [securityActions, setSecurityActions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleLogin = async () => {
    setIsProcessing(true);
    
    try {
      const response = await axios.post('http://localhost:5000/demo/instagram-login', {
        username,
        password,
        ip: '192.168.1.100'
      });
      
      setMessage('Login successful!');
    } catch (error) {
      const data = error.response?.data;
      const currentAttempts = data?.current_attempts || attempts + 1;
      
      setAttempts(currentAttempts);
      setBlocked(data?.blocked || false);
      setMessage(data?.message || 'Login failed');
      
      // Add security actions based on attempt count
      const newActions = [];
      
      if (currentAttempts === 1) {
        newActions.push({
          id: Date.now(),
          action: 'System Isolation',
          description: 'User session isolated for monitoring',
          icon: Security,
          color: 'warning'
        });
      } else if (currentAttempts === 2) {
        newActions.push({
          id: Date.now(),
          action: 'Password Reset Required',
          description: 'Account flagged for password change',
          icon: Security,
          color: 'error'
        });
      } else if (currentAttempts >= 3) {
        newActions.push(
          {
            id: Date.now(),
            action: 'IP Address Blocked',
            description: 'Source IP 192.168.1.100 blocked for 1 hour',
            icon: Block,
            color: 'error'
          },
          {
            id: Date.now() + 1,
            action: 'Browser Process Terminated',
            description: 'All browser processes killed (PID: 1234, 5678)',
            icon: Computer,
            color: 'error'
          }
        );
      }
      
      setSecurityActions(prev => [...newActions, ...prev]);
    } finally {
      setTimeout(() => setIsProcessing(false), 1500);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(45deg, #833ab4, #fd1d1d, #fcb045)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: 2,
      gap: 3
    }}>
      <Card sx={{ width: 400, boxShadow: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" align="center" sx={{ mb: 4, fontWeight: 700, color: '#262626' }}>
            Instagram
          </Typography>
          
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            sx={{ mb: 3 }}
            disabled={blocked}
          />
          
          <TextField
            fullWidth
            type="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ mb: 3 }}
            disabled={blocked}
          />
          
          <Button
            fullWidth
            variant="contained"
            onClick={handleLogin}
            disabled={blocked || isProcessing}
            sx={{ mb: 3, backgroundColor: '#0095f6', py: 1.5, fontWeight: 600, '&:hover': { backgroundColor: '#1877f2' } }}
          >
            {isProcessing ? 'Processing...' : 'Log In'}
          </Button>
          
          {isProcessing && <LinearProgress sx={{ mb: 2 }} />}
          
          {message && (
            <Alert 
              severity={blocked ? 'error' : attempts > 0 ? 'warning' : 'success'}
              sx={{ mb: 2 }}
            >
              {message}
            </Alert>
          )}
          
          {attempts > 0 && (
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2" color="error">
                Failed attempts: {attempts}/3
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Account will be locked after 3 failed attempts
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
      
      {/* Security Actions Panel */}
      {securityActions.length > 0 && (
        <Card sx={{ width: 400, boxShadow: 3, bgcolor: '#f5f5f5' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Security sx={{ mr: 1 }} />
              W.A.R.N Security Actions
            </Typography>
            
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {securityActions.map((action) => {
                const IconComponent = action.icon;
                return (
                  <Alert 
                    key={action.id}
                    severity={action.color === 'error' ? 'error' : 'warning'}
                    sx={{ mb: 1 }}
                    icon={<IconComponent />}
                  >
                    <Typography variant="subtitle2">
                      {action.action}
                    </Typography>
                    <Typography variant="body2">
                      {action.description}
                    </Typography>
                  </Alert>
                );
              })}
            </Box>
            
            <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
              <Typography variant="caption" color="textSecondary">
                💡 Demo Instructions: Use any username/password to trigger security responses.
                Each failed attempt demonstrates different protection levels.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default InstagramDemo;