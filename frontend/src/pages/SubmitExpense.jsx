import React, { useState, useRef } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle, ShieldAlert, Sparkles, Image as ImageIcon } from 'lucide-react';

export default function SubmitExpense() {
  const [formData, setFormData] = useState({ title: '', amount: '', category: 'Travel', date: '', justification: '', receipt_s3_url: '' });
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [receiptFile, setReceiptFile] = useState(null);
  
  const fileInputRef = useRef(null);

  
  const token = useAuthStore(state => state.token);
  const navigate = useNavigate();

  const handleNext = () => setStep(2);
  const handlePrev = () => setStep(1);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setReceiptFile(file);
    setIsUploading(true);

    try {
      // 1. Get Pre-signed URL
      const { data } = await axios.post('/api/upload/presigned-url', {
        filename: file.name,
        file_type: file.type
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const { presigned_post, final_url } = data;

      // 2. Prepare FormData for S3
      const s3FormData = new FormData();
      Object.entries(presigned_post.fields).forEach(([key, value]) => {
        s3FormData.append(key, value);
      });
      s3FormData.append("file", file);

      // 3. Upload to S3 directly
      await axios.post(presigned_post.url, s3FormData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      // 4. Save URL to state
      setFormData(prev => ({ ...prev, receipt_s3_url: final_url }));
    } catch (err) {
      alert("Failed to upload receipt to S3. Policy hook will be bypassed.");
      console.error(err);
      setReceiptFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      // Step 21 Integration: Submit directly triggers backend + ai service
      await axios.post('/api/expenses/', {
        title: formData.title,
        amount: parseFloat(formData.amount),
        category: formData.category,
        expense_date: new Date(formData.date).toISOString(),
        business_justification: formData.justification,
        receipt_s3_url: formData.receipt_s3_url

      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 3000);
    } catch (err) {
      alert("Submission failed. Policy might be violated. Check inputs.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-4 animate-in fade-in zoom-in duration-500">
        <div className="w-24 h-24 rounded-full bg-primary/20 flex items-center justify-center border border-primary/50 shadow-[0_0_50px_rgba(124,58,237,0.3)]">
          <CheckCircle size={48} className="text-primary" />
        </div>
        <h2 className="text-3xl font-bold">Expense Submitted!</h2>
        <p className="text-gray-400">AI rules checked. Soft budget locked. Routing for approvals.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 mt-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-secondary to-primary bg-clip-text text-transparent flex items-center justify-center gap-3">
          <Sparkles className="text-secondary" /> Submit Expense
        </h1>
        <p className="text-gray-400 mt-2">Powered by SpendWise AI Policy Engine</p>
      </div>

      <div className="flex items-center gap-4 mb-8 max-w-sm mx-auto">
        <div className={`h-1 flex-1 rounded-full \${step >= 1 ? 'bg-primary shadow-[0_0_10px_rgba(124,58,237,0.5)]' : 'bg-white/10'}`}></div>
        <div className={`h-1 flex-1 rounded-full \${step >= 2 ? 'bg-secondary shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'bg-white/10'}`}></div>
      </div>

      <form onSubmit={handleSubmit} className="glass-card p-8">
        {step === 1 && (
          <div className="space-y-6 animate-in slide-in-from-left">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Expense Title</label>
              <input type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} required className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" placeholder="e.g. Flight to Mumbai" />
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Amount (₹)</label>
                <input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} required className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono text-xl" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category (Optional: AI can auto-tag)</label>
                <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                  <option value="">Let AI Decide</option>
                  <option value="Travel">Travel</option>
                  <option value="Meals">Meals</option>
                  <option value="Software">Software</option>
                  <option value="Equipment">Equipment</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Date Incurred</label>
              <input type="date" value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} required className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary [color-scheme:dark]" />
            </div>
            
            <button type="button" onClick={handleNext} disabled={!formData.title || !formData.amount || !formData.date} className="w-full bg-gradient-to-r from-primary to-primary/80 hover:from-primary hover:to-primary text-white font-medium p-3 rounded-lg transition-all shadow-lg disabled:opacity-50 mt-8">
              Continue to Details
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6 animate-in slide-in-from-right">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2 flex justify-between">
                <span>Business Justification</span>
                <span className="text-red-400 text-xs flex items-center gap-1"><ShieldAlert size={14}/> Required for off-days</span>
              </label>
              <textarea value={formData.justification} onChange={e => setFormData({...formData, justification: e.target.value})} rows={3} className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-primary font-sans resize-none" placeholder="Provide reason for this expense..." />
            </div>

            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept="image/*,.pdf" 
            />
            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed border-gray-600 rounded-xl p-8 text-center bg-black/30 transition-all cursor-pointer group
                ${isUploading ? 'opacity-50 pointer-events-none' : 'hover:bg-black/40 hover:border-secondary'}
                ${formData.receipt_s3_url ? 'border-green-500 bg-green-500/10' : ''}`}
            >
              {isUploading ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin border-4 border-secondary border-t-transparent rounded-full w-8 h-8 mb-3"></div>
                  <p className="text-sm text-secondary">Uploading directly to S3...</p>
                </div>
              ) : formData.receipt_s3_url ? (
                <div className="flex flex-col items-center">
                  <ImageIcon size={32} className="mx-auto text-green-400 mb-3" />
                  <p className="text-sm text-green-300">Ready: {receiptFile?.name}</p>
                </div>
              ) : (
                <>
                  <UploadCloud size={32} className="mx-auto text-gray-400 group-hover:text-secondary group-hover:animate-bounce mb-3" />
                  <p className="text-sm text-gray-300">Click to Select or Drag & Drop Receipt Image</p>
                  <p className="text-xs text-gray-500 mt-1">S3 Pre-signed upload & Pytesseract OCR will scan this</p>
                </>
              )}
            </div>

            <div className="flex gap-4 pt-4">
              <button type="button" onClick={handlePrev} className="flex-1 bg-white/10 hover:bg-white/20 text-white font-medium p-3 rounded-lg transition-all">
                Back
              </button>
              <button type="submit" disabled={isSubmitting} className="flex-[2] bg-gradient-to-r from-secondary to-blue-500 text-white font-medium p-3 rounded-lg transition-all shadow-[0_0_15px_rgba(6,182,212,0.4)] flex justify-center items-center">
                {isSubmitting ? <span className="animate-spin mr-2 border-2 border-white border-t-transparent rounded-full w-5 h-5"></span> : <Sparkles size={20} className="mr-2" />}
                {isSubmitting ? 'Analyzing & Submitting...' : 'Submit & Run Policy Hook'}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
