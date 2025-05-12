import React, { useState } from 'react';

const mockProcesses = [
  { pid: 101, name: 'chrome.exe', user: 'alice', cpu: 12.5, mem: 150, status: 'Running' },
  { pid: 202, name: 'node.exe', user: 'bob', cpu: 8.2, mem: 90, status: 'Sleeping' },
  { pid: 303, name: 'mysqld', user: 'mysql', cpu: 3.1, mem: 200, status: 'Running' },
  { pid: 404, name: 'sshd', user: 'root', cpu: 0.5, mem: 30, status: 'Idle' },
  { pid: 505, name: 'explorer.exe', user: 'alice', cpu: 1.2, mem: 70, status: 'Running' },
];

const ProcessesPage = () => {
  const [search, setSearch] = useState('');
  const filtered = mockProcesses.filter(
    p => p.name.toLowerCase().includes(search.toLowerCase()) || String(p.pid).includes(search) || p.user.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 text-neon-blue">
      <h1 className="text-2xl font-bold mb-6">Processes</h1>
      <div className="mb-4 flex items-center gap-4">
        <input
          className="bg-black/60 border border-neon-blue/40 rounded px-4 py-2 text-neon-blue focus:outline-none focus:ring-2 focus:ring-neon-blue"
          placeholder="Search by name, PID, or user..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>
      <div className="overflow-x-auto rounded-lg border border-neon-blue/20 bg-black/40">
        <table className="min-w-full text-left">
          <thead>
            <tr className="bg-black/60">
              <th className="px-4 py-2 text-neon-blue">PID</th>
              <th className="px-4 py-2 text-neon-blue">Name</th>
              <th className="px-4 py-2 text-neon-blue">User</th>
              <th className="px-4 py-2 text-neon-blue">CPU %</th>
              <th className="px-4 py-2 text-neon-blue">Memory (MB)</th>
              <th className="px-4 py-2 text-neon-blue">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-neon-blue/60">No processes found.</td>
              </tr>
            ) : (
              filtered.map(proc => (
                <tr key={proc.pid} className="hover:bg-neon-blue/10 transition">
                  <td className="px-4 py-2">{proc.pid}</td>
                  <td className="px-4 py-2">{proc.name}</td>
                  <td className="px-4 py-2">{proc.user}</td>
                  <td className="px-4 py-2">{proc.cpu.toFixed(1)}</td>
                  <td className="px-4 py-2">{proc.mem}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${proc.status === 'Running' ? 'bg-green-500/30 text-green-400' : proc.status === 'Sleeping' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-gray-500/20 text-gray-300'}`}>{proc.status}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProcessesPage; 