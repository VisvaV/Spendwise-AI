import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Layout from './components/Layout';
import EmployeeDashboard from './pages/EmployeeDashboard';
import SubmitExpense from './pages/SubmitExpense';
import ApprovalDashboard from './pages/ApprovalDashboard';
import FinanceDashboard from './pages/FinanceDashboard';
import AdminDashboard from './pages/AdminDashboard';
import { useAuthStore } from './store/authStore';

const APPROVER_ROLES = ['Manager', 'Finance', 'Senior Approver', 'Admin'];
const EMPLOYEE_ONLY_ROLES = ['Employee'];

const ProtectedRoute = ({ children }) => {
  const token = useAuthStore(state => state.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

const RoleRoute = ({ children, allowedRoles }) => {
  const user = useAuthStore(state => state.user);
  if (!user) return <Navigate to="/login" replace />;
  
  const userRole = (user.role || '').toLowerCase();
  const lowerAllowed = allowedRoles.map(r => r.toLowerCase());
  
  if (!lowerAllowed.includes(userRole)) return <Navigate to="/dashboard" replace />;
  return children;
};

// Redirects to the correct dashboard index based on role
const RoleIndex = () => {
  const user = useAuthStore(state => state.user);
  const role = (user?.role || '').toLowerCase();
  
  if (role === 'admin') return <Navigate to="/dashboard/admin" replace />;
  if (role === 'finance') return <Navigate to="/dashboard/finance" replace />;
  if (role === 'manager' || role === 'senior approver') return <Navigate to="/dashboard/approvals" replace />;
  return <EmployeeDashboard />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<RoleIndex />} />
          {/* Employees and Admins can submit expenses */}
          <Route path="submit" element={
            <RoleRoute allowedRoles={['Employee', 'Admin']}>
              <SubmitExpense />
            </RoleRoute>
          } />
          {/* Approvers and Admins */}
          <Route path="approvals" element={
            <RoleRoute allowedRoles={['Manager', 'Finance', 'Senior Approver', 'Admin']}>
              <ApprovalDashboard />
            </RoleRoute>
          } />
          {/* Finance and Admins */}
          <Route path="finance" element={
            <RoleRoute allowedRoles={['Finance', 'Admin']}>
              <FinanceDashboard />
            </RoleRoute>
          } />
          {/* Admins only */}
          <Route path="admin" element={
            <RoleRoute allowedRoles={['Admin']}>
              <AdminDashboard />
            </RoleRoute>
          } />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
