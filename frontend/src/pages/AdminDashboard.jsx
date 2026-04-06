import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Users, Settings, Database, Activity } from 'lucide-react';

export default function AdminDashboard() {
  const token = useAuthStore(state => state.token);
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState({ users_count: 0, policies_count: 0, budgets_count: 0, logs_count: 0 });

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const [logsRes, metricsRes] = await Promise.all([
          axios.get('/api/logs', { headers: { Authorization: `Bearer ${token}` } }),
          axios.get('/api/admin/metrics', { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setLogs(logsRes.data);
        setMetrics(metricsRes.data);
      } catch (e) {
        console.error("Failed to fetch admin data", e);
      }
    };
    fetchAdminData();
  }, [token]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
        System Administration
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { icon: Users, label: `Manage Users (${metrics.users_count})`, color: 'text-primary' },
          { icon: Settings, label: `Policy Rules (${metrics.policies_count})`, color: 'text-secondary' },
          { icon: Database, label: `Budgets (${metrics.budgets_count})`, color: 'text-green-500' },
          { icon: Activity, label: `Service Logs (${metrics.logs_count})`, color: 'text-yellow-500' }
        ].map((item, i) => (
          <div key={i} className="glass-card hover:bg-white/5 transition-all cursor-pointer p-6 flex flex-col items-center justify-center text-center gap-3">
            <item.icon size={32} className={item.color} />
            <span className="font-medium text-gray-200">{item.label}</span>
          </div>
        ))}
      </div>

      <h2 className="text-xl font-bold mt-8 mb-4">Immutable Audit Logs</h2>
      <div className="glass-card shadow-lg shadow-black/50 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-white/5 border-b border-white/10 font-medium text-gray-400">
            <tr>
              <th className="p-4">Timestamp</th>
              <th className="p-4">Actor ID</th>
              <th className="p-4">Expense ID</th>
              <th className="p-4">Transition</th>
              <th className="p-4">Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-gray-300">
            {logs.length === 0 && <tr><td colSpan={5} className="p-4 text-center">No logs available</td></tr>}
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-white/5 transition-colors">
                <td className="p-4">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="p-4">User {log.actor_id}</td>
                <td className="p-4">EXP-{log.expense_id}</td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-white/5 rounded text-gray-400">{log.from_state}</span>
                  <span className="mx-2">→</span>
                  <span className="px-2 py-1 bg-primary/20 text-primary border border-primary/30 rounded">{log.to_state}</span>
                </td>
                <td className="p-4 text-gray-400">{log.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
