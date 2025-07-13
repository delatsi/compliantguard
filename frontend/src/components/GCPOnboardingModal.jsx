import React, { useState } from 'react';
import { XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { gcpAPI } from '../services/api';

const GCPOnboardingModal = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [projectId, setProjectId] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const steps = [
    {
      id: 1,
      title: 'Create Service Account',
      description: 'Set up a GCP service account with the required permissions'
    },
    {
      id: 2,
      title: 'Download Credentials',
      description: 'Download the service account JSON key file'
    },
    {
      id: 3,
      title: 'Upload to CompliantGuard',
      description: 'Upload your credentials to enable secure scanning'
    }
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/json') {
      setFile(selectedFile);
      setError('');
    } else {
      setError('Please select a valid JSON file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!projectId || !file) {
      setError('Please provide both project ID and service account file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await gcpAPI.uploadCredentialsFile(projectId, file);
      setUploadSuccess(true);
      setTimeout(() => {
        onComplete && onComplete(projectId);
        handleClose();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setCurrentStep(1);
    setProjectId('');
    setFile(null);
    setError('');
    setUploadSuccess(false);
    onClose();
  };

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 3));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b">
          <h3 className="text-lg font-medium text-gray-900">
            Connect Your GCP Project
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="py-6">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {steps.map((step, stepIdx) => (
                <li key={step.id} className={`${stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : ''} relative`}>
                  <div className="flex items-center">
                    <div className={`
                      flex items-center justify-center w-8 h-8 rounded-full border-2
                      ${currentStep > step.id 
                        ? 'bg-primary-600 border-primary-600' 
                        : currentStep === step.id 
                        ? 'border-primary-600 bg-white'
                        : 'border-gray-300 bg-white'
                      }
                    `}>
                      {currentStep > step.id ? (
                        <CheckCircleIcon className="h-5 w-5 text-white" />
                      ) : (
                        <span className={`text-sm font-medium ${
                          currentStep === step.id ? 'text-primary-600' : 'text-gray-500'
                        }`}>
                          {step.id}
                        </span>
                      )}
                    </div>
                    {stepIdx !== steps.length - 1 && (
                      <div className={`
                        absolute top-4 left-8 w-full h-0.5
                        ${currentStep > step.id ? 'bg-primary-600' : 'bg-gray-300'}
                      `} />
                    )}
                  </div>
                  <div className="mt-2">
                    <p className="text-sm font-medium text-gray-900">{step.title}</p>
                    <p className="text-xs text-gray-500">{step.description}</p>
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Step Content */}
        <div className="mt-6">
          {currentStep === 1 && (
            <div className="space-y-4">
              <h4 className="text-lg font-medium text-gray-900">Step 1: Create Service Account</h4>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h5 className="font-medium text-blue-900 mb-2">Follow these steps in Google Cloud Console:</h5>
                <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
                  <li>Go to <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">IAM & Admin → Service Accounts</a></li>
                  <li>Click "Create Service Account"</li>
                  <li>Enter a name: <code className="bg-blue-100 px-1 rounded">compliantguard-scanner</code></li>
                  <li>Add these roles:
                    <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                      <li>Security Reviewer</li>
                      <li>Viewer</li>
                      <li>Cloud Asset Viewer</li>
                    </ul>
                  </li>
                  <li>Click "Done"</li>
                </ol>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" />
                  <div>
                    <h5 className="font-medium text-yellow-800">Important Security Note</h5>
                    <p className="text-sm text-yellow-700 mt-1">
                      CompliantGuard only requires read-only permissions to scan your infrastructure. 
                      Never grant write or admin permissions to scanning tools.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              <h4 className="text-lg font-medium text-gray-900">Step 2: Download Service Account Key</h4>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h5 className="font-medium text-green-900 mb-2">Download the JSON key file:</h5>
                <ol className="list-decimal list-inside space-y-2 text-sm text-green-800">
                  <li>Find your service account in the list</li>
                  <li>Click the three dots (⋮) → "Manage keys"</li>
                  <li>Click "Add Key" → "Create new key"</li>
                  <li>Select "JSON" format</li>
                  <li>Click "Create" - the file will download automatically</li>
                </ol>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5 mr-2" />
                  <div>
                    <h5 className="font-medium text-red-800">Security Warning</h5>
                    <p className="text-sm text-red-700 mt-1">
                      Keep this JSON file secure! It provides access to your GCP project. 
                      CompliantGuard encrypts and stores it securely using AWS KMS.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-4">
              <h4 className="text-lg font-medium text-gray-900">Step 3: Upload to CompliantGuard</h4>
              
              {uploadSuccess ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
                    <div>
                      <h5 className="font-medium text-green-800">Success!</h5>
                      <p className="text-sm text-green-700 mt-1">
                        Your GCP project has been connected successfully. You can now start scanning.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      GCP Project ID
                    </label>
                    <input
                      type="text"
                      value={projectId}
                      onChange={(e) => setProjectId(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="my-gcp-project-id"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Service Account JSON File
                    </label>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleFileChange}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    {file && (
                      <p className="text-sm text-green-600 mt-1">
                        ✓ {file.name} selected
                      </p>
                    )}
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-sm text-red-600">{error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-6 border-t mt-6">
          <div className="flex space-x-2">
            {currentStep > 1 && !uploadSuccess && (
              <button
                onClick={prevStep}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Previous
              </button>
            )}
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              {uploadSuccess ? 'Close' : 'Cancel'}
            </button>
            
            {!uploadSuccess && (
              <>
                {currentStep < 3 ? (
                  <button
                    onClick={nextStep}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={handleUpload}
                    disabled={!projectId || !file || loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Uploading...
                      </div>
                    ) : (
                      'Connect Project'
                    )}
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GCPOnboardingModal;