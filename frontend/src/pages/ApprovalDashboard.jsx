import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Check, X, ShieldAlert, FileText } from 'lucide-react';

export default function ApprovalDashboard() {
  const [pending, setPending] = useState([]);
  const token = useAuthStore(state => state.token);

  useEffect(() => {
    // In reality this would be an endpoint fetching all expenses requiring this user's approval
    const fetchApprovals = async () => {
      try {
        // Mocking for now since backend needs a specific 'pending for me' query
        setPending([
          { id: 101, title: 'Flight to NYC', amount: 45000, category: 'Travel', risk_score: 0.1, employee_name: 'John Doe', date: '2026-03-25' },
          { id: 102, title: 'Client Dinner', amount: 15000, category: 'Meals', risk_score: 0.85, ai_category: 'Meals', employee_name: 'Jane Smith', date: '2026-03-26' }
        ]);
      } catch(e) {}
    };
    fetchApprovals();
  }, [token]);

  const handleAction = async (id, action) => {
    try {
      await axios.post(`/api/approvals/${id}/action`, { action, note: "Reviewed via portal" }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPending(pending.filter(p => p.id !== id));
    } catch(e) {
      alert("Failed action");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
        Approval Inbox
      </h1>

      <div className="grid gap-6">
        {pending.length === 0 && <p className="text-gray-400">All caught up!</p>}
        {pending.map(expense => (
          <div key={expense.id} className="glass-card p-6 flex flex-col md:flex-row justify-between gap-6 transition-all hover:border-primary/50">
            <div className="flex-1 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold">{expense.title}</h3>
                  <p className="text-gray-400 text-sm">Submitted by {expense.employee_name} • {expense.date}</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-mono text-white tracking-tight">₹{expense.amount.toLocaleString()}</span>
                  <p className="text-sm text-primary uppercase font-bold">{expense.category}</p>
                </div>
              </div>

              <div className="flex gap-4 p-4 rounded-xl bg-black/40 border border-white/5">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={18} className={expense.risk_score > 0.7 ? "text-red-500" : "text-green-500"} />
                  <span className="text-sm font-medium text-gray-300">
                    AI Risk Score: <span className={expense.risk_score > 0.7 ? "text-red-400" : "text-green-400"}>{(expense.risk_score * 100).toFixed(0)}/100</span>
                  </span>
                </div>
                <div className="w-px h-6 bg-white/10 mx-2"></div>
                <button className="text-sm text-secondary flex items-center gap-1 hover:underline">
                  <FileText size={16}/> View Receipt
                </button>
              </div>
            </div>

            <div className="flex md:flex-col gap-3 justify-center border-t md:border-t-0 md:border-l border-white/10 pt-4 md:pt-0 md:pl-6">
              <button onClick={() => handleAction(expense.id, 'APPROVED')} className="flex items-center justify-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 border border-green-500/50 py-2 md:py-3 px-6 rounded-lg transition-all font-medium whitespace-nowrap">
                <Check size={18}/> Approve
              </button>
              <button onClick={() => handleAction(expense.id, 'REJECTED')} className="flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/50 py-2 md:py-3 px-6 rounded-lg transition-all font-medium whitespace-nowrap">
                <X size={18}/> Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
