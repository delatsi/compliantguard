import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useDemoData } from '../contexts/DemoContext';
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  DocumentMagnifyingGlassIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const location = useLocation();
  const { demoData } = useDemoData();
  const isDemoMode = location.pathname.startsWith('/demo');

  // Use demo data if in demo mode, otherwise use mock data
  const dashboardStats = isDemoMode ? demoData.dashboardStats : {
    total_scans: 12,
    total_projects: 4,
    overall_compliance_score: 87,
    violation_summary: {
      total_violations: 23,
      critical_violations: 2,
      high_violations: 8,
      medium_violations: 10,
      low_violations: 3
    }
  };

  const recentScans = isDemoMode ? demoData.recentScans : [
    {
      scan_id: '1',
      project_name: 'production-app',
      scan_timestamp: '2024-01-15T10:30:00Z',
      compliance_score: 92,
      total_violations: 8,
      status: 'completed',
    },
    {
      scan_id: '2',
      project_name: 'staging-env',
      scan_timestamp: '2024-01-14T15:20:00Z',
      compliance_score: 78,
      total_violations: 15,
      status: 'completed',
    },
    {
      scan_id: '3',
      project_name: 'dev-environment',
      scan_timestamp: '2024-01-13T16:45:00Z',
      compliance_score: 85,
      total_violations: 12,
      status: 'completed',
    },
  ];

  const stats = [
    {
      name: 'Total Scans',
      value: dashboardStats.total_scans.toString(),
      change: '+12 this month',
      changeType: 'increase',
      icon: DocumentTextIcon,
    },
    {
      name: 'Compliance Score',
      value: `${dashboardStats.overall_compliance_score}%`,
      change: '+5% from last scan',
      changeType: 'increase',
      icon: ShieldCheckIcon,
    },
    {
      name: 'Active Violations',
      value: dashboardStats.violation_summary.total_violations.toString(),
      change: '-8 from last week',
      changeType: 'decrease',
      icon: ExclamationTriangleIcon,
    },
    {
      name: 'Projects Monitored',
      value: dashboardStats.total_projects.toString(),
      change: '+2 this month',
      changeType: 'increase',
      icon: ChartBarIcon,
    },
  ];

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your HIPAA compliance status
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <Link
            to="/app/scan"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            New Scan
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <span className={`font-medium ${
                  stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stat.change}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Scans */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Scans
          </h3>
          <div className="flow-root">
            <ul className="-my-5 divide-y divide-gray-200">
              {recentScans.slice(0, 4).map((scan) => (
                <li key={scan.scan_id} className="py-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className={`h-3 w-3 rounded-full ${
                        scan.compliance_score >= 90 ? 'bg-green-400' : 
                        scan.compliance_score >= 70 ? 'bg-yellow-400' : 'bg-red-400'
                      }`}></div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {scan.project_name || scan.project_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatDate(scan.scan_timestamp)} • {scan.total_violations} violations
                        {scan.duration && (
                          <span className="ml-2 text-gray-400">• {scan.duration}</span>
                        )}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="inline-flex items-center text-base font-semibold text-gray-900">
                        {scan.compliance_score}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {scan.status === 'completed' ? 'Completed' : 'In Progress'}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-6">
            <Link
              to={isDemoMode ? "/demo/reports" : "/app/reports"}
              className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              View all reports
            </Link>
          </div>
        </div>
      </div>

      {/* Compliance Breakdown */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Violation Categories */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Violations by Category
            </h3>
            <div className="space-y-4">
              {isDemoMode && demoData.complianceMetrics.violationsByCategory.map((category, index) => (
                <div key={category.category} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      index === 0 ? 'bg-red-400' :
                      index === 1 ? 'bg-orange-400' :
                      index === 2 ? 'bg-yellow-400' :
                      index === 3 ? 'bg-blue-400' : 'bg-gray-400'
                    }`}></div>
                    <span className="text-sm font-medium text-gray-900">{category.category}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">{category.count}</span>
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          index === 0 ? 'bg-red-400' :
                          index === 1 ? 'bg-orange-400' :
                          index === 2 ? 'bg-yellow-400' :
                          index === 3 ? 'bg-blue-400' : 'bg-gray-400'
                        }`}
                        style={{ width: `${category.percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500 w-8">{category.percentage}%</span>
                  </div>
                </div>
              ))}
              {!isDemoMode && (
                <div className="text-center py-8 text-gray-500">
                  <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>Run your first scan to see violation categories</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Projects Overview */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Projects Overview
            </h3>
            <div className="space-y-3">
              {(isDemoMode ? demoData.projects : [
                { id: 'prod-app', name: 'Production App', compliance_score: 92, environment: 'production' },
                { id: 'staging', name: 'Staging Environment', compliance_score: 78, environment: 'staging' }
              ]).slice(0, 4).map((project) => (
                <div key={project.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-8 rounded-full ${
                      project.environment === 'production' ? 'bg-red-500' :
                      project.environment === 'staging' ? 'bg-yellow-500' : 'bg-blue-500'
                    }`}></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{project.name}</p>
                      <p className="text-xs text-gray-500 capitalize">{project.environment}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-semibold ${
                      project.compliance_score >= 90 ? 'text-green-600' :
                      project.compliance_score >= 70 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {project.compliance_score}%
                    </div>
                    <div className="text-xs text-gray-500">compliance</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Trend Chart */}
      {isDemoMode && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Compliance Trend (Last 15 Days)
            </h3>
            <div className="mt-4">
              <div className="flex items-end space-x-1 h-32">
                {demoData.complianceMetrics.trendsData.slice(-15).map((point) => (
                  <div key={point.date} className="flex-1 flex flex-col items-center">
                    <div 
                      className="w-full bg-primary-500 rounded-t"
                      style={{ height: `${(point.score / 100) * 120}px` }}
                      title={`${point.score}% on ${new Date(point.date).toLocaleDateString()}`}
                    ></div>
                    <span className="text-xs text-gray-500 mt-1">
                      {new Date(point.date).getDate()}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>Jan 1</span>
                <span>Jan 15</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link
              to={isDemoMode ? "/demo/scan" : "/app/scan"}
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 transition-colors"
            >
              <div className="flex-shrink-0">
                <DocumentMagnifyingGlassIcon className="h-6 w-6 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  Start New Scan
                </p>
                <p className="text-sm text-gray-500">
                  Scan a GCP project
                </p>
              </div>
            </Link>
            <Link
              to={isDemoMode ? "/demo/reports" : "/app/reports"}
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 transition-colors"
            >
              <div className="flex-shrink-0">
                <DocumentTextIcon className="h-6 w-6 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  View Reports
                </p>
                <p className="text-sm text-gray-500">
                  Browse all reports
                </p>
              </div>
            </Link>
            <Link
              to={isDemoMode ? "/demo/settings" : "/app/settings"}
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 transition-colors"
            >
              <div className="flex-shrink-0">
                <Cog6ToothIcon className="h-6 w-6 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  Settings
                </p>
                <p className="text-sm text-gray-500">
                  Configure alerts
                </p>
              </div>
            </Link>
            <a
              href="https://docs.themisguard.com"
              target="_blank"
              rel="noopener noreferrer"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 transition-colors"
            >
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-6 w-6 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  Documentation
                </p>
                <p className="text-sm text-gray-500">
                  Learn more
                </p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;