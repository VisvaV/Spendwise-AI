import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Clock, CheckCircle2, XCircle, AlertTriangle, FileText, ChevronRight } from 'lucide-react';

export default function EmployeeDashboard() {
  const [expenses, setExpenses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedExpense, setSelectedExpense] = useState(null);
  
  const [statusFilter, setStatusFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");
  
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
      } finally {
        setIsLoading(false);
      }
    };
    fetchExpenses();
  }, [token]);

  const openExpenseDrawer = async (expense) => {
    setSelectedExpense({...expense, isLoadingDetails: true});
    try {
        const res = await axios.get(`/api/expenses/${expense.id}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        setSelectedExpense(res.data);
    } catch(e) {
        console.error(e);
        setSelectedExpense(expense);
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'APPROVED': return <CheckCircle2 className="text-green-500" size={18} />;
      case 'REJECTED': return <XCircle className="text-red-500" size={18} />;
      case 'PENDING_INFO': return <AlertTriangle className="text-yellow-500" size={18} />;
      default: return <Clock className="text-blue-500" size={18} />;
    }
  };

  const filteredExpenses = expenses.filter(e => {
    if (statusFilter !== "All" && e.status !== statusFilter) return false;
    if (categoryFilter !== "All" && e.category !== categoryFilter) return false;
    return true;
  });

  const totalYTD = expenses.reduce((acc, curr) => acc + curr.amount, 0);
  const pendingCount = expenses.filter(e => e.status === "SUBMITTED").length;
  const approvedCount = expenses.filter(e => e.status === "APPROVED").length;

  return (
    <div className="space-y-6 relative">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          My Expenses
        </h1>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="p-4 glass-card rounded-lg flex flex-col gap-1 border-l-4 border-l-primary">
          <span className="text-sm text-gray-400">Total Submitted (YTD)</span>
          <span className="text-2xl font-bold text-white">₹{totalYTD.toLocaleString()}</span>
        </div>
        <div className="p-4 glass-card rounded-lg flex flex-col gap-1 border-l-4 border-l-blue-500">
          <span className="text-sm text-gray-400">Pending Approval</span>
          <span className="text-2xl font-bold text-white">{pendingCount}</span>
        </div>
        <div className="p-4 glass-card rounded-lg flex flex-col gap-1 border-l-4 border-l-green-500">
          <span className="text-sm text-gray-400">Approved</span>
          <span className="text-2xl font-bold text-white">{approvedCount}</span>
        </div>
      </div>

      <div className="flex gap-4">
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="bg-black/50 border border-gray-700 rounded-lg p-2 text-sm text-white">
          <option value="All">All Statuses</option>
          <option value="SUBMITTED">Submitted</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className="bg-black/50 border border-gray-700 rounded-lg p-2 text-sm text-white">
          <option value="All">All Categories</option>
          <option value="Travel">Travel</option>
          <option value="Meals">Meals</option>
          <option value="Software">Software</option>
          <option value="Accommodation">Accommodation</option>
          <option value="Equipment">Equipment</option>
        </select>
      </div>

      <div className="glass-card shadow-lg shadow-black/50 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-white/5 border-b border-white/10 text-sm font-medium text-gray-400">
            <tr>
              <th className="p-4">Date</th>
              <th className="p-4">Title</th>
              <th className="p-4">Category</th>
              <th className="p-4 text-right">Amount</th>
              <th className="p-4 text-center">AI Risk</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {isLoading && (
               Array(3).fill(0).map((_, i) => (
                 <tr key={i}>
                   <td colSpan="6" className="p-4"><div className="h-6 bg-white/5 animate-pulse rounded"></div></td>
                 </tr>
               ))
            )}
            {!isLoading && filteredExpenses.length === 0 && (
              <tr>
                <td colSpan="6" className="p-8 text-center text-gray-500">No expenses found.</td>
              </tr>
            )}
            {!isLoading && filteredExpenses.map((expense) => (
              <tr key={expense.id} onClick={() => openExpenseDrawer(expense)} className="hover:bg-white/5 transition-colors group cursor-pointer">
                <td className="p-4 text-gray-300">
                  {new Date(expense.submitted_at).toLocaleDateString()}
                </td>
                <td className="p-4 font-medium flex items-center gap-2">
                  {expense.title}
                  {expense.receipt_s3_url && <FileText size={12} className="text-gray-500" />}
                </td>
                <td className="p-4">
                  <div className="flex flex-col">
                    <span>{expense.category}</span>
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
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(expense.status)}
                      <span className="text-sm font-medium">{expense.status.replace('_', ' ')}</span>
                    </div>
                    <ChevronRight size={16} className="text-gray-600 group-hover:text-white transition-colors"/>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedExpense && (
        <>
          <div className="fixed inset-0 bg-black/60 z-40" onClick={() => setSelectedExpense(null)}></div>
          <div className="fixed right-0 top-0 h-full w-[420px] bg-gray-900 border-l border-gray-700 z-50 p-6 shadow-2xl overflow-y-auto animate-in slide-in-from-right">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Expense Details</h2>
              <button onClick={() => setSelectedExpense(null)} className="text-gray-400 hover:text-white"><XCircle size={24}/></button>
            </div>
            
            <div className="space-y-6">
              <div className="glass-card p-4 rounded-lg border-l-4 border-l-secondary">
                <p className="text-sm text-gray-400">Amount</p>
                <p className="text-3xl font-mono text-white">₹{selectedExpense.amount.toLocaleString()}</p>
                <p className="text-sm font-medium text-primary mt-1">{selectedExpense.category}</p>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold text-gray-300">Overview</h3>
                <div className="bg-black/30 p-3 rounded-lg text-sm space-y-2 border border-white/5">
                  <div className="flex justify-between"><span className="text-gray-500">Title</span> <span>{selectedExpense.title}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Submission Date</span> <span>{new Date(selectedExpense.submitted_at).toLocaleDateString()}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Status</span> <span className="font-bold flex items-center gap-1">{getStatusIcon(selectedExpense.status)} {selectedExpense.status.replace('_', ' ')}</span></div>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold text-gray-300">AI Intelligence</h3>
                <div className="bg-black/30 p-4 rounded-lg text-sm border border-white/5 relative overflow-hidden">
                  <div className="absolute top-0 left-0 h-1 bg-gradient-to-r from-secondary to-primary" style={{width: `${selectedExpense.risk_score * 100}%`}}></div>
                  <div className="flex justify-between mt-1"><span className="text-gray-500">Risk Score</span> <span className={selectedExpense.risk_score > 0.6 ? "text-red-400 font-bold" : "text-green-400 font-bold"}>{(selectedExpense.risk_score * 100).toFixed(0)} / 100</span></div>
                  <div className="flex justify-between mt-2"><span className="text-gray-500">AI Category</span> <span>{selectedExpense.ai_category || "N/A"}</span></div>
                  <div className="mt-3 flex gap-2 flex-wrap">
                    {selectedExpense.risk_flags && selectedExpense.risk_flags.map((f, i) => <span key={i} className="text-[10px] uppercase bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">{f}</span>)}
                    {selectedExpense.duplicate_flag && <span className="text-[10px] uppercase bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 px-2 py-0.5 rounded-full">DUPLICATE</span>}
                  </div>
                </div>
              </div>
              
              {selectedExpense.receipt_s3_url && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-gray-300">Receipt</h3>
                  <a href={selectedExpense.receipt_s3_url} target="_blank" rel="noreferrer" className="block w-full h-40 bg-black/50 border border-gray-700 rounded-lg flex flex-col justify-center items-center hover:bg-black/40 transition-colors group">
                    <FileText size={32} className="text-gray-500 group-hover:text-secondary mb-2" />
                    <span className="text-xs text-secondary font-medium">Click to view full receipt</span>
                  </a>
                </div>
              )}
              {selectedExpense.receipt_s3_url && (
                <div className="space-y-2 mt-4">
                  <h3 className="font-semibold text-gray-300">Receipt</h3>
                  <a href={selectedExpense.receipt_s3_url} target="_blank" rel="noreferrer" className="block w-full h-40 bg-black/50 border border-gray-700 rounded-lg flex flex-col justify-center items-center hover:bg-black/40 transition-colors group">
                    <FileText size={32} className="text-gray-500 group-hover:text-secondary mb-2" />
                    <span className="text-xs text-secondary font-medium">Click to view full receipt</span>
                  </a>
                </div>
              )}
              
              {selectedExpense.approvals && selectedExpense.approvals.length > 0 && (
                <div className="space-y-2 mt-4 text-sm">
                  <h3 className="font-semibold text-gray-300">Approval Chain</h3>
                  <div className="bg-black/30 p-4 rounded-lg border border-white/5 space-y-3">
                    {selectedExpense.approvals.map((appr, idx) => (
                      <div key={idx} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className={`w-3 h-3 rounded-full border-2 border-black ${appr.action === 'APPROVED' ? 'bg-green-500' : appr.action === 'REJECTED' ? 'bg-red-500' : 'bg-gray-500'}`}></div>
                          {idx !== selectedExpense.approvals.length - 1 && <div className="w-px h-full bg-white/10 my-1"></div>}
                        </div>
                        <div className="pb-4">
                          <p className="font-bold text-gray-300">{appr.role_required}</p>
                          <p className="text-xs text-gray-500">{appr.action ? `${appr.action} at ${new Date(appr.acted_at).toLocaleString()}` : 'Pending review'}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
