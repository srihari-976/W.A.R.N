import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import SecurityCard from '../common/SecurityCard';
import StatusIndicator from '../common/StatusIndicator';

const API_BASE_URL = 'http://localhost:5001';

const EndpointList = () => {
  const navigate = useNavigate();
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const fetchEndpoints = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`${API_BASE_URL}/api/status`);
        const trackingData = response.data.tracking || {};
        
        // Convert tracking data to endpoint format
        const endpointList = Object.entries(trackingData).map(([ip, data]) => ({
          id: ip,
          hostname: data.username || 'Unknown',
          ip_address: ip,
          status: data.count >= 5 ? 'isolated' : 'active',
          os_type: 'Unknown',
          agent_version: '1.0.0',
          last_seen: data.attempts[data.attempts.length - 1] || new Date().toISOString()
        }));
        
        setEndpoints(endpointList);
      } catch (error) {
        console.error('Error fetching endpoints:', error);
        setError('Failed to load endpoints. Please check server connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchEndpoints();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchEndpoints, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredEndpoints = endpoints.filter(endpoint => {
    const matchesSearch = endpoint.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         endpoint.ip_address.includes(searchTerm);
    const matchesStatus = statusFilter === 'all' || endpoint.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neon-blue"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-500 text-xl">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-neon-blue animate-pulse-neon">
          Endpoints
        </h2>
        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="Search endpoints..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="cyber-input"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="cyber-select"
            aria-label="Filter by status"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
            <option value="isolated">Isolated</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEndpoints.map(endpoint => (
          <SecurityCard
            key={endpoint.id}
            title={endpoint.hostname}
            severity={endpoint.status === 'active' ? 'low' : 'high'}
          >
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <StatusIndicator
                  status={endpoint.status === 'active' ? 'healthy' : 'warning'}
                  pulse={endpoint.status === 'active'}
                />
                <span className="text-sm text-neon-blue/60">
                  Last seen: {new Date(endpoint.last_seen).toLocaleString()}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">IP Address</span>
                  <span className="text-neon-blue">{endpoint.ip_address}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">OS Type</span>
                  <span className="text-neon-blue">{endpoint.os_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">Agent Version</span>
                  <span className="text-neon-blue">{endpoint.agent_version}</span>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => navigate(`/endpoints/${endpoint.id}`)}
                  className="cyber-button-blue flex-1"
                >
                  View Details
                </button>
                <button
                  onClick={() => navigate(`/endpoints/${endpoint.id}`)}
                  className="cyber-button-purple flex-1"
                >
                  Manage
                </button>
              </div>
            </div>
          </SecurityCard>
        ))}
      </div>
    </div>
  );
};

export default EndpointList; 