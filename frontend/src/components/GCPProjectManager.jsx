import React, { useState, useEffect } from 'react';
import { 
  CloudIcon,
  TrashIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon,
  PlusIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';
import { gcpAPI } from '../services/api';
import GCPOnboardingModal from './GCPOnboardingModal';

const GCPProjectManager = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await gcpAPI.listProjects();
      setProjects(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load projects');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadProjects();
    setRefreshing(false);
  };

  const handleRemoveProject = async (projectId) => {
    if (!window.confirm(`Are you sure you want to disconnect project "${projectId}"? This will remove all stored credentials for this project.`)) {
      return;
    }

    try {
      await gcpAPI.revokeCredentials(projectId);
      await loadProjects(); // Reload the list
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove project');
    }
  };

  const handleOnboardingComplete = async (projectId) => {
    await loadProjects(); // Reload to show the new project
    setShowOnboarding(false);
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
      case 'failed':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ExclamationCircleIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'Connected';
      case 'connected':
        return 'Connected';
      case 'error':
        return 'Connection Error';
      case 'failed':
        return 'Authentication Failed';
      default:
        return 'Unknown Status';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white shadow rounded-lg">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Connected GCP Projects
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Manage your Google Cloud Platform project connections
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                <ArrowPathIcon className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={() => setShowOnboarding(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Connect Project
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="px-6 py-4 bg-red-50 border-b border-red-200">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Projects List */}
        <div className="divide-y divide-gray-200">
          {projects.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <CloudIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No connected projects</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by connecting your first GCP project
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setShowOnboarding(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Connect Your First Project
                </button>
              </div>
            </div>
          ) : (
            projects.map((project) => (
              <div key={project.project_id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <CloudIcon className="h-8 w-8 text-blue-500" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {project.project_id}
                      </h4>
                      <div className="flex items-center mt-1">
                        {getStatusIcon(project.status)}
                        <span className="ml-2 text-sm text-gray-500">
                          {getStatusText(project.status)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        Service Account: {project.service_account_email}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        Connected: {formatDate(project.created_at)}
                      </p>
                      <p className="text-xs text-gray-400">
                        Last Used: {formatDate(project.last_used)}
                      </p>
                    </div>
                    
                    <button
                      onClick={() => handleRemoveProject(project.project_id)}
                      className="inline-flex items-center p-2 border border-transparent rounded-full text-red-400 hover:text-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      title="Disconnect project"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Info Footer */}
        {projects.length > 0 && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-start space-x-2">
              <ExclamationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
              <div className="text-sm text-gray-600">
                <p className="font-medium">Security Information</p>
                <p className="mt-1">
                  All credentials are encrypted using AWS KMS before storage. 
                  CompliantGuard only has read-only access to scan your infrastructure.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Onboarding Modal */}
      <GCPOnboardingModal
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onComplete={handleOnboardingComplete}
      />
    </>
  );
};

export default GCPProjectManager;