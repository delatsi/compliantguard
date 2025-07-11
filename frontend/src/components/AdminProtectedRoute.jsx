import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAdmin } from '../contexts/AdminContext';
import { 
  ShieldExclamationIcon,
  LockClosedIcon 
} from '@heroicons/react/24/outline';

const AdminProtectedRoute = ({ children, requiredPermission = null }) => {
  const { isAdmin, is2FAVerified, adminUser, hasPermission } = useAdmin();
  const location = useLocation();

  // Not authenticated as admin
  if (!isAdmin || !is2FAVerified) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  // Check specific permission if required
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="flex justify-center">
            <ShieldExclamationIcon className="h-12 w-12 text-red-500" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Access Denied
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            You don't have permission to access this resource.
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <LockClosedIcon className="h-5 w-5 text-red-400 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Insufficient Permissions
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>Required permission: <code className="bg-red-100 px-1 rounded">{requiredPermission}</code></p>
                    <p className="mt-1">Your permissions: {adminUser?.permissions?.join(', ') || 'None'}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <button
                onClick={() => window.history.back()}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return children;
};

export default AdminProtectedRoute;