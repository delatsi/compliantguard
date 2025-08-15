import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useDemoData } from '../contexts/DemoContext';
import { complianceAPI } from '../services/api';
import { 
  DocumentTextIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const Reports = () => {
  const location = useLocation();
  const { demoData } = useDemoData();
  const isDemoMode = location.pathname.startsWith('/demo');
  
  // State for real API reports
  const [realReports, setRealReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch reports from API when not in demo mode
  useEffect(() => {
    if (!isDemoMode) {
      fetchReports();
    }
  }, [isDemoMode]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      setError('');
      console.log('📋 Fetching reports from API...');
      const response = await complianceAPI.listReports();
      console.log('✅ Reports fetched:', response.data);
      setRealReports(response.data.reports || []);
    } catch (err) {
      console.error('❌ Failed to fetch reports:', err);
      setError(err.response?.data?.detail || 'Failed to load reports');
      setRealReports([]);
    } finally {
      setLoading(false);
    }
  };

  const reports = isDemoMode ? demoData.recentScans : realReports;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSeverityBadge = (score) => {
    if (score >= 90) return { color: 'bg-green-100 text-green-800', text: 'Excellent' };
    if (score >= 80) return { color: 'bg-yellow-100 text-yellow-800', text: 'Good' };
    if (score >= 70) return { color: 'bg-orange-100 text-orange-800', text: 'Fair' };
    return { color: 'bg-red-100 text-red-800', text: 'Poor' };
  };

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Compliance Reports
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            View and manage your HIPAA compliance scan reports
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          {!isDemoMode && (
            <button
              onClick={fetchReports}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          )}
          <Link
            to={isDemoMode ? "/demo/scan" : "/app/scan"}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            New Scan
          </Link>
        </div>
      </div>

      {/* Reports Stats */}
      {isDemoMode && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Reports
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {demoData.recentScans.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ShieldCheckIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Compliance
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {Math.round(demoData.recentScans.reduce((sum, scan) => sum + scan.compliance_score, 0) / demoData.recentScans.length)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Violations
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {demoData.recentScans.reduce((sum, scan) => sum + scan.total_violations, 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Last Scan
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {new Date(demoData.recentScans[0]?.scan_timestamp).toLocaleDateString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && !isDemoMode && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-sm text-red-600">{error}</div>
          <button 
            onClick={fetchReports}
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

      {/* Reports Table */}
      {!loading && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
          {reports.length > 0 ? (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Project
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Scan Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Compliance Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Violations
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reports.map((report) => {
                    const severityBadge = getSeverityBadge(report.compliance_score);
                    return (
                      <tr key={report.scan_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                                <DocumentTextIcon className="h-5 w-5 text-primary-600" />
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {report.project_name || report.project_id}
                              </div>
                              <div className="text-sm text-gray-500">
                                {report.project_id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{formatDate(report.scan_timestamp)}</div>
                          {report.duration && (
                            <div className="text-sm text-gray-500">Duration: {report.duration}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="text-sm font-medium text-gray-900 mr-2">
                              {report.compliance_score}%
                            </div>
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${severityBadge.color}`}>
                              {severityBadge.text}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <ExclamationTriangleIcon className="h-4 w-4 text-red-400 mr-1" />
                            <span className="text-sm text-gray-900">{report.total_violations}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircleIcon className="h-3 w-3 mr-1" />
                            {report.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link 
                            to={`${isDemoMode ? '/demo' : '/app'}/reports/${report.scan_id}`}
                            className="text-primary-600 hover:text-primary-900 flex items-center"
                          >
                            <EyeIcon className="h-4 w-4 mr-1" />
                            View Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No reports yet
              </h3>
              <p className="text-gray-500 mb-6">
                Start your first compliance scan to see reports here.
              </p>
              <Link
                to={isDemoMode ? "/demo/scan" : "/app/scan"}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                Start First Scan
              </Link>
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;