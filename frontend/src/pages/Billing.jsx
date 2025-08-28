import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { billingAPI } from '../services/api';

const Billing = () => {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPlansAndSubscription();
  }, []);

  const fetchPlansAndSubscription = async () => {
    try {
      setLoading(true);
      const [plansResponse, subscriptionResponse] = await Promise.all([
        billingAPI.getPlans(),
        billingAPI.getSubscription()
      ]);
      
      setPlans(plansResponse.data.plans);
      setCurrentSubscription(subscriptionResponse.data.subscription);
    } catch (err) {
      console.error('Error fetching billing data:', err);
      setError('Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubscription = async (planTier, billingInterval = 'month') => {
    try {
      setCreating(true);
      setError(null);

      // First create a Stripe customer if needed
      const customerResponse = await billingAPI.createCustomer({
        email: user.email,
        company: 'CompliantGuard Customer'
      });

      // Then create the subscription
      const subscriptionResponse = await billingAPI.createSubscription({
        customer_id: customerResponse.data.customer_id,
        plan_tier: planTier,
        billing_interval: billingInterval,
        trial_days: 14
      });

      setCurrentSubscription(subscriptionResponse.data.subscription);
      alert('Subscription created successfully! You have a 14-day free trial.');
      
    } catch (err) {
      console.error('Error creating subscription:', err);
      setError('Failed to create subscription. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleManageBilling = async () => {
    try {
      const response = await billingAPI.createPortalSession({
        return_url: window.location.origin + '/billing'
      });
      
      // Redirect to Stripe billing portal
      window.location.href = response.data.portal_url;
    } catch (err) {
      console.error('Error creating portal session:', err);
      setError('Failed to open billing portal');
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(price);
  };

  const getAnnualSavings = (monthly, annual) => {
    const monthlyCost = monthly * 12;
    const savings = monthlyCost - annual;
    const percentage = Math.round((savings / monthlyCost) * 100);
    return { savings, percentage };
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
          <p className="text-xl text-gray-600">
            Scale your HIPAA compliance with the right plan for your organization
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {currentSubscription && (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-800">
                  Current Plan: {currentSubscription.plan_tier} 
                  {currentSubscription.billing_interval === 'year' ? ' (Annual)' : ' (Monthly)'}
                </h3>
                <p className="text-green-600">
                  Status: {currentSubscription.status}
                  {currentSubscription.status === 'trialing' && (
                    <span className="ml-2 text-sm">
                      (Trial ends {new Date(currentSubscription.trial_end).toLocaleDateString()})
                    </span>
                  )}
                </p>
              </div>
              <button
                onClick={handleManageBilling}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
              >
                Manage Billing
              </button>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {Object.entries(plans).map(([planKey, plan]) => {
            const annualSavings = getAnnualSavings(plan.price_monthly, plan.price_annual);
            const isCurrentPlan = currentSubscription?.plan_tier === plan.tier;

            return (
              <div key={planKey} className={`bg-white rounded-lg shadow-lg overflow-hidden ${
                plan.tier === 'professional' ? 'ring-2 ring-blue-500' : ''
              }`}>
                {plan.tier === 'professional' && (
                  <div className="bg-blue-500 text-white text-center py-2 text-sm font-semibold">
                    Most Popular
                  </div>
                )}
                
                <div className="p-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-6">{plan.description}</p>
                  
                  <div className="mb-6">
                    <div className="flex items-baseline mb-2">
                      <span className="text-3xl font-bold text-gray-900">
                        {formatPrice(plan.price_monthly)}
                      </span>
                      <span className="text-gray-600 ml-1">/month</span>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      or {formatPrice(plan.price_annual)}/year 
                      <span className="text-green-600 font-semibold ml-1">
                        (Save {annualSavings.percentage}%)
                      </span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <svg className="flex-shrink-0 h-5 w-5 text-green-500 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {!isCurrentPlan && !currentSubscription && (
                    <div className="space-y-3">
                      <button
                        onClick={() => handleCreateSubscription(plan.tier, 'month')}
                        disabled={creating}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400"
                      >
                        {creating ? 'Creating...' : 'Start Monthly Plan'}
                      </button>
                      <button
                        onClick={() => handleCreateSubscription(plan.tier, 'year')}
                        disabled={creating}
                        className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition-colors disabled:bg-gray-400"
                      >
                        {creating ? 'Creating...' : 'Start Annual Plan'}
                      </button>
                    </div>
                  )}

                  {isCurrentPlan && (
                    <div className="text-center">
                      <span className="inline-block bg-gray-100 text-gray-700 px-4 py-2 rounded">
                        Current Plan
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Need Enterprise-Grade Compliance?
          </h3>
          <p className="text-gray-600 mb-6">
            Get custom compliance solutions, dedicated support, and volume pricing for your organization.
          </p>
          <button className="bg-gray-900 text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition-colors">
            Contact Sales
          </button>
        </div>

        <div className="mt-12 text-center text-sm text-gray-600">
          <p>
            All plans include a 14-day free trial. No credit card required to start.
            <br />
            Invoices are automatically generated and emailed after each successful payment.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Billing;