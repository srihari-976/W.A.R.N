import React, { useState, useEffect } from 'react';
import axiosInstance from '../utils/axiosInstance';
import { FaTimes, FaFileExport, FaDownload, FaCheck, FaEye, FaTrash } from 'react-icons/fa';

const NotificationsPanel = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [alertsRes, eventsRes] = await Promise.all([
          axiosInstance.get('/api/alerts'),
          axiosInstance.get('/api/events')
        ]);
        setNotifications(alertsRes.data.alerts);
        setLogs(eventsRes.data.events);
      } catch (error) {
        console.error('Error fetching notifications:', error);
      } finally {
        setLoading(false);
      }
    };
    if (isOpen) {
      fetchData();
      const interval = setInterval(fetchData, 10000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const markAsRead = async (alertId) => {
    // Simulate mark as read (backend can be extended for real support)
    setNotifications(notifications.map(a => a.id === alertId ? { ...a, read: true } : a));
  };

  const clearAlert = async (alertId) => {
    // Simulate delete (backend can be extended for real support)
    setNotifications(notifications.filter(a => a.id !== alertId));
  };

  const exportCSV = (data) => {
    if (!data || data.length === 0) {
      console.error('No data to export');
      return;
    }
    try {
      const header = Object.keys(data[0]).join(',');
      const rows = data.map(row => Object.values(row).join(','));
      const csv = [header, ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'security_logs.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  const exportJSON = (data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'security_logs.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="absolute inset-0 bg-cyber-black/80" onClick={onClose} />
      <div className="relative bg-cyber-dark border border-neon-blue/20 rounded-lg shadow-neon-glow w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-neon-blue/20">
          <h2 className="text-2xl font-bold text-neon-blue animate-pulse-neon">
            Notifications & Logs
          </h2>
          <button
            onClick={onClose}
            className="text-neon-blue/60 hover:text-neon-blue transition-colors"
          >
            <FaTimes className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {loading ? (
            <div className="text-neon-blue animate-pulse">Loading...</div>
          ) : (
            <>
              {/* Notifications Section */}
              <div className="mb-8">
                <h3 className="text-lg font-bold text-neon-purple mb-4">Recent Alerts</h3>
                <div className="space-y-4">
                  {notifications.length === 0 ? (
                    <div className="text-neon-blue/60">No recent alerts</div>
                  ) : (
                    notifications.map(alert => (
                      <div
                        key={alert.id}
                        className={`p-4 rounded bg-cyber-gray/50 border ${alert.severity === 'high' ? 'border-neon-pink/40' : 'border-neon-purple/20'} flex flex-col gap-2 relative`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`font-bold ${alert.severity === 'high' ? 'text-neon-pink' : 'text-neon-purple'}`}>
                            {alert.alert_type}
                          </span>
                          <span className="text-neon-blue/60 text-sm">
                            {new Date(alert.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="mt-2 text-neon-blue/80">{alert.details?.description || alert.description}</p>
                        <div className="flex gap-2 mt-2">
                          <button
                            className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${alert.read ? 'bg-gray-700 text-gray-400' : 'bg-green-500/30 text-green-400 hover:bg-green-500/50'}`}
                            onClick={() => markAsRead(alert.id)}
                            disabled={alert.read}
                          >
                            <FaCheck /> Mark as Read
                          </button>
                          <button
                            className="px-2 py-1 rounded text-xs flex items-center gap-1 bg-blue-500/30 text-neon-blue hover:bg-blue-500/50"
                            onClick={() => setSelectedAlert(alert)}
                          >
                            <FaEye /> View Details
                          </button>
                          <button
                            className="px-2 py-1 rounded text-xs flex items-center gap-1 bg-red-500/30 text-neon-pink hover:bg-red-500/50"
                            onClick={() => clearAlert(alert.id)}
                          >
                            <FaTrash /> Clear
                          </button>
                        </div>
                        {alert.read && <span className="absolute top-2 right-2 text-xs text-green-400">Read</span>}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Logs Section */}
              <div>
                <h3 className="text-lg font-bold text-neon-blue mb-4">Event Log</h3>
                <div className="space-y-4">
                  {logs.length === 0 ? (
                    <div className="text-neon-blue/60">No events recorded</div>
                  ) : (
                    logs.map(event => (
                      <div
                        key={event.id}
                        className="p-4 rounded bg-cyber-gray/50 border border-neon-blue/20"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-neon-blue font-bold">{event.event_type}</span>
                          <span className="text-neon-blue/60 text-sm">
                            {new Date(event.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div className="mt-2 text-neon-blue/80">
                          <span className="mr-4">Source: {event.source_ip}</span>
                          {event.details?.user && (
                            <span>User: {event.details.user}</span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="p-6 border-t border-neon-blue/20 bg-cyber-gray/30">
          <div className="flex justify-end space-x-4">
            <button
              onClick={() => exportCSV(logs)}
              className="cyber-button-blue flex items-center space-x-2"
            >
              <FaFileExport className="w-4 h-4" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => exportJSON(logs)}
              className="cyber-button-purple flex items-center space-x-2"
            >
              <FaDownload className="w-4 h-4" />
              <span>Export JSON</span>
            </button>
          </div>
        </div>

        {/* Alert Details Modal */}
        {selectedAlert && (
          <div className="fixed inset-0 flex items-center justify-center z-60">
            <div className="absolute inset-0 bg-black/70" onClick={() => setSelectedAlert(null)} />
            <div className="relative bg-cyber-dark border border-neon-purple/40 rounded-lg shadow-lg p-8 max-w-lg w-full">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-xl font-bold text-neon-purple">Alert Details</h4>
                <button onClick={() => setSelectedAlert(null)} className="text-neon-purple/60 hover:text-neon-purple">
                  <FaTimes className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-2">
                <div><span className="font-bold">Type:</span> {selectedAlert.alert_type}</div>
                <div><span className="font-bold">Severity:</span> <span className={selectedAlert.severity === 'high' ? 'text-neon-pink' : 'text-neon-purple'}>{selectedAlert.severity}</span></div>
                <div><span className="font-bold">Time:</span> {new Date(selectedAlert.timestamp).toLocaleString()}</div>
                <div><span className="font-bold">Description:</span> {selectedAlert.details?.description || selectedAlert.description}</div>
                {selectedAlert.details && Object.keys(selectedAlert.details).map(key => (
                  key !== 'description' && <div key={key}><span className="font-bold">{key}:</span> {String(selectedAlert.details[key])}</div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsPanel; 