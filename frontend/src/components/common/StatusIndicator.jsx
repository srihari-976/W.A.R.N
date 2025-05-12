import React from 'react';

const StatusIndicator = ({ status = 'healthy', pulse = false }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'critical':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'healthy':
      default:
        return 'bg-green-500';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div
        className={`w-3 h-3 rounded-full ${getStatusColor(status)} ${
          pulse ? 'animate-pulse' : ''
        }`}
      />
      <span className="text-sm text-neon-blue capitalize">{status}</span>
    </div>
  );
};

export default StatusIndicator; 