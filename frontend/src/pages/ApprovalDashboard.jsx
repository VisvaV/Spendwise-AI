import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Check, X, ShieldAlert, FileText, Info } from 'lucide-react';

export default function ApprovalDashboard() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const token = useAuthStore(state => state.token);

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        const res = await axios.get('/api/approvals/pending', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setPending(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchApprovals();
  }, [token]);

  const handleAction = async (id, action, note) => {
    try {
      await axios.post(`/api/approvals/${id}/action`, { action, note }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPending(prev => prev.filter(p => p.expense_id !== id));
      setRejectingId(null);
      setRejectReason("");
    } catch (e) {
      alert("Action failed: " + (e?.response?.data?.detail || e.message));
    }
  };

  const handleRequestInfo = async (id) => {
    const info = prompt("What information do you need?");
    if (info) {
      handleAction(id, 'PENDING_INFO', info);
    }
  };

  // Normalize ID to string for safe comparison regardless of API returning number or string
  const startRejecting = (id) => {
    setRejectingId(String(id));
    setRejectReason("");
  };

  const isRejecting = (id) => rejectingId === String(id);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Approval Inbox
        </h1>
        {[1, 2, 3].map(i => (
          <div key={i} className="glass-card p-6 h-32 animate-pulse bg-white/5"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
        Approval Inbox
      </h1>

      <div className="grid gap-6">
        {pending.length === 0 && (
          <p className="text-gray-400">All caught up! No pending approvals.</p>
        )}

        {pending.map(expense => (
          <div
            key={expense.approval_id}
            className="glass-card p-6 flex flex-col md:flex-row justify-between gap-6 transition-all border-l-4 border-l-blue-500"
          >
            {/* Left: Expense Details */}
            <div className="flex-1 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold flex items-center gap-2">
                    {expense.expense_title}
                    {expense.duplicate_flag && (
                      <span className="text-[10px] bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 px-2 py-0.5 rounded uppercase">
                        Possible Duplicate
                      </span>
                    )}
                  </h3>
                  <p className="text-gray-400 text-sm">
                    Submitted by {expense.employee_name} • {expense.expense_date}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-mono text-white tracking-tight">
                    ₹{expense.expense_amount.toLocaleString()}
                  </span>
                  <p className="text-sm text-primary uppercase font-bold">
                    {expense.expense_category}
                  </p>
                </div>
              </div>

              <div className="flex gap-4 p-4 rounded-xl bg-black/40 border border-white/5">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <ShieldAlert
                      size={18}
                      className={expense.risk_score > 0.7 ? "text-red-500" : "text-green-500"}
                    />
                    <span className="text-sm font-medium text-gray-300">
                      AI Risk Score:{" "}
                      <span className={expense.risk_score > 0.7 ? "text-red-400" : "text-green-400"}>
                        {(expense.risk_score * 100).toFixed(0)}/100
                      </span>
                    </span>
                  </div>
                  <div className="flex gap-2 flex-wrap mt-1">
                    {expense.risk_flags && expense.risk_flags.map((flag, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] uppercase bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full"
                      >
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="w-px h-6 bg-white/10 mx-2 self-center"></div>
                {expense.receipt_s3_url && (
                  <button
                    className="text-sm text-secondary flex items-center gap-1 hover:underline self-center"
                    onClick={() => window.open(expense.receipt_s3_url, "_blank")}
                  >
                    <FileText size={16} /> View Receipt
                  </button>
                )}
              </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex flex-col gap-3 justify-center border-t md:border-t-0 md:border-l border-white/10 pt-4 md:pt-0 md:pl-6 min-w-[200px]">
              {isRejecting(expense.expense_id) ? (
                <div className="flex flex-col gap-2">
                  <textarea
                    autoFocus
                    value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)}
                    placeholder="Reason for rejection (min 10 chars)..."
                    className="w-full bg-black/50 border border-gray-700 rounded p-2 text-sm text-white resize-none focus:outline-none focus:border-red-500"
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setRejectingId(null); setRejectReason(""); }}
                      className="flex-1 text-xs text-gray-400 hover:text-white py-1 rounded border border-white/10 hover:border-white/30 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleAction(expense.expense_id, 'REJECTED', rejectReason)}
                      disabled={rejectReason.length < 10}
                      className="flex-[2] bg-red-500 hover:bg-red-600 text-white text-xs py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Confirm Reject
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => handleAction(expense.expense_id, 'APPROVED', "Approved")}
                    className="flex items-center justify-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 border border-green-500/50 py-2 md:py-3 px-6 rounded-lg transition-all font-medium whitespace-nowrap"
                  >
                    <Check size={18} /> Approve
                  </button>
                  <button
                    onClick={() => handleRequestInfo(expense.expense_id)}
                    className="flex items-center justify-center gap-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 border border-yellow-500/50 py-1.5 px-6 rounded-lg transition-all text-sm whitespace-nowrap"
                  >
                    <Info size={16} /> Request Info
                  </button>
                  <button
                    onClick={() => startRejecting(expense.expense_id)}
                    className="flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/50 py-1.5 px-6 rounded-lg transition-all text-sm whitespace-nowrap"
                  >
                    <X size={16} /> Reject
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}