import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { complianceAPI, gcpAPI } from '../services/api';
import { PlusIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import GCPOnboardingModal from '../components/GCPOnboardingModal';

const Scan = () => {
  const [formData, setFormData] = useState({
    projectId: '',
    scanType: 'full',
  });
  const [connectedProjects, setConnectedProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadConnectedProjects();
  }, []);

  const loadConnectedProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await gcpAPI.listProjects();
      setConnectedProjects(response.data);
    } catch (err) {
      console.error('Failed to load connected projects:', err);
      setConnectedProjects([]);
    } finally {
      setLoadingProjects(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.projectId) {
      setError('Please select a GCP project');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await complianceAPI.triggerScan(formData.projectId);
      const { scan_id } = response.data;
      
      // Redirect to reports with the new scan
      navigate(`/app/reports?scan=${scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardingComplete = async (projectId) => {
    await loadConnectedProjects();
    setFormData(prev => ({ ...prev, projectId }));
    setShowOnboarding(false);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Start New Scan
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Scan your GCP project for HIPAA compliance violations
          </p>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <form onSubmit={handleSubmit} className="space-y-6 p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="projectId" className="block text-sm font-medium text-gray-700">
              GCP Project
            </label>
            
            {loadingProjects ? (
              <div className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-gray-50">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
                  Loading connected projects...
                </div>
              </div>
            ) : connectedProjects.length > 0 ? (
              <>
                <div className="mt-1 flex rounded-md shadow-sm">
                  <select
                    name="projectId"
                    id="projectId"
                    value={formData.projectId}
                    onChange={handleInputChange}
                    className="flex-1 block w-full border border-gray-300 rounded-l-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    required
                  >
                    <option value="">Select a connected project</option>
                    {connectedProjects.map((project) => (
                      <option key={project.project_id} value={project.project_id}>
                        {project.project_id} 
                        {project.status === 'active' ? ' ✓' : ' ⚠️'}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setShowOnboarding(true)}
                    className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    title="Connect new project"
                  >
                    <PlusIcon className="h-4 w-4" />
                  </button>
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  Select a connected GCP project to scan for compliance violations. 
                  ✓ indicates an active connection.
                </p>
              </>
            ) : (
              <>
                <div className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-gray-50">
                  <span className="text-gray-500">No connected projects</span>
                </div>
                <div className="mt-2 bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <div className="flex">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" />
                    <div>
                      <h3 className="text-sm font-medium text-yellow-800">
                        Connect Your First GCP Project
                      </h3>
                      <p className="text-sm text-yellow-700 mt-1">
                        You need to connect a GCP project before you can start scanning. 
                        Click below to get started with our guided setup.
                      </p>
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={() => setShowOnboarding(true)}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                        >
                          <PlusIcon className="h-4 w-4 mr-2" />
                          Connect GCP Project
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          <div>
            <label htmlFor="scanType" className="block text-sm font-medium text-gray-700">
              Scan Type
            </label>
            <select
              id="scanType"
              name="scanType"
              value={formData.scanType}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="full">Full Compliance Scan</option>
              <option value="quick">Quick Security Check</option>
              <option value="hipaa">HIPAA-Only Scan</option>
            </select>
            <p className="mt-2 text-sm text-gray-500">
              Choose the type of scan you want to perform on your project.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  What will be scanned?
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc pl-5 space-y-1">
                    <li>IAM policies and service accounts</li>
                    <li>Firewall rules and network security</li>
                    <li>Storage bucket permissions</li>
                    <li>Compute instance configurations</li>
                    <li>Logging and monitoring settings</li>
                    <li>Encryption and data protection</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate('/app')}
              className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || connectedProjects.length === 0 || !formData.projectId}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting scan...
                </div>
              ) : (
                'Start Scan'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* GCP Onboarding Modal */}
      <GCPOnboardingModal
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onComplete={handleOnboardingComplete}
      />
    </div>
  );
};

export default Scan;