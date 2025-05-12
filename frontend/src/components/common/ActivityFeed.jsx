import React from 'react';
import { FaBell, FaShieldAlt, FaExclamationTriangle, FaCheckCircle } from 'react-icons/fa';

const ActivityFeed = ({ activities = [] }) => {
  const getActivityIcon = (type) => {
    switch (type) {
      case 'alert':
        return <FaExclamationTriangle className="text-red-500" />;
      case 'security':
        return <FaShieldAlt className="text-blue-500" />;
      case 'notification':
        return <FaBell className="text-yellow-500" />;
      case 'success':
        return <FaCheckCircle className="text-green-500" />;
      default:
        return <FaBell className="text-neon-blue" />;
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-neon-blue">Activity Feed</h3>
      <div className="space-y-3">
        {activities.map((activity, index) => (
          <div
            key={index}
            className="flex items-start space-x-3 p-3 rounded-lg bg-cyber-dark/50 border border-neon-blue/20"
          >
            <div className="mt-1">
              {getActivityIcon(activity.type)}
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <p className="text-neon-blue font-medium">{activity.title}</p>
                <span className="text-sm text-neon-blue/60">
                  {new Date(activity.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-neon-blue/80 text-sm mt-1">
                {activity.description}
              </p>
              {activity.details && (
                <div className="mt-2 text-sm text-neon-blue/60">
                  {activity.details}
                </div>
              )}
            </div>
          </div>
        ))}
        {activities.length === 0 && (
          <div className="text-center text-neon-blue/60 py-4">
            No recent activities
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityFeed; 