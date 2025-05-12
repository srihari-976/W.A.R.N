import React from 'react';
import { FaShieldAlt, FaSearch, FaSync, FaExclamationTriangle } from 'react-icons/fa';

const QuickActions = ({ onAction }) => {
  const actions = [
    {
      id: 'scan',
      title: 'Run Scan',
      description: 'Initiate a full system security scan',
      icon: <FaSearch className="w-6 h-6" />,
      color: 'blue'
    },
    {
      id: 'update',
      title: 'Update Agents',
      description: 'Update security agents on all endpoints',
      icon: <FaSync className="w-6 h-6" />,
      color: 'purple'
    },
    {
      id: 'isolate',
      title: 'Isolate Endpoint',
      description: 'Isolate a compromised endpoint',
      icon: <FaShieldAlt className="w-6 h-6" />,
      color: 'red'
    },
    {
      id: 'alert',
      title: 'Create Alert',
      description: 'Create a new security alert',
      icon: <FaExclamationTriangle className="w-6 h-6" />,
      color: 'yellow'
    }
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-neon-blue">Quick Actions</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {actions.map(action => (
          <button
            key={action.id}
            onClick={() => onAction(action.id)}
            className={`p-4 rounded-lg border-2 border-neon-${action.color} bg-neon-${action.color}/10 
              hover:bg-neon-${action.color}/20 transition-colors text-left`}
          >
            <div className="flex items-start space-x-3">
              <div className={`text-neon-${action.color}`}>
                {action.icon}
              </div>
              <div>
                <h4 className="font-medium text-neon-blue">
                  {action.title}
                </h4>
                <p className="text-sm text-neon-blue/60 mt-1">
                  {action.description}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions; 