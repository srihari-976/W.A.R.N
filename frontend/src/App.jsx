import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/dashboard/Dashboard';
import EndpointList from './components/endpoints/EndpointList';
import ThreatList from './components/threats/ThreatList';
import AssetDetails from './components/endpoints/AssetDetails';
import SecurityTester from './components/security/SecurityTester';
import NotificationsPanel from './components/NotificationsPanel';
import { FaBell } from 'react-icons/fa';
import NetworkPage from './components/network/NetworkPage';
import ProcessesPage from './components/processes/ProcessesPage';
import InstagramLogin from './components/InstagramLogin';

const App = () => {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-cyber-black text-neon-blue">
        <nav className="bg-cyber-dark border-b border-neon-blue/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <Link to="/" className="text-2xl font-bold text-neon-blue hover:text-neon-purple transition-colors">
                  W.A.R.N
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/endpoints" className="text-neon-blue/80 hover:text-neon-blue">
                  Endpoints
                </Link>
                <Link to="/threats" className="text-neon-blue/80 hover:text-neon-blue">
                  Threats
                </Link>
                <Link to="/processes" className="text-neon-blue/80 hover:text-neon-blue">
                  Processes
                </Link>
                <Link to="/network" className="text-neon-blue/80 hover:text-neon-blue">
                  Network
                </Link>
                <Link to="/security-test" className="text-neon-blue/80 hover:text-neon-blue">
                  Security Test
                </Link>
                <button
                  onClick={() => setIsNotificationsOpen(true)}
                  className="text-neon-blue/80 hover:text-neon-blue transition-colors"
                  aria-label="Open notifications"
                >
                  <FaBell className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard onOpenNotifications={() => setIsNotificationsOpen(true)} />} />
            <Route path="/endpoints" element={<EndpointList />} />
            <Route path="/endpoints/:id" element={<AssetDetails />} />
            <Route path="/threats" element={<ThreatList />} />
            <Route path="/processes" element={<ProcessesPage />} />
            <Route path="/network" element={<NetworkPage />} />
            <Route path="/security-test" element={<SecurityTester />} />
            <Route path="/instagram-login" element={<InstagramLogin />} />
          </Routes>
        </main>

        <NotificationsPanel
          isOpen={isNotificationsOpen}
          onClose={() => setIsNotificationsOpen(false)}
        />
      </div>
    </Router>
  );
};

export default App; 