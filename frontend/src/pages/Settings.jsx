import React from 'react';

const Settings = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Settings
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account and application settings
          </p>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Settings Coming Soon
          </h3>
          <p className="text-gray-500">
            The settings interface will be implemented next.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;