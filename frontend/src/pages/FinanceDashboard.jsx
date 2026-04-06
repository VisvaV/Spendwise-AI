import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { ShieldAlert, TrendingUp, AlertOctagon } from 'lucide-react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

export default function FinanceDashboard() {
  const token = useAuthStore(state => state.token);
  const [metrics, setMetrics] = useState({
    total_pipeline: 0,
    flagged_count: 0,
    policy_breaches: 0,
    risk_data: [],
    category_spend: []
  });

  React.useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await axios.get('/api/finance/metrics', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMetrics(res.data);
      } catch (e) {
        console.error("Failed to fetch finance metrics", e);
      }
    };
    fetchMetrics();
  }, [token]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Finance Risk Dashboard
        </h1>
        <button className="glass-card hover:border-primary/50 px-4 py-2 font-medium text-sm transition-all text-secondary">
          Export Compliance Report
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-t-2 border-primary">
          <div className="flex items-center gap-3 text-gray-400 mb-2">
            <TrendingUp size={20} className="text-primary"/> Total Pipeline
          </div>
          <p className="text-3xl font-mono text-white">₹{metrics.total_pipeline.toLocaleString('en-IN')}</p>
        </div>
        <div className="glass-card p-6 border-t-2 border-red-500">
          <div className="flex items-center gap-3 text-gray-400 mb-2">
            <ShieldAlert size={20} className="text-red-500"/> Flagged by AI
          </div>
          <p className="text-3xl font-mono text-white">{metrics.flagged_count}</p>
        </div>
        <div className="glass-card p-6 border-t-2 border-secondary">
          <div className="flex items-center gap-3 text-gray-400 mb-2">
            <AlertOctagon size={20} className="text-secondary"/> Policy Breaches
          </div>
          <p className="text-3xl font-mono text-white">{metrics.policy_breaches}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
        <div className="glass-card p-6 flex flex-col">
          <h3 className="text-lg font-bold mb-4">Risk Distribution</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={metrics.risk_data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={60} stroke="none">
                  {metrics.risk_data.map((entry, index) => <Cell key={`cell-\${index}`} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0f', borderColor: '#333', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-6 flex flex-col">
          <h3 className="text-lg font-bold mb-4">Spend By Category (YTD)</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.category_spend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tickLine={false} />
                <YAxis stroke="#666" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0f', borderColor: '#333', borderRadius: '8px' }} />
                {Object.keys(metrics.category_spend[0] || {}).filter(k => k !== 'name').map((catKey, i) => (
                   <Bar key={catKey} dataKey={catKey} stackId="a" fill={['#7c3aed', '#06b6d4', '#3b82f6', '#ec4899', '#f59e0b'][i % 5]} radius={i === 0 ? [0,0,0,0] : [4,4,0,0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
