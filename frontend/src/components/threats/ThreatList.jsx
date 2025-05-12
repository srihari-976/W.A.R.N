import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SecurityCard from '../common/SecurityCard';
import StatusIndicator from '../common/StatusIndicator';

const API_BASE_URL = 'http://localhost:5001';

const ThreatList = ({ onLogActivity }) => {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const fetchThreats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`${API_BASE_URL}/api/threats`);
        setThreats(response.data.threats || []);
      } catch (error) {
        console.error('Error fetching threats:', error);
        setError('Failed to load threats. Please check server connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchThreats();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchThreats, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredThreats = threats.filter(threat => {
    const matchesSeverity = severityFilter === 'all' || threat.risk_level === severityFilter;
    const matchesStatus = statusFilter === 'all' || threat.status === statusFilter;
    return matchesSeverity && matchesStatus;
  });

  const handleStatusUpdate = async (threatId, newStatus) => {
    try {
      // Update local state immediately for better UX
      setThreats(threats.map(threat =>
        threat.id === threatId ? { ...threat, status: newStatus } : threat
      ));

      // Log the activity
      if (onLogActivity) {
        onLogActivity({
          type: 'threat',
          event_type: 'Status Update',
          description: `Threat status updated to ${newStatus}`,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      console.error('Error updating threat status:', error);
    }
  };

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
          Threats
        </h2>
        <div className="flex space-x-4">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="cyber-select"
            aria-label="Filter by severity"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="cyber-select"
            aria-label="Filter by status"
          >
            <option value="all">All Status</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="false_positive">False Positive</option>
          </select>
        </div>
      </div>

      {filteredThreats.length === 0 ? (
        <div className="text-neon-blue/60 text-center py-8">
          No threats detected.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredThreats.map(threat => (
            <div key={threat.id} className="p-4 rounded bg-cyber-gray/50 border border-neon-pink/40 flex flex-col gap-2 relative">
              <div className="flex items-center justify-between">
                <span className="font-bold text-neon-pink">{threat.type}</span>
                <span className="text-neon-blue/60 text-sm">{new Date(threat.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-2 text-neon-blue/80">{threat.details?.description || 'No description available'}</p>
              <div className="flex gap-2 mt-2">
                <button 
                  className="px-2 py-1 rounded text-xs bg-green-500/30 text-green-400 hover:bg-green-500/50" 
                  onClick={() => handleStatusUpdate(threat.id, 'investigating')}
                  disabled={threat.status === 'investigating'}
                >
                  Investigate
                </button>
                <button 
                  className="px-2 py-1 rounded text-xs bg-yellow-500/30 text-yellow-300 hover:bg-yellow-500/50" 
                  onClick={() => handleStatusUpdate(threat.id, 'resolved')}
                  disabled={threat.status === 'resolved'}
                >
                  Resolve
                </button>
              </div>
              {threat.status && (
                <span className="absolute top-2 right-2 text-xs text-neon-blue">
                  {threat.status.charAt(0).toUpperCase() + threat.status.slice(1)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThreatList; 