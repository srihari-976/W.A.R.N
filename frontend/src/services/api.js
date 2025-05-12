import axiosInstance from '../utils/axiosInstance';

// Endpoint/Asset Services
export const assetService = {
  getAll: () => axiosInstance.get('/api/assets'),
  getById: (id) => axiosInstance.get(`/api/assets/${id}`),
  update: (id, data) => axiosInstance.put(`/api/assets/${id}`, data),
  delete: (id) => axiosInstance.delete(`/api/assets/${id}`),
  getRiskAssessment: (id) => axiosInstance.get(`/api/assets/${id}/risk-assessment`),
  getActivityLog: (id) => axiosInstance.get(`/api/assets/${id}/activity-log`),
};

// Alert Services
export const alertService = {
  getAll: () => axiosInstance.get('/api/alerts'),
  getById: (id) => axiosInstance.get(`/api/alerts/${id}`),
  updateStatus: (id, status) => axiosInstance.put(`/api/alerts/${id}/status`, { status }),
  getByAssetId: (assetId) => axiosInstance.get(`/api/alerts/asset/${assetId}`),
};

// Security Test Services
export const securityTestService = {
  runTest: (assetId, testType) => axiosInstance.post(`/api/security-test/${assetId}`, { testType }),
  getTestResults: (assetId) => axiosInstance.get(`/api/security-test/${assetId}/results`),
  getTestHistory: (assetId) => axiosInstance.get(`/api/security-test/${assetId}/history`),
};

// Dashboard Services
export const dashboardService = {
  getMetrics: () => axiosInstance.get('/api/dashboard/metrics'),
  getRecentAlerts: () => axiosInstance.get('/api/dashboard/recent-alerts'),
  getAssetStatus: () => axiosInstance.get('/api/dashboard/asset-status'),
  getActivityFeed: () => axiosInstance.get('/api/dashboard/activity-feed'),
};

// Risk Assessment Services
export const riskService = {
  getRiskLevel: (assetId) => axiosInstance.get(`/api/risk/${assetId}/level`),
  getRiskFactors: (assetId) => axiosInstance.get(`/api/risk/${assetId}/factors`),
  updateRiskMitigation: (assetId, data) => axiosInstance.put(`/api/risk/${assetId}/mitigation`, data),
  getRiskHistory: (assetId) => axiosInstance.get(`/api/risk/${assetId}/history`),
}; 