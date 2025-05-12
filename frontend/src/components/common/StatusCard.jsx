import React from 'react';
import { FaArrowUp, FaArrowDown, FaEquals } from 'react-icons/fa';

const StatusCard = ({ title, value, change, trend = 'neutral', color = 'blue' }) => {
  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <FaArrowUp className="text-green-500" />;
      case 'down':
        return <FaArrowDown className="text-red-500" />;
      default:
        return <FaEquals className="text-yellow-500" />;
    }
  };

  return (
    <div className={`p-4 rounded-lg border-2 border-neon-${color} bg-neon-${color}/10`}>
      <h3 className="text-sm font-medium text-neon-blue/60">{title}</h3>
      <div className="mt-2 flex items-baseline justify-between">
        <p className="text-2xl font-semibold text-neon-blue">{value}</p>
        <div className="flex items-center space-x-1">
          {getTrendIcon(trend)}
          <span className={`text-sm ${
            trend === 'up' ? 'text-green-500' :
            trend === 'down' ? 'text-red-500' :
            'text-yellow-500'
          }`}>
            {change}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatusCard; 