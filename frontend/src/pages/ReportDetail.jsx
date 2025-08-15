import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { complianceAPI } from '../services/api';
import { 
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ShieldCheckIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const ReportDetail = () => {
  const { scanId } = useParams();
  const location = useLocation();
  const isDemoMode = location.pathname.startsWith('/demo');
  
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      console.log('📋 Fetching report details for:', scanId);
      const response = await complianceAPI.getReport(scanId);
      console.log('✅ Report details fetched:', response.data);
      setReport(response.data);
    } catch (err) {
      console.error('❌ Failed to fetch report details:', err);
      setError(err.response?.data?.detail || 'Failed to load report details');
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    fetchReport();
  }, [scanId, fetchReport]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'HIGH':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      case 'MEDIUM':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'LOW':
        return <CheckCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <CheckCircleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getComplianceScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 80) return 'text-yellow-600 bg-yellow-50';
    if (score >= 70) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="bg-white shadow rounded-lg p-6">
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <Link
            to={isDemoMode ? "/demo/reports" : "/app/reports"}
            className="flex items-center text-gray-500 hover:text-gray-700 mr-4"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Reports
          </Link>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <XCircleIcon className="h-6 w-6 text-red-500 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-red-900">Error Loading Report</h3>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const violationsBySeverity = {
    CRITICAL: report.violations?.filter(v => v.severity === 'CRITICAL') || [],
    HIGH: report.violations?.filter(v => v.severity === 'HIGH') || [],
    MEDIUM: report.violations?.filter(v => v.severity === 'MEDIUM') || [],
    LOW: report.violations?.filter(v => v.severity === 'LOW') || []
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link
            to={isDemoMode ? "/demo/reports" : "/app/reports"}
            className="flex items-center text-gray-500 hover:text-gray-700 mr-4"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Reports
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Compliance Report Details
            </h1>
            <p className="text-sm text-gray-500">
              Scan ID: {report.scan_id}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className={`px-4 py-2 rounded-lg ${getComplianceScoreColor(report.compliance_score)}`}>
            <div className="flex items-center">
              <ShieldCheckIcon className="h-5 w-5 mr-2" />
              <span className="font-semibold">{report.compliance_score}% Compliant</span>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <ClockIcon className="h-8 w-8 text-gray-400" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Scan Date</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatDate(report.scan_timestamp)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Violations</p>
              <p className="text-lg font-semibold text-gray-900">
                {report.total_violations}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <XCircleIcon className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Critical Issues</p>
              <p className="text-lg font-semibold text-gray-900">
                {violationsBySeverity.CRITICAL.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-blue-600">{report.project_id?.charAt(0).toUpperCase()}</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Project</p>
              <p className="text-lg font-semibold text-gray-900">
                {report.project_id}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Violations by Severity */}
      {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(severity => {
        const violations = violationsBySeverity[severity];
        if (violations.length === 0) return null;

        return (
          <div key={severity} className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                {getSeverityIcon(severity)}
                <h3 className="ml-2 text-lg font-medium text-gray-900">
                  {severity} Priority Issues ({violations.length})
                </h3>
              </div>
            </div>
            
            <div className="divide-y divide-gray-200">
              {violations.map((violation, index) => (
                <div key={index} className="px-6 py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getSeverityColor(violation.severity)}`}>
                          {violation.severity}
                        </span>
                        <span className="ml-2 text-sm text-gray-500">
                          {violation.service} • {violation.resource}
                        </span>
                      </div>
                      
                      <h4 className="text-base font-medium text-gray-900 mb-2">
                        {violation.violation}
                      </h4>
                      
                      {violation.hipaa_rule && (
                        <p className="text-sm text-blue-600 mb-2">
                          <strong>HIPAA Rule:</strong> {violation.hipaa_rule}
                        </p>
                      )}
                      
                      {violation.business_impact && (
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Business Impact:</strong> {violation.business_impact}
                        </p>
                      )}
                      
                      {violation.remediation && (
                        <div className="bg-green-50 border border-green-200 rounded-md p-3 mt-3">
                          <p className="text-sm text-green-800">
                            <strong>Remediation:</strong> {violation.remediation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {report.violations?.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <CheckCircleIcon className="h-6 w-6 text-green-500 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-green-900">No Violations Found</h3>
              <p className="text-green-700 mt-1">
                This scan found no HIPAA compliance violations. Your infrastructure appears to be properly configured.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportDetail;