import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { complianceAPI } from '../services/api';

const Scan = () => {
  const [formData, setFormData] = useState({
    projectId: '',
    scanType: 'full',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

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
      setError('Project ID is required');
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
              GCP Project ID
            </label>
            <input
              type="text"
              name="projectId"
              id="projectId"
              value={formData.projectId}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="my-gcp-project-id"
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              Enter the ID of the GCP project you want to scan for compliance violations.
            </p>
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
              disabled={loading}
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
    </div>
  );
};

export default Scan;