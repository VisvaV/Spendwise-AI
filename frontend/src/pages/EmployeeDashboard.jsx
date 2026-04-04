import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function EmployeeDashboard() {
  const [expenses, setExpenses] = useState([]);
  const token = useAuthStore(state => state.token);

  useEffect(() => {
    const fetchExpenses = async () => {
      try {
        const res = await axios.get('/api/expenses/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setExpenses(res.data);
      } catch (e) {
        console.error("Failed to load expenses");
      }
    };
    fetchExpenses();
  }, [token]);

  const getStatusIcon = (status) => {
    switch(status) {
      case 'APPROVED': return <CheckCircle2 className="text-green-500" size={18} />;
      case 'REJECTED': return <XCircle className="text-red-500" size={18} />;
      case 'PENDING_INFO': return <AlertTriangle className="text-yellow-500" size={18} />;
      default: return <Clock className="text-blue-500" size={18} />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          My Expenses
        </h1>
        <div className="px-4 py-2 glass-card rounded-lg flex items-center gap-2">
          <span className="text-sm text-gray-400">Total Submitted (YTD):</span>
          <span className="text-lg font-bold text-primary">₹{expenses.reduce((acc, curr) => acc + curr.amount, 0).toLocaleString()}</span>
        </div>
      </div>

      <div className="glass-card shadow-lg shadow-black/50 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-white/5 border-b border-white/10 text-sm font-medium text-gray-400">
            <tr>
              <th className="p-4">Date</th>
              <th className="p-4">Title</th>
              <th className="p-4">Category / AI Tag</th>
              <th className="p-4 text-right">Amount</th>
              <th className="p-4 text-center">AI Risk</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {expenses.length === 0 && (
              <tr>
                <td colSpan="6" className="p-8 text-center text-gray-500">No expenses submitted yet.</td>
              </tr>
            )}
            {expenses.map((expense) => (
              <tr key={expense.id} className="hover:bg-white/5 transition-colors group">
                <td className="p-4 text-gray-300">
                  {new Date(expense.submitted_at).toLocaleDateString()}
                </td>
                <td className="p-4 font-medium">{expense.title}</td>
                <td className="p-4">
                  <div className="flex flex-col">
                    <span>{expense.category}</span>
                    {expense.ai_category && (
                      <span className="text-[10px] text-primary uppercase tracking-wider font-semibold">
                        AI: {expense.ai_category}
                      </span>
                    )}
                  </div>
                </td>
                <td className="p-4 text-right font-mono text-white group-hover:text-secondary transition-colors">
                  ₹{expense.amount.toLocaleString()}
                </td>
                <td className="p-4 text-center">
                  {expense.risk_score > 0.6 ? (
                    <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400 border border-red-500/30">High Risk</span>
                  ) : expense.risk_score > 0.2 ? (
                    <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">Mod Risk</span>
                  ) : (
                    <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">Low Risk</span>
                  )}
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(expense.status)}
                    <span className="text-sm font-medium">{expense.status.replace('_', ' ')}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
