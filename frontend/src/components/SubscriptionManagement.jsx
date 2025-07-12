import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  CreditCardIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CurrencyDollarIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const SubscriptionManagement = () => {
  const { user, isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [availablePlans, setAvailablePlans] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [changingPlan, setChangingPlan] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [billingInterval, setBillingInterval] = useState('monthly');

  useEffect(() => {
    if (isAuthenticated) {
      loadSubscriptionData();
    }
  }, [isAuthenticated, loadSubscriptionData]);

  const loadSubscriptionData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load subscription, usage, and available plans in parallel
      const [subResponse, usageResponse, plansResponse] = await Promise.all([
        fetch('/api/v1/billing/subscription', {
          headers: { 'Authorization': `Bearer ${user.token}` }
        }),
        fetch('/api/v1/billing/usage', {
          headers: { 'Authorization': `Bearer ${user.token}` }
        }),
        fetch('/api/v1/billing/plans')
      ]);

      const [subData, usageData, plansData] = await Promise.all([
        subResponse.json(),
        usageResponse.json(),
        plansResponse.json()
      ]);

      setSubscription(subData.subscription);
      setUsage(usageData);
      setAvailablePlans(plansData.plans);
      
    } catch {
      setError('Failed to load subscription data');
      console.error('Subscription data error');
    } finally {
      setLoading(false);
    }
  }, [user]);

  const handleSubscribe = async (planTier, interval = 'monthly') => {
    try {
      setChangingPlan(true);
      
      const response = await fetch('/api/v1/billing/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          plan_tier: planTier,
          billing_interval: interval === 'yearly' ? 'year' : 'month',
          trial_days: 14
        })
      });

      if (response.ok) {
        await loadSubscriptionData();
        setSelectedPlan(null);
      } else {
        throw new Error('Failed to create subscription');
      }
      
    } catch {
      setError('Failed to create subscription');
    } finally {
      setChangingPlan(false);
    }
  };

  const handlePlanChange = async (newPlanTier, newInterval) => {
    try {
      setChangingPlan(true);
      
      const response = await fetch('/api/v1/billing/change-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          customer_id: user.user_id,
          new_plan_tier: newPlanTier,
          new_billing_interval: newInterval === 'yearly' ? 'year' : 'month',
          prorate: true
        })
      });

      if (response.ok) {
        await loadSubscriptionData();
        setSelectedPlan(null);
      } else {
        throw new Error('Failed to change subscription');
      }
      
    } catch {
      setError('Failed to change subscription');
    } finally {
      setChangingPlan(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will continue to have access until the end of your billing period.')) {
      return;
    }
    
    try {
      const response = await fetch('/api/v1/billing/cancel-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          cancel_immediately: false
        })
      });

      if (response.ok) {
        await loadSubscriptionData();
      } else {
        throw new Error('Failed to cancel subscription');
      }
      
    } catch {
      setError('Failed to cancel subscription');
    }
  };

  const openBillingPortal = async () => {
    try {
      const response = await fetch('/api/v1/billing/portal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          return_url: window.location.href
        })
      });

      const data = await response.json();
      if (response.ok && data.portal_url) {
        window.open(data.portal_url, '_blank');
      }
      
    } catch {
      setError('Failed to open billing portal');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getUsagePercentage = (used, limit) => {
    if (!limit) return 0; // Unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
        <p className="text-center mt-4 text-gray-600">Loading subscription...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Subscription & Billing</h1>
        <p className="mt-2 text-gray-600">Manage your ThemisGuard subscription and monitor usage</p>
      </div>

      {/* Current Subscription Status */}
      {subscription ? (
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Current Subscription</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Plan</h3>
                <p className="mt-1 text-2xl font-semibold text-gray-900">
                  {subscription.plan.name}
                </p>
                <p className="text-sm text-gray-600">{subscription.plan.description}</p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500">Status</h3>
                <div className="mt-1 flex items-center">
                  <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    subscription.status === 'active' ? 'bg-green-100 text-green-800' :
                    subscription.status === 'trialing' ? 'bg-blue-100 text-blue-800' :
                    subscription.status === 'past_due' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500">
                  {subscription.billing_interval === 'year' ? 'Annual' : 'Monthly'} Cost
                </h3>
                <p className="mt-1 text-2xl font-semibold text-gray-900">
                  {formatCurrency(
                    subscription.billing_interval === 'year' 
                      ? subscription.plan.price_annual 
                      : subscription.plan.price_monthly
                  )}
                  <span className="text-sm text-gray-600">
                    /{subscription.billing_interval === 'year' ? 'year' : 'month'}
                  </span>
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Current Period</h3>
                <p className="mt-1 text-sm text-gray-900">
                  {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
                </p>
                {subscription.trial_end && new Date(subscription.trial_end) > new Date() && (
                  <p className="text-sm text-blue-600">
                    Trial ends: {formatDate(subscription.trial_end)}
                  </p>
                )}
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={openBillingPortal}
                  className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700"
                >
                  Manage Billing
                </button>
                <button
                  onClick={() => setSelectedPlan('change')}
                  className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700"
                >
                  Change Plan
                </button>
                <button
                  onClick={handleCancelSubscription}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* No Subscription - Show Plans */
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Choose Your Plan</h2>
            <p className="text-sm text-gray-600">Start your 14-day free trial</p>
          </div>
          <div className="p-6">
            <div className="mb-4 flex justify-center">
              <div className="bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setBillingInterval('monthly')}
                  className={`px-4 py-2 text-sm font-medium rounded-md ${
                    billingInterval === 'monthly'
                      ? 'bg-white text-gray-900 shadow'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBillingInterval('yearly')}
                  className={`px-4 py-2 text-sm font-medium rounded-md ${
                    billingInterval === 'yearly'
                      ? 'bg-white text-gray-900 shadow'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Yearly (Save 17%)
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(availablePlans).map(([tier, plan]) => (
                <div key={tier} className="border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900">{plan.name}</h3>
                  <p className="mt-2 text-sm text-gray-600">{plan.description}</p>
                  <div className="mt-4">
                    <span className="text-3xl font-bold text-gray-900">
                      {formatCurrency(
                        billingInterval === 'yearly' ? plan.price_annual / 12 : plan.price_monthly
                      )}
                    </span>
                    <span className="text-sm text-gray-600">/month</span>
                    {billingInterval === 'yearly' && (
                      <p className="text-sm text-gray-600">
                        Billed annually: {formatCurrency(plan.price_annual)}
                      </p>
                    )}
                  </div>
                  <ul className="mt-6 space-y-3">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => handleSubscribe(tier, billingInterval)}
                    disabled={changingPlan}
                    className="mt-6 w-full bg-red-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                  >
                    {changingPlan ? 'Processing...' : 'Start Free Trial'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Usage Monitoring */}
      {subscription && usage && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Usage This Month</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Scans Usage */}
              <div>
                <h3 className="text-sm font-medium text-gray-500">Scans</h3>
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-semibold text-gray-900">
                      {usage.usage.scans_count}
                    </span>
                    <span className="text-sm text-gray-600">
                      {subscription.plan.scan_limit ? `/ ${subscription.plan.scan_limit}` : '/ Unlimited'}
                    </span>
                  </div>
                  {subscription.plan.scan_limit && (
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getUsageColor(getUsagePercentage(usage.usage.scans_count, subscription.plan.scan_limit))}`}
                        style={{ width: `${getUsagePercentage(usage.usage.scans_count, subscription.plan.scan_limit)}%` }}
                      ></div>
                    </div>
                  )}
                </div>
              </div>

              {/* Projects Usage */}
              <div>
                <h3 className="text-sm font-medium text-gray-500">Projects</h3>
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-semibold text-gray-900">
                      {usage.usage.projects_scanned}
                    </span>
                    <span className="text-sm text-gray-600">
                      {subscription.plan.project_limit ? `/ ${subscription.plan.project_limit}` : '/ Unlimited'}
                    </span>
                  </div>
                  {subscription.plan.project_limit && (
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getUsageColor(getUsagePercentage(usage.usage.projects_scanned, subscription.plan.project_limit))}`}
                        style={{ width: `${getUsagePercentage(usage.usage.projects_scanned, subscription.plan.project_limit)}%` }}
                      ></div>
                    </div>
                  )}
                </div>
              </div>

              {/* API Calls */}
              <div>
                <h3 className="text-sm font-medium text-gray-500">API Calls</h3>
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-semibold text-gray-900">
                      {usage.usage.api_calls}
                    </span>
                    <span className="text-sm text-gray-600">
                      {subscription.plan.api_access ? '/ Unlimited' : '/ Not Available'}
                    </span>
                  </div>
                  {!subscription.plan.api_access && (
                    <p className="mt-1 text-xs text-gray-500">
                      Upgrade to Professional for API access
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Usage Limits Warning */}
            {usage.limits_check && !usage.limits_check.within_limits && (
              <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">Usage Limit Warning</h3>
                    <p className="mt-1 text-sm text-yellow-700">{usage.limits_check.reason}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Plan Change Modal */}
      {selectedPlan === 'change' && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Change Your Plan</h3>
              
              <div className="mb-4 flex justify-center">
                <div className="bg-gray-100 p-1 rounded-lg">
                  <button
                    onClick={() => setBillingInterval('monthly')}
                    className={`px-4 py-2 text-sm font-medium rounded-md ${
                      billingInterval === 'monthly'
                        ? 'bg-white text-gray-900 shadow'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Monthly
                  </button>
                  <button
                    onClick={() => setBillingInterval('yearly')}
                    className={`px-4 py-2 text-sm font-medium rounded-md ${
                      billingInterval === 'yearly'
                        ? 'bg-white text-gray-900 shadow'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Yearly (Save 17%)
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {Object.entries(availablePlans).map(([tier, plan]) => (
                  <div key={tier} className={`border rounded-lg p-4 ${
                    subscription?.plan.tier === tier ? 'border-red-500 bg-red-50' : 'border-gray-200'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{plan.name}</h4>
                        <p className="text-sm text-gray-600">
                          {formatCurrency(
                            billingInterval === 'yearly' ? plan.price_annual / 12 : plan.price_monthly
                          )}/month
                        </p>
                      </div>
                      <div>
                        {subscription?.plan.tier === tier ? (
                          <span className="text-sm text-red-600 font-medium">Current Plan</span>
                        ) : (
                          <button
                            onClick={() => handlePlanChange(tier, billingInterval)}
                            disabled={changingPlan}
                            className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                          >
                            {changingPlan ? 'Processing...' : 'Switch to this plan'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setSelectedPlan(null)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubscriptionManagement;