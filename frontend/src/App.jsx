import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import Settings from './pages/Settings';
import Documentation from './pages/Documentation';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import SubscriptionManagement from './components/SubscriptionManagement';
import DemoLayout from './components/DemoLayout';
import ProtectedRoute from './components/ProtectedRoute';
import AdminProtectedRoute from './components/AdminProtectedRoute';

function App() {
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
                  <Route path="documentation" element={<Documentation />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
                
                {/* Protected Routes */}
                <Route path="/app" element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }>
                  <Route index element={<Dashboard />} />
                  <Route path="scan" element={<Scan />} />
                  <Route path="reports" element={<Reports />} />
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