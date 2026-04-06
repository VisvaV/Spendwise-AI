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

// Redirects to the correct dashboard index based on role
const RoleIndex = () => {
  const user = useAuthStore(state => state.user);
  const role = user?.role;
  if (role === 'Admin') return <Navigate to="/dashboard/admin" replace />;
  if (role === 'Finance') return <Navigate to="/dashboard/finance" replace />;
  if (role === 'Manager' || role === 'Senior Approver') return <Navigate to="/dashboard/approvals" replace />;
  return <EmployeeDashboard />;
};

// Blocks a route if the user's role is not in the allowedRoles list
const RoleRoute = ({ children, allowedRoles }) => {
  const user = useAuthStore(state => state.user);
  if (!user) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<RoleIndex />} />
          {/* Employees only — Admins/Managers/Finance should NOT submit expenses */}
          <Route path="submit" element={
            <RoleRoute allowedRoles={['Employee']}>
              <SubmitExpense />
            </RoleRoute>
          } />
          {/* Approvers */}
          <Route path="approvals" element={
            <RoleRoute allowedRoles={APPROVER_ROLES}>
              <ApprovalDashboard />
            </RoleRoute>
          } />
          {/* Finance */}
          <Route path="finance" element={
            <RoleRoute allowedRoles={['Finance', 'Admin']}>
              <FinanceDashboard />
            </RoleRoute>
          } />
          {/* Admin */}
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
