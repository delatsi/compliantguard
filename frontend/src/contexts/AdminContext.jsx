import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AdminContext = createContext();

// eslint-disable-next-line react-refresh/only-export-components
export const useAdmin = () => {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error('useAdmin must be used within an AdminProvider');
  }
  return context;
};

export const AdminProvider = ({ children }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminUser, setAdminUser] = useState(null);
  const [is2FAVerified, setIs2FAVerified] = useState(false);
  const [adminToken, setAdminToken] = useState(null);

  const validateAdminSession = useCallback(async (token) => {
    try {
      // In real implementation, this would validate with backend
      // For demo purposes, we'll simulate admin validation
      if (token === 'admin_demo_token_12345') {
        setIsAdmin(true);
        setIs2FAVerified(true);
        setAdminToken(token);
        setAdminUser({
          id: 'admin-001',
          email: 'admin@themisguard.com',
          name: 'System Administrator',
          role: 'super_admin',
          lastLogin: new Date().toISOString(),
          permissions: [
            'view_customers',
            'view_revenue',
            'view_analytics',
            'manage_subscriptions',
            'view_system_health'
          ]
        });
      }
    } catch {
      console.error('Admin session validation failed');
      logoutAdmin();
    }
  }, []);

  // Check admin session on component mount
  useEffect(() => {
    const storedAdminToken = localStorage.getItem('admin_token');
    const stored2FA = localStorage.getItem('admin_2fa_verified');
    
    if (storedAdminToken && stored2FA === 'true') {
      // Verify token is still valid (in real app, this would call API)
      validateAdminSession(storedAdminToken);
    }
  }, [validateAdminSession]);

  const loginAdmin = async (credentials) => {
    try {
      // Simulate admin login API call
      const { email, password } = credentials;
      
      // Demo admin credentials
      if (email === 'admin@themisguard.com' && password === 'SecureAdmin123!') {
        // Simulate successful login but require 2FA
        return {
          success: true,
          requires2FA: true,
          tempToken: 'temp_admin_token_67890'
        };
      } else {
        return {
          success: false,
          error: 'Invalid admin credentials'
        };
      }
    } catch {
      return {
        success: false,
        error: 'Login failed. Please try again.'
      };
    }
  };

  const verify2FA = async (tempToken, twoFactorCode) => {
    try {
      // Simulate 2FA verification
      // In real implementation, this would verify TOTP/SMS code
      if (tempToken === 'temp_admin_token_67890' && twoFactorCode === '123456') {
        const adminToken = 'admin_demo_token_12345';
        
        setIsAdmin(true);
        setIs2FAVerified(true);
        setAdminToken(adminToken);
        setAdminUser({
          id: 'admin-001',
          email: 'admin@themisguard.com',
          name: 'System Administrator',
          role: 'super_admin',
          lastLogin: new Date().toISOString(),
          permissions: [
            'view_customers',
            'view_revenue',
            'view_analytics',
            'manage_subscriptions',
            'view_system_health'
          ]
        });

        // Store admin session
        localStorage.setItem('admin_token', adminToken);
        localStorage.setItem('admin_2fa_verified', 'true');

        return { success: true };
      } else {
        return {
          success: false,
          error: 'Invalid 2FA code'
        };
      }
    } catch {
      return {
        success: false,
        error: '2FA verification failed'
      };
    }
  };

  const logoutAdmin = () => {
    setIsAdmin(false);
    setAdminUser(null);
    setIs2FAVerified(false);
    setAdminToken(null);
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_2fa_verified');
  };

  const hasPermission = (permission) => {
    return adminUser?.permissions?.includes(permission) || false;
  };

  // Admin demo data - aggregated, non-sensitive metrics only
  const getAdminDashboardData = () => {
    return {
      // Customer metrics (aggregated, no PII)
      customerMetrics: {
        totalCustomers: 1247,
        activeCustomers: 1103,
        newCustomersThisMonth: 89,
        churnRate: 3.2,
        customersByPlan: {
          starter: 456,
          professional: 623,
          enterprise: 168
        },
        customersByIndustry: {
          healthcare: 489,
          finance: 312,
          technology: 287,
          other: 159
        }
      },

      // Revenue metrics (aggregated)
      revenueMetrics: {
        monthlyRecurringRevenue: 187420,
        annualRecurringRevenue: 2249040,
        revenueGrowthRate: 23.4,
        averageRevenuePerUser: 169.89,
        monthlyRevenue: [
          { month: 'Jan', revenue: 156890 },
          { month: 'Feb', revenue: 163420 },
          { month: 'Mar', revenue: 171230 },
          { month: 'Apr', revenue: 178910 },
          { month: 'May', revenue: 184560 },
          { month: 'Jun', revenue: 187420 }
        ],
        revenueByPlan: {
          starter: 22800,  // 456 * $50
          professional: 124600, // 623 * $200
          enterprise: 40320   // 168 * $240
        }
      },

      // Usage metrics (aggregated)
      usageMetrics: {
        totalScans: 45789,
        scansThisMonth: 8934,
        averageScansPerCustomer: 36.7,
        totalViolationsFound: 123456,
        averageComplianceScore: 84.3,
        popularFeatures: [
          { feature: 'HIPAA Compliance Scanning', usage: 89 },
          { feature: 'SOC 2 Reports', usage: 67 },
          { feature: 'Environment Separation', usage: 54 },
          { feature: 'Custom Policies', usage: 43 }
        ]
      },

      // System health (operational metrics)
      systemHealth: {
        apiUptime: 99.97,
        averageResponseTime: 245,
        errorRate: 0.12,
        activeScans: 23,
        queuedScans: 7,
        systemAlerts: 2
      },

      // Support metrics
      supportMetrics: {
        openTickets: 34,
        averageResolutionTime: 4.2,
        customerSatisfactionScore: 4.6,
        escalatedTickets: 3
      }
    };
  };

  const value = {
    // Admin authentication state
    isAdmin,
    adminUser,
    is2FAVerified,
    adminToken,

    // Admin authentication methods
    loginAdmin,
    verify2FA,
    logoutAdmin,
    hasPermission,

    // Admin data access
    getAdminDashboardData
  };

  return (
    <AdminContext.Provider value={value}>
      {children}
    </AdminContext.Provider>
  );
};

export default AdminProvider;