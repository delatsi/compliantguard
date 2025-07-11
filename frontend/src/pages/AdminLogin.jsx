import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdmin } from '../contexts/AdminContext';
import {
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
  KeyIcon,
  LockClosedIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

const AdminLogin = () => {
  const navigate = useNavigate();
  const { loginAdmin, verify2FA } = useAdmin();

  const [step, setStep] = useState('login'); // 'login' or '2fa'
  const [tempToken, setTempToken] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [loginForm, setLoginForm] = useState({
    email: '',
    password: ''
  });

  const [twoFactorCode, setTwoFactorCode] = useState('');

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const result = await loginAdmin(loginForm);
      
      if (result.success && result.requires2FA) {
        setTempToken(result.tempToken);
        setStep('2fa');
      } else if (result.success) {
        navigate('/admin');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const result = await verify2FA(tempToken, twoFactorCode);
      
      if (result.success) {
        navigate('/admin');
      } else {
        setError(result.error || '2FA verification failed');
      }
    } catch (err) {
      setError('2FA verification failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="h-12 w-12 bg-red-600 rounded-lg flex items-center justify-center">
            <ShieldCheckIcon className="h-8 w-8 text-white" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          ThemisGuard Admin Portal
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          {step === 'login' ? 'Administrator Access Only' : 'Two-Factor Authentication Required'}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {/* Security Notice */}
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <LockClosedIcon className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Restricted Access
                </h3>
                <p className="mt-1 text-sm text-red-700">
                  This portal is restricted to authorized administrators only. 
                  All access attempts are logged and monitored.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {step === 'login' && (
            <form onSubmit={handleLoginSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Administrator Email
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={loginForm.email}
                    onChange={handleInputChange}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-red-500 focus:border-red-500"
                    placeholder="admin@themisguard.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="mt-1 relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={loginForm.password}
                    onChange={handleInputChange}
                    className="appearance-none block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-red-500 focus:border-red-500"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                    ) : (
                      <EyeIcon className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Authenticating...
                    </div>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </div>
            </form>
          )}

          {step === '2fa' && (
            <form onSubmit={handle2FASubmit} className="space-y-6">
              <div className="text-center">
                <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">
                  Two-Factor Authentication
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>

              <div>
                <label htmlFor="twoFactorCode" className="block text-sm font-medium text-gray-700">
                  Authentication Code
                </label>
                <div className="mt-1">
                  <input
                    id="twoFactorCode"
                    name="twoFactorCode"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength="6"
                    required
                    value={twoFactorCode}
                    onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-red-500 focus:border-red-500 text-center text-lg tracking-widest"
                    placeholder="123456"
                    autoComplete="one-time-code"
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setStep('login');
                    setTempToken(null);
                    setTwoFactorCode('');
                    setError('');
                  }}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isLoading || twoFactorCode.length !== 6}
                  className="flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Verifying...
                    </div>
                  ) : (
                    'Verify & Sign In'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Demo Credentials Notice */}
          <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-xs text-yellow-700">
              <strong>Demo Credentials:</strong><br />
              Email: admin@themisguard.com<br />
              Password: SecureAdmin123!<br />
              2FA Code: 123456
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;