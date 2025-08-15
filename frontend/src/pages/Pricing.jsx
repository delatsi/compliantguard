import React from 'react';
import { Link } from 'react-router-dom';
import { CheckIcon } from '@heroicons/react/24/outline';

const Pricing = () => {
  const plans = [
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'Perfect for small teams getting started with HIPAA compliance',
      features: [
        'Up to 5 GCP projects',
        '10 scans per month',
        'Basic compliance reports',
        'Email support',
        'Standard security policies',
        'Monthly compliance score tracking'
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Professional',
      price: '$99',
      period: '/month',
      description: 'For growing organizations with multiple projects and advanced needs',
      features: [
        'Up to 25 GCP projects',
        'Unlimited scans',
        'Advanced compliance reports',
        'Priority support',
        'Custom security policies',
        'Real-time violation alerts',
        'API access',
        'Team collaboration',
        'Compliance dashboard',
        'Historical reporting'
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: '$299',
      period: '/month',
      description: 'For large enterprises with complex compliance requirements',
      features: [
        'Unlimited GCP projects',
        'Unlimited scans',
        'White-label reports',
        'Dedicated support manager',
        'Custom policy development',
        'Integration with SIEM tools',
        'Advanced API access',
        'SSO integration',
        'Custom compliance frameworks',
        'Audit trail and logging',
        'SLA guarantees',
        'Professional services'
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <div className="bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link to="/" className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TG</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">ThemisGuard</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
              Simple, transparent pricing
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 max-w-3xl mx-auto">
              Choose the perfect plan for your organization's HIPAA compliance needs. 
              All plans include a 14-day free trial with no credit card required.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-24 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border p-8 shadow-sm ${
                  plan.popular
                    ? 'border-primary-500 ring-2 ring-primary-500 bg-white'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="inline-flex items-center rounded-full bg-primary-600 px-4 py-1 text-xs font-medium text-white">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                  <div className="mt-4 flex items-baseline justify-center">
                    <span className="text-4xl font-bold tracking-tight text-gray-900">
                      {plan.price}
                    </span>
                    <span className="ml-1 text-lg font-semibold text-gray-500">
                      {plan.period}
                    </span>
                  </div>
                  <p className="mt-4 text-sm text-gray-500">{plan.description}</p>
                </div>

                <ul className="mt-8 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-primary-500 flex-shrink-0 mt-0.5" />
                      <span className="ml-3 text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <div className="mt-8">
                  <Link
                    to={plan.cta === 'Contact Sales' ? '/contact' : '/register'}
                    className={`block w-full rounded-md py-3 px-4 text-center text-sm font-semibold transition-colors ${
                      plan.popular
                        ? 'bg-primary-600 text-white hover:bg-primary-700'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">
              Frequently asked questions
            </h2>
          </div>
          
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                What's included in the free trial?
              </h3>
              <p className="text-gray-600">
                All plans include a 14-day free trial with full access to features. 
                No credit card required to start.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Can I change plans anytime?
              </h3>
              <p className="text-gray-600">
                Yes, you can upgrade or downgrade your plan at any time. 
                Changes take effect on your next billing cycle.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Do you offer annual discounts?
              </h3>
              <p className="text-gray-600">
                Yes, save 20% when you pay annually. Contact our sales team 
                for custom enterprise pricing.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                What if I need more projects?
              </h3>
              <p className="text-gray-600">
                Enterprise plans include unlimited projects. For other plans, 
                additional projects can be added for $5/month each.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Ready to get started?
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Start your free trial today and see how ThemisGuard can help you achieve HIPAA compliance.
          </p>
          <div className="mt-8">
            <Link
              to="/register"
              className="rounded-md bg-white px-8 py-3 text-base font-semibold text-primary-600 shadow-sm hover:bg-gray-50"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">TG</span>
              </div>
              <span className="text-xl font-semibold text-white">ThemisGuard</span>
            </div>
          </div>
          <p className="mt-4 text-center text-gray-400">
            © {new Date().getFullYear()} ThemisGuard. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Pricing;