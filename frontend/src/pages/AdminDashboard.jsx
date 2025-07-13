import React, { useState, useEffect, useCallback } from 'react';
import { useAdmin } from '../contexts/AdminContext';
import {
  UsersIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ShieldCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const AdminDashboard = () => {
  const { adminUser, hasPermission, getAdminDashboardData, logoutAdmin } = useAdmin();
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [selectedTimeRange, loadDashboardData]);

  const loadDashboardData = useCallback(async () => {
    setRefreshing(true);
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      const data = getAdminDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setRefreshing(false);
    }
  }, [selectedTimeRange]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (number) => {
    return new Intl.NumberFormat('en-US').format(number);
  };

  const formatPercentage = (percentage) => {
    return `${percentage.toFixed(1)}%`;
  };

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-red-600 rounded-lg flex items-center justify-center mr-3">
                <ShieldCheckIcon className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ThemisGuard Admin</h1>
                <p className="text-sm text-gray-500">System Administration Portal</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-red-500 focus:border-red-500"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
              </select>

              <button
                onClick={loadDashboardData}
                disabled={refreshing}
                className="bg-white border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>

              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <span>{adminUser?.name}</span>
                <button
                  onClick={logoutAdmin}
                  className="text-red-600 hover:text-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Security Notice */}
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Data Privacy Notice
              </h3>
              <p className="mt-1 text-sm text-red-700">
                This dashboard displays aggregated business metrics only. No customer PII or sensitive data is shown. 
                All access is logged and monitored for security compliance.
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Customers */}
          {hasPermission('view_customers') && (
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UsersIcon className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Customers
                      </dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {formatNumber(dashboardData.customerMetrics.totalCustomers)}
                        </div>
                        <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                          <ArrowUpIcon className="h-3 w-3 flex-shrink-0 self-center" />
                          <span className="sr-only">Increased by</span>
                          7.2%
                        </div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-500">Active: </span>
                  <span className="font-medium text-gray-900">
                    {formatNumber(dashboardData.customerMetrics.activeCustomers)}
                  </span>
                  <span className="text-gray-500"> ({formatPercentage(
                    (dashboardData.customerMetrics.activeCustomers / dashboardData.customerMetrics.totalCustomers) * 100
                  )})</span>
                </div>
              </div>
            </div>
          )}

          {/* Monthly Recurring Revenue */}
          {hasPermission('view_revenue') && (
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CurrencyDollarIcon className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Monthly Recurring Revenue
                      </dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {formatCurrency(dashboardData.revenueMetrics.monthlyRecurringRevenue)}
                        </div>
                        <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                          <ArrowUpIcon className="h-3 w-3 flex-shrink-0 self-center" />
                          <span className="sr-only">Increased by</span>
                          {formatPercentage(dashboardData.revenueMetrics.revenueGrowthRate)}
                        </div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-500">ARR: </span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(dashboardData.revenueMetrics.annualRecurringRevenue)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* System Health */}
          {hasPermission('view_system_health') && (
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ServerIcon className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        System Uptime
                      </dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {formatPercentage(dashboardData.systemHealth.apiUptime)}
                        </div>
                        <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                          <CheckCircleIcon className="h-3 w-3 flex-shrink-0 self-center" />
                          <span className="sr-only">Healthy</span>
                          Healthy
                        </div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-500">Avg Response: </span>
                  <span className="font-medium text-gray-900">
                    {dashboardData.systemHealth.averageResponseTime}ms
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Usage Analytics */}
          {hasPermission('view_analytics') && (
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <ChartBarIcon className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Scans
                      </dt>
                      <dd className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {formatNumber(dashboardData.usageMetrics.totalScans)}
                        </div>
                        <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                          <ArrowUpIcon className="h-3 w-3 flex-shrink-0 self-center" />
                          <span className="sr-only">Increased by</span>
                          12.3%
                        </div>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-500">This month: </span>
                  <span className="font-medium text-gray-900">
                    {formatNumber(dashboardData.usageMetrics.scansThisMonth)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Churn Analytics Section */}
        {hasPermission('view_customers') && (
          <div className="mb-8">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Churn Analytics & Predictions</h3>
                <p className="text-sm text-gray-500">Customer retention insights and early warning indicators</p>
              </div>
              <div className="p-6">
                {/* Churn Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-red-600">Monthly Churn Rate</div>
                    <div className="text-2xl font-bold text-red-700">{formatPercentage(dashboardData.churn_analytics.monthly_churn_rate)}</div>
                    <div className="text-xs text-red-500">
                      Net: {formatPercentage(dashboardData.churn_analytics.net_churn_rate)}
                    </div>
                  </div>
                  
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-yellow-600">At-Risk Customers</div>
                    <div className="text-2xl font-bold text-yellow-700">
                      {formatNumber(dashboardData.churn_analytics.at_risk_customers.high_risk + dashboardData.churn_analytics.at_risk_customers.medium_risk)}
                    </div>
                    <div className="text-xs text-yellow-500">
                      High Risk: {dashboardData.churn_analytics.at_risk_customers.high_risk}
                    </div>
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-blue-600">Predicted Churn (30d)</div>
                    <div className="text-2xl font-bold text-blue-700">
                      {formatNumber(dashboardData.churn_analytics.predicted_churn_next_30_days)}
                    </div>
                    <div className="text-xs text-blue-500">
                      90d: {dashboardData.churn_analytics.predicted_churn_next_90_days}
                    </div>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-sm font-medium text-green-600">Revenue Saved</div>
                    <div className="text-2xl font-bold text-green-700">
                      {formatCurrency(dashboardData.churn_analytics.saved_revenue_from_retention_efforts)}
                    </div>
                    <div className="text-xs text-green-500">This month</div>
                  </div>
                </div>

                {/* Churn Trends Chart */}
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">6-Month Churn Trend</h4>
                  <div className="space-y-2">
                    {dashboardData.churn_analytics.churn_trend_6_months.map((month) => (
                      <div key={month.month} className="flex items-center justify-between py-2">
                        <span className="text-sm font-medium text-gray-900 w-12">{month.month}</span>
                        <div className="flex items-center space-x-4 flex-1">
                          <div className="flex items-center space-x-2 w-32">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-red-500 h-2 rounded-full" 
                                style={{ width: `${(month.churn_rate / 5) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-red-600 w-8">{month.churn_rate}%</span>
                          </div>
                          <span className="text-sm text-gray-600 w-20">{month.churned_customers} lost</span>
                          <span className="text-sm text-green-600">+{formatCurrency(month.expansion_revenue)} expansion</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Churn by Segment */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Churn Rate by Plan</h4>
                    <div className="space-y-2">
                      {Object.entries(dashboardData.churn_analytics.churn_by_plan).map(([plan, rate]) => (
                        <div key={plan} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 capitalize">{plan}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-orange-500 h-2 rounded-full" 
                                style={{ width: `${(rate / 6) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-8">{rate}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Top Churn Reasons</h4>
                    <div className="space-y-2">
                      {dashboardData.churn_analytics.churn_reasons.slice(0, 4).map((reason) => (
                        <div key={reason.reason} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 truncate">{reason.reason}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-purple-500 h-2 rounded-full" 
                                style={{ width: `${reason.percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-8">{reason.percentage.toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Revenue Chart */}
          {hasPermission('view_revenue') && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Revenue Trends</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {dashboardData.revenueMetrics.monthlyRevenue.map((month, index) => (
                    <div key={month.month} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">{month.month}</span>
                      <div className="flex items-center space-x-3">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ 
                              width: `${(month.revenue / Math.max(...dashboardData.revenueMetrics.monthlyRevenue.map(m => m.revenue))) * 100}%` 
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900 w-20 text-right">
                          {formatCurrency(month.revenue)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Customer Distribution */}
          {hasPermission('view_customers') && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Customer Distribution</h3>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">By Plan</h4>
                    <div className="space-y-2">
                      {Object.entries(dashboardData.customerMetrics.customersByPlan).map(([plan, count]) => (
                        <div key={plan} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 capitalize">{plan}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ 
                                  width: `${(count / dashboardData.customerMetrics.totalCustomers) * 100}%` 
                                }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-12 text-right">
                              {formatNumber(count)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">By Industry</h4>
                    <div className="space-y-2">
                      {Object.entries(dashboardData.customerMetrics.customersByIndustry).map(([industry, count]) => (
                        <div key={industry} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 capitalize">{industry}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-purple-600 h-2 rounded-full" 
                                style={{ 
                                  width: `${(count / dashboardData.customerMetrics.totalCustomers) * 100}%` 
                                }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-12 text-right">
                              {formatNumber(count)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Cohort Analysis and Early Warning Indicators */}
        {hasPermission('view_customers') && (
          <div className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Cohort Retention */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Cohort Retention Analysis</h3>
                <p className="text-sm text-gray-500">Customer retention by signup cohort</p>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {dashboardData.churn_analytics.cohort_retention_rates.slice(0, 4).map((cohort, index) => (
                    <div key={cohort.cohort} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">{cohort.cohort} Cohort</span>
                        <span className="text-xs text-gray-500">
                          LTV: {formatCurrency(dashboardData.churn_analytics.ltv_by_cohort[`Q${Math.floor(index/3) + 1}_2023`] || 0)}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div className="text-center">
                          <div className="text-gray-500">Month 1</div>
                          <div className="font-medium text-green-600">{cohort.month_1}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-gray-500">Month 3</div>
                          <div className="font-medium text-yellow-600">{cohort.month_3}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-gray-500">Month 6</div>
                          <div className="font-medium text-orange-600">{cohort.month_6}%</div>
                        </div>
                        <div className="text-center">
                          <div className="text-gray-500">Month 12</div>
                          <div className="font-medium text-red-600">{cohort.month_12}%</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Early Warning Indicators */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Early Warning Indicators</h3>
                <p className="text-sm text-gray-500">Proactive churn prevention alerts</p>
              </div>
              <div className="p-6 space-y-4">
                {/* Risk Distribution */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Customer Risk Distribution</h4>
                  <div className="space-y-2">
                    {Object.entries(dashboardData.churn_analytics.churn_risk_score_distribution).map(([range, count]) => (
                      <div key={range} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{range}% risk</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                range.startsWith('80') ? 'bg-red-500' :
                                range.startsWith('60') ? 'bg-orange-500' :
                                range.startsWith('40') ? 'bg-yellow-500' :
                                range.startsWith('20') ? 'bg-blue-500' :
                                'bg-green-500'
                              }`}
                              style={{ width: `${(count / 1000) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-gray-900 w-8">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Alert Summary */}
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Active Alerts</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <span className="text-sm text-red-700">Engagement Decline</span>
                      <span className="text-sm font-medium text-red-900">
                        {dashboardData.churn_analytics.engagement_decline_alerts}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-yellow-50 rounded">
                      <span className="text-sm text-yellow-700">Payment Failures</span>
                      <span className="text-sm font-medium text-yellow-900">
                        {dashboardData.churn_analytics.payment_failure_alerts}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-orange-50 rounded">
                      <span className="text-sm text-orange-700">Support Escalations</span>
                      <span className="text-sm font-medium text-orange-900">
                        {dashboardData.churn_analytics.support_escalation_alerts}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Financial Impact */}
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Financial Impact</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Lost Revenue (This Month)</span>
                      <span className="font-medium text-red-600">
                        -{formatCurrency(dashboardData.churn_analytics.lost_revenue_this_month)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Potential Loss (Next Quarter)</span>
                      <span className="font-medium text-orange-600">
                        -{formatCurrency(dashboardData.churn_analytics.potential_lost_revenue_next_quarter)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Revenue Saved</span>
                      <span className="font-medium text-green-600">
                        +{formatCurrency(dashboardData.churn_analytics.saved_revenue_from_retention_efforts)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* System Health and Support */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* System Health Details */}
          {hasPermission('view_system_health') && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">System Health</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">API Uptime</span>
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium">{formatPercentage(dashboardData.systemHealth.apiUptime)}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Error Rate</span>
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium">{formatPercentage(dashboardData.systemHealth.errorRate)}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Active Scans</span>
                    <span className="text-sm font-medium">{dashboardData.systemHealth.activeScans}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Queued Scans</span>
                    <span className="text-sm font-medium">{dashboardData.systemHealth.queuedScans}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">System Alerts</span>
                    <div className="flex items-center space-x-2">
                      {dashboardData.systemHealth.systemAlerts > 0 ? (
                        <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      )}
                      <span className="text-sm font-medium">{dashboardData.systemHealth.systemAlerts}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Feature Usage */}
          {hasPermission('view_analytics') && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Popular Features</h3>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {dashboardData.usageMetrics.popularFeatures.map((feature, index) => (
                    <div key={feature.feature} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{feature.feature}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full" 
                            style={{ width: `${feature.usage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900 w-8 text-right">
                          {feature.usage}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;