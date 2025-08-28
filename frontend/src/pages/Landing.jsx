import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useVersion } from '../hooks/useVersion';
import { 
  ShieldCheckIcon, 
  DocumentMagnifyingGlassIcon, 
  ChartBarIcon,
  CloudIcon,
  LockClosedIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

const Landing = () => {
  const { user, logout } = useAuth();
  const { version, loading } = useVersion();
  const features = [
    {
      name: 'HIPAA Compliance Scanning',
      description: 'Comprehensive scanning of your GCP infrastructure for HIPAA compliance violations.',
      icon: ShieldCheckIcon,
    },
    {
      name: 'Real-time Analysis',
      description: 'Get instant feedback on your security posture with detailed violation reports.',
      icon: DocumentMagnifyingGlassIcon,
    },
    {
      name: 'Compliance Dashboard',
      description: 'Track your compliance progress with intuitive dashboards and metrics.',
      icon: ChartBarIcon,
    },
    {
      name: 'Cloud-Native',
      description: 'Built specifically for Google Cloud Platform with deep integration.',
      icon: CloudIcon,
    },
    {
      name: 'Secure by Design',
      description: 'Enterprise-grade security with encrypted data storage and transmission.',
      icon: LockClosedIcon,
    },
    {
      name: 'Lightning Fast',
      description: 'Serverless architecture ensures fast scans and minimal latency.',
      icon: BoltIcon,
    },
  ];

  return (
    <div className="bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">TG</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">ThemisGuard</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/pricing"
                className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Pricing
              </Link>
              {user ? (
                // Authenticated user menu
                <>
                  <Link
                    to="/app"
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Dashboard
                  </Link>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">
                      Hello, {user.first_name || user.email}
                    </span>
                    <button
                      onClick={logout}
                      className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                    >
                      Sign Out
                    </button>
                  </div>
                </>
              ) : (
                // Unauthenticated user menu
                <>
                  <Link
                    to="/login"
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium"
                    onClick={() => console.log('Header register link clicked')}
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-primary-600 to-primary-700 py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              HIPAA Compliance
              <br />
              <span className="text-primary-200">Made Simple</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-primary-100 max-w-3xl mx-auto">
              Automated HIPAA compliance scanning for your Google Cloud Platform infrastructure. 
              Identify violations, track remediation, and maintain compliance with ease.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                to="/register"
                className="rounded-md bg-white px-6 py-3 text-base font-semibold text-primary-600 shadow-sm hover:bg-gray-50"
              >
                Start Free Trial
              </Link>
              <Link
                to="/demo"
                className="rounded-md border border-white/20 px-6 py-3 text-base font-semibold text-white hover:bg-white/10 flex items-center space-x-2"
              >
                <span>View Demo</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m6-6a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need for HIPAA compliance
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Comprehensive tools and insights to keep your GCP infrastructure compliant.
            </p>
          </div>
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.name} className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
                <div className="flex items-center">
                  <feature.icon className="h-8 w-8 text-primary-600" />
                  <h3 className="ml-3 text-lg font-semibold text-gray-900">{feature.name}</h3>
                </div>
                <p className="mt-4 text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Ready to secure your infrastructure?
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Join thousands of organizations who trust ThemisGuard for their HIPAA compliance needs.
          </p>
          <div className="mt-8">
            <Link
              to="/register"
              className="rounded-md bg-white px-8 py-3 text-base font-semibold text-primary-600 shadow-sm hover:bg-gray-50"
            >
              Get Started Today
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
            {!loading && (
              <span className="block text-sm text-gray-500 mt-1">
                v{version.app_version} • Built {version.build_date}
              </span>
            )}
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;