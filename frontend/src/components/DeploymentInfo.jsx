import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const DeploymentInfo = ({ showDetails = false }) => {
  const [frontendInfo, setFrontendInfo] = useState(null);
  const [backendInfo, setBackendInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(showDetails);

  useEffect(() => {
    const fetchDeploymentInfo = async () => {
      try {
        // Fetch frontend deployment info
        const frontendResponse = await fetch('/deployment-info.json');
        if (frontendResponse.ok) {
          const frontendData = await frontendResponse.json();
          setFrontendInfo(frontendData);
        }

        // Fetch backend deployment info
        const backendResponse = await authAPI.get('/deployment-info');
        if (backendResponse.data) {
          setBackendInfo(backendResponse.data);
        }
      } catch (error) {
        console.warn('Could not fetch deployment info:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDeploymentInfo();
  }, []);

  if (loading) {
    return (
      <div className="text-xs text-gray-400">
        Loading deployment info...
      </div>
    );
  }

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getStatusColor = (info) => {
    if (!info) return 'text-red-500';
    if (info.status?.includes('error')) return 'text-red-500';
    if (info.status?.includes('missing')) return 'text-yellow-500';
    return 'text-green-500';
  };

  const shortHash = (hash) => hash?.substring(0, 7) || 'unknown';

  if (!expanded) {
    return (
      <div className="flex items-center space-x-4 text-xs">
        <button
          onClick={() => setExpanded(true)}
          className="text-gray-400 hover:text-gray-600 underline"
        >
          v{backendInfo?.version || '1.3.0'}
        </button>
        {frontendInfo?.git?.shortHash && (
          <span className={`font-mono ${getStatusColor(frontendInfo)}`}>
            FE: {shortHash(frontendInfo.git.shortHash)}
          </span>
        )}
        {backendInfo?.git?.shortHash && (
          <span className={`font-mono ${getStatusColor(backendInfo)}`}>
            BE: {shortHash(backendInfo.git.shortHash)}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border rounded-lg p-4 text-xs space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-700">Deployment Information</h3>
        <button
          onClick={() => setExpanded(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Frontend Info */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-600 flex items-center">
            Frontend
            <span className={`ml-2 w-2 h-2 rounded-full ${getStatusColor(frontendInfo) === 'text-green-500' ? 'bg-green-500' : getStatusColor(frontendInfo) === 'text-yellow-500' ? 'bg-yellow-500' : 'bg-red-500'}`}></span>
          </h4>
          {frontendInfo ? (
            <div className="space-y-1 text-gray-600">
              <div>Environment: <span className="font-mono">{frontendInfo.environment}</span></div>
              {frontendInfo.git && (
                <>
                  <div>Hash: <span className="font-mono">{frontendInfo.git.shortHash}</span></div>
                  <div>Branch: <span className="font-mono">{frontendInfo.git.branch}</span></div>
                </>
              )}
              <div>Built: {formatTimestamp(frontendInfo.timestamp)}</div>
            </div>
          ) : (
            <div className="text-red-500">Deployment info not available</div>
          )}
        </div>

        {/* Backend Info */}
        <div className="space-y-2">
          <h4 className="font-medium text-gray-600 flex items-center">
            Backend
            <span className={`ml-2 w-2 h-2 rounded-full ${getStatusColor(backendInfo) === 'text-green-500' ? 'bg-green-500' : getStatusColor(backendInfo) === 'text-yellow-500' ? 'bg-yellow-500' : 'bg-red-500'}`}></span>
          </h4>
          {backendInfo ? (
            <div className="space-y-1 text-gray-600">
              <div>Environment: <span className="font-mono">{backendInfo.environment}</span></div>
              {backendInfo.git && (
                <>
                  <div>Hash: <span className="font-mono">{backendInfo.git.shortHash}</span></div>
                  <div>Branch: <span className="font-mono">{backendInfo.git.branch}</span></div>
                </>
              )}
              <div>Version: <span className="font-mono">{backendInfo.version}</span></div>
              <div>Status: <span className={getStatusColor(backendInfo)}>{backendInfo.status}</span></div>
            </div>
          ) : (
            <div className="text-red-500">Backend info not available</div>
          )}
        </div>
      </div>

      {/* Sync Status */}
      <div className="border-t pt-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Sync Status:</span>
          {frontendInfo?.git?.shortHash === backendInfo?.git?.shortHash ? (
            <span className="text-green-600 flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              In Sync
            </span>
          ) : (
            <span className="text-yellow-600 flex items-center">
              <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
              Version Mismatch
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeploymentInfo;