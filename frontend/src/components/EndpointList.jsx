import React, { useEffect, useState } from 'react';
import websocketService from '../services/websocket';

const EndpointList = ({ alerts }) => {
  const [endpoints, setEndpoints] = useState([]);
  const [activeProcesses, setActiveProcesses] = useState(new Map());

  useEffect(() => {
    // Handle process events
    websocketService.on('process_event', (data) => {
      setActiveProcesses(prev => {
        const newProcesses = new Map(prev);
        
        if (data.type === 'process_started') {
          newProcesses.set(data.process.pid, {
            name: data.process.name,
            startTime: data.process.timestamp,
            status: 'running'
          });
        } else if (data.type === 'process_terminated') {
          newProcesses.delete(data.process.pid);
        }
        
        return newProcesses;
      });
    });

    // Handle system events that might affect endpoints
    websocketService.on('system_event', (data) => {
      if (data.type === 'modified' && data.path.includes('network')) {
        // Update endpoint status based on network changes
        setEndpoints(prev => {
          return prev.map(endpoint => {
            if (endpoint.path === data.path) {
              return { ...endpoint, lastActivity: data.timestamp };
            }
            return endpoint;
          });
        });
      }
    });

    // Cleanup
    return () => {
      websocketService.off('process_event');
      websocketService.off('system_event');
    };
  }, []);

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-blue-500';
    }
  };

  return (
    <div className="endpoint-list">
      {alerts.length === 0 ? (
        <div className="no-alerts">No active alerts</div>
      ) : (
        alerts.map((alert, index) => (
          <div key={index} className={`alert-item ${alert.severity}`}>
            <div className="alert-header">
              <span className="alert-title">{alert.title}</span>
              <span className="alert-severity">{alert.severity}</span>
            </div>
            <div className="alert-details">
              <p>{alert.description}</p>
              <div className="alert-meta">
                <span>Time: {new Date(alert.timestamp).toLocaleString()}</span>
                {alert.threat_id && (
                  <span>Threat ID: {alert.threat_id}</span>
                )}
              </div>
            </div>
          </div>
        ))
      )}

      <style jsx>{`
        .endpoint-list {
          max-height: 500px;
          overflow-y: auto;
        }

        .no-alerts {
          text-align: center;
          padding: 20px;
          color: #666;
        }

        .alert-item {
          margin-bottom: 10px;
          padding: 15px;
          border-radius: 4px;
          background: #fff;
          border-left: 4px solid #ccc;
        }

        .alert-item.high {
          border-left-color: #f44336;
        }

        .alert-item.medium {
          border-left-color: #ff9800;
        }

        .alert-item.low {
          border-left-color: #4CAF50;
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
        }

        .alert-title {
          font-weight: bold;
        }

        .alert-severity {
          text-transform: capitalize;
          font-weight: bold;
        }

        .alert-details {
          font-size: 0.9em;
        }

        .alert-meta {
          display: flex;
          justify-content: space-between;
          margin-top: 10px;
          font-size: 0.8em;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default EndpointList; 