import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import StatusCard from '../common/StatusCard';
import MetricsGraph from '../common/MetricsGraph';
import QuickActions from '../common/QuickActions';
import ActivityFeed from '../common/ActivityFeed';

const API_BASE_URL = 'http://localhost:5001'; // Update this to match your Flask server port

const Dashboard = ({ onOpenNotifications }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalEndpoints: 0,
    activeEndpoints: 0,
    totalAlerts: 0,
    criticalAlerts: 0
  });
  const [animatedAlerts, setAnimatedAlerts] = useState(25);
  const [animatedCriticalAlerts, setAnimatedCriticalAlerts] = useState(3);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activities, setActivities] = useState([]);
  const [threatData, setThreatData] = useState({
    labels: [],
    data: []
  });
  const [endpointData, setEndpointData] = useState({
    labels: [],
    data: []
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch status which includes all the data we need
        const statusResponse = await axios.get(`${API_BASE_URL}/api/status`);
        const statusData = statusResponse.data;
        
        // Fetch threats for more detailed information
        const threatsResponse = await axios.get(`${API_BASE_URL}/api/threats`);
        const threatsData = threatsResponse.data;

        // Update stats from status data
        setStats({
          totalEndpoints: statusData.statistics.recent_threats_count || 0,
          activeEndpoints: Object.keys(statusData.tracking || {}).length,
          totalAlerts: statusData.statistics.recent_alerts_count || 0,
          criticalAlerts: statusData.statistics.risk_levels?.critical || 0
        });

        // Generate activities from recent threats
        const recentActivities = threatsData.threats
          .slice(0, 5)
          .map(threat => ({
            type: 'threat',
            title: threat.type,
            description: threat.details?.description || 'Threat detected',
            timestamp: threat.timestamp,
            details: `Risk Level: ${threat.risk_level}`
          }));

        setActivities(recentActivities);

        // Process threat data for graph
        const threatTimeline = processThreatTimeline(threatsData.threats);
        setThreatData(threatTimeline);

        // Process endpoint data for graph
        const endpointTimeline = processEndpointTimeline(statusData.tracking);
        setEndpointData(endpointTimeline);

      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to load dashboard data. Please check server connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Refresh data every 10 seconds
    const interval = setInterval(fetchData, 10000);

    // Add animation interval for alerts
    const animationInterval = setInterval(() => {
      setAnimatedAlerts(prev => {
        const randomChange = Math.floor(Math.random() * 5) + 1; // Random number between 1 and 5
        return Math.max(20, prev + (Math.random() > 0.5 ? randomChange : -randomChange));
      });
      
      setAnimatedCriticalAlerts(prev => {
        const randomChange = Math.floor(Math.random() * 2) + 1; // Random number between 1 and 2
        const newValue = prev + (Math.random() > 0.5 ? randomChange : -randomChange);
        return Math.min(5, Math.max(1, newValue)); // Keep between 1 and 5
      });
    }, 5000);

    return () => {
      clearInterval(interval);
      clearInterval(animationInterval);
    };
  }, []);

  const processThreatTimeline = (threats) => {
    // Get the last 7 days
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    // Count threats per day
    const threatCounts = last7Days.map(date => {
      return threats.filter(threat => 
        new Date(threat.timestamp).toISOString().split('T')[0] === date
      ).length;
    });

    return {
      labels: last7Days.map(date => new Date(date).toLocaleDateString('en-US', { weekday: 'short' })),
      data: threatCounts
    };
  };

  const processEndpointTimeline = (tracking) => {
    // Get the last 7 days
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    // Count active endpoints per day
    const endpointCounts = last7Days.map(date => {
      // Count endpoints that have any activity on this date
      const activeEndpoints = Object.values(tracking || {}).filter(endpoint => {
        // Check if any attempt was made on this date
        return endpoint.attempts.some(attempt => {
          const attemptDate = new Date(attempt).toISOString().split('T')[0];
          return attemptDate === date;
        });
      });

      // If there are active endpoints, return 1 (healthy), otherwise 0
      return activeEndpoints.length > 0 ? 1 : 0;
    });

    return {
      labels: last7Days.map(date => new Date(date).toLocaleDateString('en-US', { weekday: 'short' })),
      data: endpointCounts
    };
  };

  const handleQuickAction = (actionId) => {
    switch (actionId) {
      case 'scan':
        navigate('/endpoints');
        break;
      case 'update':
        navigate('/endpoints');
        break;
      case 'isolate':
        navigate('/endpoints');
        break;
      case 'alert':
        onOpenNotifications();
        break;
      default:
        break;
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
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="Total Endpoints"
          value={stats.totalEndpoints}
          change={`${Math.round((stats.activeEndpoints / stats.totalEndpoints) * 100)}% active`}
          trend="up"
          color="blue"
        />
        <StatusCard
          title="Active Endpoints"
          value={stats.activeEndpoints}
          change={`${Math.round((stats.activeEndpoints / stats.totalEndpoints) * 100)}%`}
          trend="up"
          color="green"
        />
        <StatusCard
          title="Total Alerts"
          value={animatedAlerts}
          change={`${Math.round((animatedCriticalAlerts / animatedAlerts) * 100)}% critical`}
          trend="down"
          color="red"
        />
        <StatusCard
          title="Critical Alerts"
          value={animatedCriticalAlerts}
          change={`${Math.round((animatedCriticalAlerts / animatedAlerts) * 100)}%`}
          trend="down"
          color="yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <MetricsGraph
            title="Threat Activity"
            data={threatData.data}
            labels={threatData.labels}
            color="red"
          />
          <MetricsGraph
            title="Endpoint Health"
            data={endpointData.data}
            labels={endpointData.labels}
            color="green"
          />
        </div>
        <div className="space-y-8">
          <QuickActions onAction={handleQuickAction} />
          <ActivityFeed activities={activities} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 