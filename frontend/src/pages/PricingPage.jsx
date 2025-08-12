import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircleIcon,
  XMarkIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

const PricingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [billingInterval, setBillingInterval] = useState('monthly');

  // Updated pricing plans
  const availablePlans = {
    free: {
      name: 'Free',
      price_monthly: 0,
      price_annual: 0,
      description: 'Perfect for getting started with basic compliance scanning',
      features: [
        'Up to 5 scans per month',
        'Basic HIPAA compliance checks',
        'Email support',
        'Standard reports',
        'Public cloud scanning (GCP, AWS)',
        'Basic dashboard'
      ],
      limitations: [
        'No ML-powered insights',
        'No custom policies',
        'No priority support'
      ],
      cta: 'Get Started Free',
      popular: false
    },
    starter: {
      name: 'Starter',
      price_monthly: 49,
      price_annual: 490, // ~17% savings (49*12 = 588, so 490 is about 17% off)
      description: 'Ideal for small teams and growing organizations',
      features: [
        'Up to 50 scans per month',
        'Full HIPAA & SOC 2 compliance',
        'Priority email support',
        'Advanced reporting & analytics',
        'Multi-cloud scanning',
        'Custom compliance policies',
        'API access',
        'Team collaboration (up to 5 users)'
      ],
      limitations: [
        'No ML-powered risk assessment',
        'No automated remediation suggestions'
      ],
      cta: 'Start Free Trial',
      popular: true
    },
    pro: {
      name: 'Pro',
      price_monthly: 99,
      price_annual: 990, // ~17% savings
      description: 'Advanced features for enterprise security teams',
      features: [
        'Unlimited scans',
        'All compliance frameworks (HIPAA, SOC 2, PCI DSS, GDPR)',
        'Phone & chat support',
        'ML-powered risk assessment',
        'Automated remediation suggestions',
        'Custom integrations',
        'Advanced API with webhooks',
        'Unlimited team members',
        'White-label reporting',
        'Dedicated account manager',
        'SSO integration'
      ],
      limitations: [],
      cta: 'Start Free Trial',
      popular: false
    }
  };

  const handleGetStarted = (planTier) => {
    if (!isAuthenticated) {
      // Redirect to login with plan selection
      navigate('/login', { state: { selectedPlan: planTier, billingInterval } });
    } else {
      // Redirect to subscription management
      navigate('/dashboard/subscription', { state: { selectedPlan: planTier, billingInterval } });
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getYearlySavings = (monthly, yearly) => {
    if (monthly === 0) return { savings: 0, percentage: 0 }; // Free plan
    const monthlyTotal = monthly * 12;
    const savings = monthlyTotal - yearly;
    const percentage = Math.round((savings / monthlyTotal) * 100);
    return { savings, percentage };
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
              Simple, transparent pricing
            </h1>
            <p className="mt-4 text-xl text-gray-600">
              Choose the plan that's right for your team. Start with a 14-day free trial.
            </p>
          </div>

          {/* Billing Toggle */}
          <div className="mt-8 flex justify-center">
            <div className="bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setBillingInterval('monthly')}
                className={`px-6 py-2 text-sm font-medium rounded-md transition-colors ${
                  billingInterval === 'monthly'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Monthly billing
              </button>
              <button
                onClick={() => setBillingInterval('yearly')}
                className={`px-6 py-2 text-sm font-medium rounded-md transition-colors ${
                  billingInterval === 'yearly'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Annual billing
                <span className="ml-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Save 17%
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {Object.entries(availablePlans).map(([tier, plan]) => {
            const isPopular = plan.popular;
            const price = billingInterval === 'yearly' ? plan.price_annual / 12 : plan.price_monthly;
            const yearlyPrice = plan.price_annual;
            const yearlySavings = getYearlySavings(plan.price_monthly, plan.price_annual);

            return (
              <div
                key={tier}
                className={`relative rounded-lg shadow-lg overflow-hidden ${
                  isPopular 
                    ? 'border-2 border-red-500 transform scale-105'
                    : 'border border-gray-200'
                }`}
              >
                {isPopular && (
                  <div className="absolute top-0 left-0 right-0 bg-red-500 text-white text-center py-2 text-sm font-medium">
                    Most Popular
                  </div>
                )}
                
                <div className={`bg-white px-6 ${isPopular ? 'pt-8 pb-6' : 'py-6'}`}>
                  <div className="text-center">
                    <h3 className="text-2xl font-semibold text-gray-900">{plan.name}</h3>
                    <p className="mt-2 text-gray-600">{plan.description}</p>
                    
                    <div className="mt-6">
                      <span className="text-4xl font-extrabold text-gray-900">
                        {formatCurrency(price)}
                      </span>
                      <span className="text-base font-medium text-gray-500">/month</span>
                      
                      {billingInterval === 'yearly' && yearlyPrice > 0 && (
                        <div className="mt-1">
                          <p className="text-sm text-gray-600">
                            {formatCurrency(yearlyPrice)} billed annually
                          </p>
                          {yearlySavings.percentage > 0 && (
                            <p className="text-sm text-green-600 font-medium">
                              Save {formatCurrency(yearlySavings.savings)} ({yearlySavings.percentage}%)
                            </p>
                          )}
                        </div>
                      )}
                      {tier === 'free' && (
                        <div className="mt-1">
                          <p className="text-sm text-green-600 font-medium">
                            Forever free
                          </p>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleGetStarted(tier)}
                      className={`mt-6 w-full py-3 px-6 border border-transparent rounded-md text-center text-base font-medium transition-colors ${
                        isPopular
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : tier === 'free'
                          ? 'bg-green-600 text-white hover:bg-green-700'
                          : 'bg-gray-800 text-white hover:bg-gray-900'
                      }`}
                    >
                      {plan.cta}
                      <ArrowRightIcon className="ml-2 h-4 w-4 inline" />
                    </button>
                  </div>
                </div>

                <div className="bg-gray-50 px-6 py-8">
                  <h4 className="text-sm font-medium text-gray-900 uppercase tracking-wide">
                    What's included
                  </h4>
                  <ul className="mt-4 space-y-3">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Plan Limitations */}
                  {plan.limitations && plan.limitations.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <h5 className="text-xs font-medium text-gray-900 uppercase tracking-wide">
                        Limitations
                      </h5>
                      <ul className="mt-3 space-y-2">
                        {plan.limitations.map((limitation, index) => (
                          <li key={index} className="flex items-start">
                            <XMarkIcon className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                            <span className="text-sm text-gray-600">{limitation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-20">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-extrabold text-gray-900 text-center">
              Frequently asked questions
            </h2>
            <div className="mt-12 divide-y divide-gray-200">
              <div className="py-6">
                <h3 className="text-lg font-medium text-gray-900">
                  How does the free trial work?
                </h3>
                <p className="mt-2 text-gray-600">
                  Start with any plan and get 14 days completely free. No credit card required. 
                  You can cancel anytime during the trial period.
                </p>
              </div>
              
              <div className="py-6">
                <h3 className="text-lg font-medium text-gray-900">
                  Can I change plans later?
                </h3>
                <p className="mt-2 text-gray-600">
                  Yes, you can upgrade or downgrade your plan at any time. Changes take effect 
                  immediately with prorated billing.
                </p>
              </div>
              
              <div className="py-6">
                <h3 className="text-lg font-medium text-gray-900">
                  What payment methods do you accept?
                </h3>
                <p className="mt-2 text-gray-600">
                  We accept all major credit cards (Visa, MasterCard, American Express) and 
                  ACH transfers for annual plans.
                </p>
              </div>
              
              <div className="py-6">
                <h3 className="text-lg font-medium text-gray-900">
                  Do you offer enterprise plans?
                </h3>
                <p className="mt-2 text-gray-600">
                  Yes! Contact us for custom enterprise solutions with volume discounts, 
                  dedicated support, and additional compliance features.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-red-600">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-white">
              Ready to secure your HIPAA compliance?
            </h2>
            <p className="mt-4 text-xl text-red-100">
              Start your free 14-day trial today. No credit card required.
            </p>
            <div className="mt-8">
              <button
                onClick={() => handleGetStarted('professional')}
                className="bg-white text-red-600 px-8 py-3 rounded-md text-lg font-medium hover:bg-gray-100 transition-colors"
              >
                Start Free Trial
                <ArrowRightIcon className="ml-2 h-5 w-5 inline" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;