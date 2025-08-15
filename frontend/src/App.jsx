import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Version update to test deployment pipeline
const APP_VERSION = '1.0.1';
import { AuthProvider } from './contexts/AuthContext';
import { DemoProvider } from './contexts/DemoContext';
import { AdminProvider } from './contexts/AdminContext';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Pricing from './pages/Pricing';
import PricingPage from './pages/PricingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Scan from './pages/Scan';
import Reports from './pages/Reports';
import ReportDetail from './pages/ReportDetail';
import Settings from './pages/Settings';
import Documentation from './pages/Documentation';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import SubscriptionManagement from './components/SubscriptionManagement';
import DemoLayout from './components/DemoLayout';
import ProtectedRoute from './components/ProtectedRoute';
import AdminProtectedRoute from './components/AdminProtectedRoute';

function App() {
  // Log version for debugging
  console.log(`CompliantGuard Frontend v${APP_VERSION}`);
  
  return (
    <AdminProvider>
      <DemoProvider>
        <AuthProvider>
          <Router>
            <div className="min-h-screen bg-gray-50">
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Landing />} />
                <Route path="/pricing" element={<PricingPage />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                
                {/* Admin Routes */}
                <Route path="/admin/login" element={<AdminLogin />} />
                <Route path="/admin" element={
                  <AdminProtectedRoute>
                    <AdminDashboard />
                  </AdminProtectedRoute>
                } />
                
                {/* Demo Routes */}
                <Route path="/demo" element={<DemoLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="scan" element={<Scan />} />
                  <Route path="reports" element={<Reports />} />
                  <Route path="reports/:scanId" element={<ReportDetail />} />
                  <Route path="documentation" element={<Documentation />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
                
                {/* Dashboard redirect - redirect to protected app */}
                <Route path="/dashboard" element={<Navigate to="/app" replace />} />
                
                {/* Protected Routes */}
                <Route path="/app" element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }>
                  <Route index element={<Dashboard />} />
                  <Route path="scan" element={<Scan />} />
                  <Route path="reports" element={<Reports />} />
                  <Route path="reports/:scanId" element={<ReportDetail />} />
                  <Route path="documentation" element={<Documentation />} />
                  <Route path="settings" element={<Settings />} />
                  <Route path="subscription" element={<SubscriptionManagement />} />
                </Route>
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </DemoProvider>
    </AdminProvider>
  );
}

export default App;