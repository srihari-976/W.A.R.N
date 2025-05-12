import React from 'react';

const SecurityCard = ({ title, severity = 'low', children }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-500/10';
      case 'high':
        return 'border-orange-500 bg-orange-500/10';
      case 'medium':
        return 'border-yellow-500 bg-yellow-500/10';
      case 'low':
      default:
        return 'border-green-500 bg-green-500/10';
    }
  };

  return (
    <div className={`p-6 rounded-lg border-2 ${getSeverityColor(severity)} backdrop-blur-sm`}>
      <h3 className="text-xl font-bold text-neon-blue mb-4">{title}</h3>
      {children}
    </div>
  );
};

export default SecurityCard; 