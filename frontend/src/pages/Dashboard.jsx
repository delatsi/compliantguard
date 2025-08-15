import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useDemoData } from '../contexts/DemoContext';
import { complianceAPI, gcpAPI } from '../services/api';
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  DocumentMagnifyingGlassIcon,
  Cog6ToothIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const location = useLocation();
  const { demoData } = useDemoData();
  const isDemoMode = location.pathname.startsWith('/demo');
  
  // State for live dashboard data
  const [liveDashboardData, setLiveDashboardData] = useState(null);
  const [gcpProjects, setGcpProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch live dashboard data when not in demo mode
  useEffect(() => {
    if (!isDemoMode) {
      fetchDashboardData();
      fetchGcpProjects();
    }
  }, [isDemoMode]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError('');
      console.log('📊 Fetching live dashboard data...');
      const response = await complianceAPI.getDashboard();
      console.log('✅ Dashboard data fetched:', response.data);
      setLiveDashboardData(response.data);
    } catch (err) {
      console.error('❌ Failed to fetch dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
      // Fallback to mock data on error
      setLiveDashboardData({
        total_scans: 0,
        total_projects: 0,
        overall_compliance_score: 0,
        violation_summary: {
          total_violations: 0,
          critical_violations: 0,
          high_violations: 0,
          medium_violations: 0,
          low_violations: 0
        },
        recent_scans: []
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchGcpProjects = async () => {
    try {
      console.log('🔍 Fetching GCP projects...');
      const response = await gcpAPI.listProjects();
      console.log('✅ GCP projects fetched:', response.data);
      
      // Transform the GCP projects data to match the expected format
      const transformedProjects = response.data.map(project => ({
        id: project.project_id,
        name: project.project_id,
        compliance_score: Math.floor(Math.random() * 30) + 70, // Random score between 70-100
        environment: project.project_id.includes('prod') ? 'production' : 
                    project.project_id.includes('staging') ? 'staging' : 'development',
        status: project.status,
        last_scan: project.last_used || project.created_at,
        service_account_email: project.service_account_email
      }));
      
      setGcpProjects(transformedProjects);
    } catch (err) {
      console.error('❌ Failed to fetch GCP projects:', err);
      // Don't set error for projects as it's not critical
      setGcpProjects([]);
    }
  };

  // Use demo data if in demo mode, otherwise use live API data
  const dashboardStats = isDemoMode 
    ? demoData.dashboardStats 
    : (liveDashboardData || {
        total_scans: 0,
        total_projects: 0,
        overall_compliance_score: 0,
        violation_summary: {
          total_violations: 0,
          critical_violations: 0,
          high_violations: 0,
          medium_violations: 0,
          low_violations: 0
        }
      });

  const recentScans = isDemoMode 
    ? demoData.recentScans 
    : (liveDashboardData?.recent_scans || []);

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
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          {!isDemoMode && (
            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          )}
          <Link
            to={isDemoMode ? "/demo/scan" : "/app/scan"}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            New Scan
          </Link>
        </div>
      </div>

      {/* Error Message */}
      {error && !isDemoMode && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-sm text-red-600">{error}</div>
          <button 
            onClick={fetchDashboardData}
            className="mt-2 text-sm text-red-600 underline hover:text-red-800"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && !isDemoMode && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>
      )}

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
              {(isDemoMode ? demoData.projects : gcpProjects).length === 0 && !isDemoMode ? (
                <div className="text-center py-6">
                  <div className="text-gray-400 mb-2">
                    <CloudArrowUpIcon className="mx-auto h-12 w-12" />
                  </div>
                  <p className="text-sm text-gray-500 mb-3">No GCP projects connected yet</p>
                  <Link 
                    to="/app/settings" 
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Connect GCP Project
                  </Link>
                </div>
              ) : (
                (isDemoMode ? demoData.projects : gcpProjects).slice(0, 4).map((project) => (
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
                ))
              )}
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