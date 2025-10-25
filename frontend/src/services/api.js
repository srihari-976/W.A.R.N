import axiosInstance from '../utils/axiosInstance';

// Auth Services
export const authService = {
  login: (credentials) => axiosInstance.post('/api/auth/login', credentials),
  register: (userData) => axiosInstance.post('/api/auth/register', userData),
  refresh: (refreshToken) => axiosInstance.post('/api/auth/refresh', { refresh_token: refreshToken }),
  logout: () => axiosInstance.post('/api/auth/logout'),
  getCurrentUser: () => axiosInstance.get('/api/auth/me'),
};

// Security Services
export const securityService = {
  scanURL: (url) => axiosInstance.post('/api/security/scan-url', { url }),
  getBlockedIPs: () => axiosInstance.get('/api/security/blocked-ips'),
  unblockIP: (ip) => axiosInstance.post('/api/security/unblock-ip', { ip_address: ip }),
  getLockedAccounts: () => axiosInstance.get('/api/security/locked-accounts'),
  unlockAccount: (username) => axiosInstance.post('/api/security/unlock-account', { username }),
  killProcesses: (processName) => axiosInstance.post('/api/security/kill-processes', { process_name: processName }),
};

// Alert Services
export const alertService = {
  getAll: () => axiosInstance.get('/api/alerts/'),
  getById: (id) => axiosInstance.get(`/api/alerts/${id}`),
  updateStatus: (id, status) => axiosInstance.put(`/api/alerts/${id}/status`, { status }),
};

// Risk Services
export const riskService = {
  getScores: () => axiosInstance.get('/api/risk/scores'),
  getFactors: () => axiosInstance.get('/api/risk/factors'),
};

// Dashboard Services
export const dashboardService = {
  getMetrics: () => axiosInstance.get('/api/dashboard/metrics'),
  getRecentAlerts: () => axiosInstance.get('/api/dashboard/recent-alerts'),
  getAssetStatus: () => axiosInstance.get('/api/dashboard/asset-status'),
};

// Convenience exports
export const scanURL = (url) => securityService.scanURL(url);
export const checkIPStatus = () => securityService.getBlockedIPs();
export const unblockIP = (ip) => securityService.unblockIP(ip);
export const unlockAccount = (username) => securityService.unlockAccount(username); 