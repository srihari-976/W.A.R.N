import React from 'react';
import { Box, AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { Security, Dashboard, Shield, Computer, Assessment } from '@mui/icons-material';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: Dashboard },
    { label: 'Threat Control', path: '/threat-control', icon: Shield },
    { label: 'Live Demo', path: '/live-demo', icon: Security },
    { label: 'Instagram Demo', path: '/instagram-demo', icon: Computer },
    { label: 'Analytics', path: '/analytics', icon: Assessment }
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Navigation Bar */}
      <AppBar 
        position="static" 
        sx={{ 
          background: 'linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
          boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <Security sx={{ mr: 2, color: '#64b5f6' }} />
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 600,
                color: '#ffffff',
                letterSpacing: '0.5px'
              }}
            >
              W.A.R.N Security Platform
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  startIcon={<Icon />}
                  sx={{
                    color: isActive ? '#64b5f6' : '#b0bec5',
                    backgroundColor: isActive ? 'rgba(100,181,246,0.1)' : 'transparent',
                    border: isActive ? '1px solid rgba(100,181,246,0.3)' : '1px solid transparent',
                    borderRadius: 1,
                    px: 2,
                    py: 1,
                    textTransform: 'none',
                    fontWeight: isActive ? 600 : 400,
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      backgroundColor: 'rgba(100,181,246,0.1)',
                      color: '#64b5f6'
                    }
                  }}
                >
                  {item.label}
                </Button>
              );
            })}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, backgroundColor: '#f5f7fa', minHeight: 'calc(100vh - 64px - 60px)' }}>
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>

      {/* Footer */}
      <Box 
        sx={{ 
          backgroundColor: '#1a1a2e',
          color: '#b0bec5',
          py: 2,
          borderTop: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2">
              © 2025 W.A.R.N Security Platform. All rights reserved.
            </Typography>
            <Typography variant="body2">
              Version 2.0.0 | Powered by Llama 3.2 MITRE ATT&CK
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;