import React, { useState } from 'react';

const mockConnections = [
  { id: 1, local: '192.168.1.10:443', remote: '172.217.3.110:443', protocol: 'TCP', status: 'ESTABLISHED', process: 'chrome.exe' },
  { id: 2, local: '192.168.1.10:22', remote: '10.0.0.5:51234', protocol: 'TCP', status: 'CLOSE_WAIT', process: 'sshd' },
  { id: 3, local: '192.168.1.10:8080', remote: '203.0.113.5:80', protocol: 'TCP', status: 'LISTEN', process: 'node.exe' },
  { id: 4, local: '192.168.1.10:53', remote: '8.8.8.8:53', protocol: 'UDP', status: 'ESTABLISHED', process: 'dns.exe' },
  { id: 5, local: '192.168.1.10:3306', remote: '10.0.0.20:60000', protocol: 'TCP', status: 'TIME_WAIT', process: 'mysqld' },
];

const NetworkPage = () => {
  const [search, setSearch] = useState('');
  const filtered = mockConnections.filter(
    c => c.local.includes(search) || c.remote.includes(search) || c.process.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 text-neon-blue">
      <h1 className="text-2xl font-bold mb-6">Network Activity</h1>
      <div className="mb-4 flex items-center gap-4">
        <input
          className="bg-black/60 border border-neon-blue/40 rounded px-4 py-2 text-neon-blue focus:outline-none focus:ring-2 focus:ring-neon-blue"
          placeholder="Search by IP, port, or process..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>
      <div className="overflow-x-auto rounded-lg border border-neon-blue/20 bg-black/40">
        <table className="min-w-full text-left">
          <thead>
            <tr className="bg-black/60">
              <th className="px-4 py-2 text-neon-blue">Local Address</th>
              <th className="px-4 py-2 text-neon-blue">Remote Address</th>
              <th className="px-4 py-2 text-neon-blue">Protocol</th>
              <th className="px-4 py-2 text-neon-blue">Status</th>
              <th className="px-4 py-2 text-neon-blue">Process</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-neon-blue/60">No connections found.</td>
              </tr>
            ) : (
              filtered.map(conn => (
                <tr key={conn.id} className="hover:bg-neon-blue/10 transition">
                  <td className="px-4 py-2">{conn.local}</td>
                  <td className="px-4 py-2">{conn.remote}</td>
                  <td className="px-4 py-2">{conn.protocol}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${conn.status === 'ESTABLISHED' ? 'bg-green-500/30 text-green-400' : 'bg-yellow-500/20 text-yellow-300'}`}>{conn.status}</span>
                  </td>
                  <td className="px-4 py-2">{conn.process}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NetworkPage; 