import React from 'react';
import { useVersion } from '../hooks/useVersion';
import DeploymentInfo from './DeploymentInfo';

const Footer = () => {
  const { version, loading } = useVersion();

  if (loading) {
    return null; // Don't show footer while loading
  }

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <span>© 2025 ThemisGuard</span>
            <span className="hidden sm:inline">HIPAA Compliance Scanner</span>
          </div>
          <div className="flex items-center space-x-4">
            <DeploymentInfo />
            <div className="hidden md:flex items-center space-x-4 text-xs text-gray-500">
              <span title={`Git commit: ${version.git_commit}`}>
                v{version.app_version}
              </span>
              <span className="hidden lg:inline">
                API v{version.api_version}
              </span>
              <span className="hidden lg:inline">
                {version.build_date}
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;