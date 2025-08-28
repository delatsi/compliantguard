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
      },

      // Comprehensive churn analytics
      churn_analytics: {
        // Current churn metrics
        monthly_churn_rate: 3.2,
        quarterly_churn_rate: 9.1,
        annual_churn_rate: 32.4,
        gross_churn_rate: 3.8,
        net_churn_rate: 1.9,  // Lower due to expansion revenue
        // Churn trends over 6 months
        churn_trend_6_months: [
          {
            month: "Jan",
            churn_rate: 4.1,
            churned_customers: 18,
            expansion_revenue: 12400,
          },
          {
            month: "Feb",
            churn_rate: 3.8,
            churned_customers: 16,
            expansion_revenue: 15200,
          },
          {
            month: "Mar",
            churn_rate: 3.5,
            churned_customers: 15,
            expansion_revenue: 18900,
          },
          {
            month: "Apr",
            churn_rate: 3.2,
            churned_customers: 14,
            expansion_revenue: 21300,
          },
          {
            month: "May",
            churn_rate: 2.9,
            churned_customers: 13,
            expansion_revenue: 23800,
          },
          {
            month: "Jun",
            churn_rate: 3.2,
            churned_customers: 15,
            expansion_revenue: 25100,
          },
        ],
        // Churn by customer segments
        churn_by_plan: {
          starter: 5.8,  // Higher churn for lower-tier plans
          professional: 2.4,  // Mid-tier plans more stable
          enterprise: 0.9,  // Enterprise customers very sticky
        },
        churn_by_industry: {
          healthcare: 2.1,  // Lower churn in healthcare (compliance critical)
          finance: 2.8,  // Moderate churn in finance
          technology: 4.2,  // Higher churn in tech (more options)
          other: 4.8,
        },
        churn_by_customer_age: {
          "0-3_months": 15.2,  // High early churn
          "3-6_months": 8.7,  // Onboarding complete, more stable
          "6-12_months": 4.1,  // Getting value, lower churn
          "12-24_months": 2.3,  // Established customers
          "24+_months": 1.2,  // Long-term loyal customers
        },
        // Churn reasons and patterns
        churn_reasons: [
          { reason: "Price/Budget Constraints", percentage: 28.3, count: 17 },
          { reason: "Lack of Product Adoption", percentage: 22.1, count: 13 },
          { reason: "Competitive Solution", percentage: 18.5, count: 11 },
          { reason: "Internal Tool Development", percentage: 12.4, count: 7 },
          { reason: "Business Change/Closure", percentage: 8.9, count: 5 },
          { reason: "Technical Issues", percentage: 6.2, count: 4 },
          { reason: "Poor Support Experience", percentage: 3.6, count: 2 },
        ],
        voluntary_vs_involuntary: {
          voluntary: 78.5,  // Customer chose to leave
          involuntary: 21.5,  // Payment failures, etc.
        },
        // Early warning indicators
        at_risk_customers: {
          high_risk: 45,  // >70% churn probability
          medium_risk: 123,  // 40-70% churn probability
          low_risk: 234,  // 20-40% churn probability
        },
        engagement_decline_alerts: 28,  // Customers with declining usage
        payment_failure_alerts: 12,  // Failed payment attempts
        support_escalation_alerts: 8,  // Escalated support tickets
        // Cohort retention analysis
        cohort_retention_rates: [
          {
            cohort: "Jan_2023",
            month_1: 95.2,
            month_3: 87.1,
            month_6: 78.9,
            month_12: 68.2,
          },
          {
            cohort: "Feb_2023",
            month_1: 96.1,
            month_3: 88.3,
            month_6: 81.2,
            month_12: 72.1,
          },
          {
            cohort: "Mar_2023",
            month_1: 94.8,
            month_3: 86.9,
            month_6: 79.4,
            month_12: 70.8,
          },
          {
            cohort: "Apr_2023",
            month_1: 95.7,
            month_3: 89.1,
            month_6: 82.3,
            month_12: 74.2,
          },
        ],
        ltv_by_cohort: {
          Q1_2023: 2847.50,
          Q2_2023: 3124.80,
          Q3_2023: 3356.20,
          Q4_2023: 3598.90,
        },
        // Predictive analytics
        predicted_churn_next_30_days: 23,
        predicted_churn_next_90_days: 67,
        churn_risk_score_distribution: {
          "0-20": 832,  // Very low risk
          "20-40": 234,  // Low risk
          "40-60": 123,  // Medium risk
          "60-80": 45,  // High risk
          "80-100": 13,  // Very high risk
        },
        // Financial impact of churn
        lost_revenue_this_month: 47800.00,
        potential_lost_revenue_next_quarter: 142400.00,
        saved_revenue_from_retention_efforts: 89300.00,
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