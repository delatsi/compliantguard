import React, { useState } from 'react';
import { 
  UserCircleIcon, 
  CloudIcon, 
  BellIcon, 
  ShieldCheckIcon 
} from '@heroicons/react/24/outline';
import GCPProjectManager from '../components/GCPProjectManager';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('gcp');

  const tabs = [
    { id: 'gcp', name: 'GCP Projects', icon: CloudIcon },
    { id: 'profile', name: 'Profile', icon: UserCircleIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
  ];

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

      {/* Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'gcp' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Google Cloud Platform Integration
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Connect your GCP projects to enable automated compliance scanning. 
                Your credentials are encrypted and stored securely.
              </p>
              <GCPProjectManager />
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="text-center py-12">
              <UserCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Profile Settings
              </h3>
              <p className="text-gray-500">
                Profile management coming soon. Update your personal information and preferences.
              </p>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="text-center py-12">
              <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Notification Settings
              </h3>
              <p className="text-gray-500">
                Configure how and when you receive compliance alerts and scan notifications.
              </p>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="text-center py-12">
              <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Security Settings
              </h3>
              <p className="text-gray-500">
                Manage your security preferences, two-factor authentication, and API keys.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;