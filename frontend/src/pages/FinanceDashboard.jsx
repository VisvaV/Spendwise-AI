import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { ShieldAlert, TrendingUp, AlertOctagon } from 'lucide-react';

const riskData = [
  { name: 'Low Risk', value: 400, color: '#22c55e' },
  { name: 'Medium Risk', value: 150, color: '#eab308' },
  { name: 'High Risk', value: 45, color: '#ef4444' }
];

const categorySpend = [
  { name: 'Jan', Travel: 4000, Meals: 2400, Equipment: 2400 },
  { name: 'Feb', Travel: 3000, Meals: 1398, Equipment: 2210 },
  { name: 'Mar', Travel: 2000, Meals: 9800, Equipment: 2290 },
  { name: 'Apr', Travel: 2780, Meals: 3908, Equipment: 2000 },
];

export default function FinanceDashboard() {
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
          <p className="text-3xl font-mono text-white">₹2,45,000</p>
        </div>
        <div className="glass-card p-6 border-t-2 border-red-500">
          <div className="flex items-center gap-3 text-gray-400 mb-2">
            <ShieldAlert size={20} className="text-red-500"/> Flagged by AI
          </div>
          <p className="text-3xl font-mono text-white">45</p>
        </div>
        <div className="glass-card p-6 border-t-2 border-secondary">
          <div className="flex items-center gap-3 text-gray-400 mb-2">
            <AlertOctagon size={20} className="text-secondary"/> Policy Breaches
          </div>
          <p className="text-3xl font-mono text-white">12</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96">
        <div className="glass-card p-6 flex flex-col">
          <h3 className="text-lg font-bold mb-4">Risk Distribution</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={60} stroke="none">
                  {riskData.map((entry, index) => <Cell key={`cell-\${index}`} fill={entry.color} />)}
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
              <BarChart data={categorySpend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tickLine={false} />
                <YAxis stroke="#666" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0f', borderColor: '#333', borderRadius: '8px' }} />
                <Bar dataKey="Travel" stackId="a" fill="#7c3aed" radius={[0,0,0,0]} />
                <Bar dataKey="Meals" stackId="a" fill="#06b6d4" radius={[0,0,0,0]} />
                <Bar dataKey="Equipment" stackId="a" fill="#3b82f6" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
