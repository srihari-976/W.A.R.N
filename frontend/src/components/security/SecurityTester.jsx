import React, { useState } from 'react';
import SecurityCard from '../common/SecurityCard';
import StatusIndicator from '../common/StatusIndicator';
import axiosInstance from '../../utils/axiosInstance';

const SecurityTester = ({ onLogActivity, onIsolateEndpoint }) => {
  const [target, setTarget] = useState('');
  const [attackType, setAttackType] = useState('brute_force');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [isIsolated, setIsIsolated] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isolationResult, setIsolationResult] = useState(null);

  const handleTest = async () => {
    if (!target) {
      setError('Please enter a target IP or hostname');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResults(null);

    try {
      // Simulate API call to security test endpoint
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock results
      setResults({
        success: true,
        risk_level: Math.random() > 0.5 ? 'high' : 'low',
        vulnerabilities_found: Math.floor(Math.random() * 5),
        recommendations: [
          'Enable two-factor authentication',
          'Update security policies',
          'Implement rate limiting'
        ]
      });
    } catch (err) {
      setError('Failed to run security test');
    } finally {
      setIsRunning(false);
    }
  };

  const handleBruteForce = async () => {
    const newAttempts = attempts + 1;
    setAttempts(newAttempts);
    if (onLogActivity) {
      onLogActivity({
        type: 'security',
        event_type: 'Brute Force Attempt',
        description: `Brute force attempt #${newAttempts}`,
        timestamp: new Date().toISOString(),
      });
    }
    if (newAttempts === 5) {
      setIsIsolated(true);
      setShowModal(true);
      if (onLogActivity) {
        onLogActivity({
          type: 'threat',
          event_type: 'Brute Force Detected',
          description: '5 failed login attempts detected. System isolated and Brave killed.',
          timestamp: new Date().toISOString(),
        });
      }
      if (onIsolateEndpoint) {
        onIsolateEndpoint();
      }
      // Call backend to kill Brave
      try {
        const res = await axiosInstance.post('/api/isolation/isolate');
        setIsolationResult(res.data.message || 'Brave browser killed.');
      } catch (err) {
        setIsolationResult('Failed to kill Brave: ' + (err.response?.data?.message || err.message));
      }
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-neon-blue animate-pulse-neon">
        Security Test
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SecurityCard
          title="Test Configuration"
          severity="low"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neon-blue/60 mb-2">
                Target
              </label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="Enter IP or hostname"
                className="cyber-input w-full"
                disabled={isRunning}
              />
            </div>

            <div>
              <label className="block text-sm text-neon-blue/60 mb-2">
                Attack Type
              </label>
              <select
                value={attackType}
                onChange={(e) => setAttackType(e.target.value)}
                className="cyber-select w-full"
                disabled={isRunning}
                aria-label="Select attack type"
              >
                <option value="brute_force">Brute Force</option>
                <option value="sql_injection">SQL Injection</option>
                <option value="xss">Cross-Site Scripting</option>
              </select>
            </div>

            <button
              onClick={handleTest}
              disabled={isRunning}
              className="cyber-button-purple w-full"
            >
              {isRunning ? 'Running Test...' : 'Run Test'}
            </button>

            {error && (
              <div className="text-red-500 text-sm">{error}</div>
            )}
          </div>
        </SecurityCard>

        {results && (
          <SecurityCard
            title="Test Results"
            severity={results.risk_level}
          >
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <StatusIndicator
                  status={results.risk_level === 'high' ? 'critical' : 'healthy'}
                  pulse={results.risk_level === 'high'}
                />
                <span className="text-neon-blue">
                  Risk Level: {results.risk_level.toUpperCase()}
                </span>
              </div>

              <div className="text-neon-blue">
                Vulnerabilities Found: {results.vulnerabilities_found}
              </div>

              <div>
                <h3 className="text-sm text-neon-blue/60 mb-2">
                  Recommendations:
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {results.recommendations.map((rec, index) => (
                    <li key={index} className="text-neon-blue">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </SecurityCard>
        )}
      </div>

      <div className="mt-6">
        <h2 className="text-2xl font-bold mb-4">Brute Force Simulation</h2>
        <div className="mb-4">
          <button
            className="cyber-button-blue px-6 py-2 text-lg font-bold"
            onClick={handleBruteForce}
            disabled={isIsolated}
          >
            Simulate Brute Force Attempt
          </button>
        </div>
        <div className="mb-4 text-neon-blue/80">
          Attempts: <span className="font-bold">{attempts}</span> / 5
        </div>
        {isIsolated && (
          <div className="p-4 bg-red-900/40 border border-neon-pink/40 rounded text-neon-pink font-bold">
            System Isolated! Brave/browser killed due to brute force attack.
          </div>
        )}
        {showModal && (
          <div className="fixed inset-0 flex items-center justify-center z-60">
            <div className="absolute inset-0 bg-black/70" onClick={() => setShowModal(false)} />
            <div className="relative bg-cyber-dark border border-neon-pink/40 rounded-lg shadow-lg p-8 max-w-lg w-full">
              <h2 className="text-xl font-bold text-neon-pink mb-4">System Isolated</h2>
              <p className="mb-4">5 failed brute force attempts detected.<br />Brave/browser has been killed and the system is now isolated.</p>
              {isolationResult && (
                <div className="text-neon-pink">
                  {isolationResult}
                </div>
              )}
              <button className="cyber-button-blue" onClick={() => setShowModal(false)}>Close</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityTester; 