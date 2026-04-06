import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LayoutDashboard, Receipt, CheckSquare, BarChart3, Settings, LogOut } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const location = useLocation();

  const userRole = (user?.role || '').toLowerCase();

  const navItems = [
    { label: 'My Expenses', path: '/dashboard', icon: LayoutDashboard, hide: !['employee', 'admin'].includes(userRole) },
    { label: 'Submit Expense', path: '/dashboard/submit', icon: Receipt, hide: !['employee', 'admin'].includes(userRole) },
    { label: 'Approvals', path: '/dashboard/approvals', icon: CheckSquare, hide: !['manager', 'finance', 'senior approver', 'admin'].includes(userRole) },
    { label: 'Finance Risk', path: '/dashboard/finance', icon: BarChart3, hide: !['finance', 'admin'].includes(userRole) },
    { label: 'Admin Panel', path: '/dashboard/admin', icon: Settings, hide: userRole !== 'admin' },
  ].filter(item => !item.hide);

  return (
    <div className="flex h-screen bg-dark text-white overflow-hidden font-sans">
      {/* Sidebar - Glassmorphism style */}
      <aside className="w-64 glass-card m-4 flex flex-col z-20">
        <div className="p-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            SpendWise AI
          </h2>
          <p className="text-sm text-gray-400 mt-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            {user?.name || 'Employee'}
          </p>
          <div className="text-xs text-primary bg-primary/10 px-2 py-1 rounded inline-block mt-2 font-medium">
            Role: {user?.role}
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  active 
                  ? 'bg-gradient-to-r from-primary/20 to-transparent border-l-4 border-primary text-white shadow-[inset_0_0_20px_rgba(124,58,237,0.1)]' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon size={20} className={active ? 'text-primary' : ''} />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <button 
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-400/10 w-full transition-colors"
          >
            <LogOut size={20} />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 relative overflow-y-auto outline-none" tabIndex="-1">
        {/* Decorative background glows */}
        <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-primary/5 rounded-full blur-[120px] pointer-events-none -z-10" />
        <div className="absolute bottom-0 left-1/4 w-1/3 h-1/3 bg-secondary/5 rounded-full blur-[120px] pointer-events-none -z-10" />
        
        <div className="p-8 max-w-7xl mx-auto h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
