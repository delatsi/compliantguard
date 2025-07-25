import React, { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const GoogleSSO = ({ onSuccess, onError, disabled = false }) => {
  const googleButtonRef = useRef(null);
  const { login } = useAuth();

  const handleCredentialResponse = useCallback(async (response) => {
    try {
      // Decode the JWT token from Google
      const userInfo = JSON.parse(atob(response.credential.split('.')[1]));
      
      // Mock successful login for development
      const mockLoginResult = await login(userInfo.email, 'google-sso-password');
      
      if (mockLoginResult.success) {
        onSuccess?.(userInfo);
      } else {
        onError?.(new Error('SSO login failed'));
      }
    } catch (error) {
      console.error('Google SSO error:', error);
      onError?.(error);
    }
  }, [login, onSuccess, onError]);

  useEffect(() => {
    // Load Google Identity Services script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      if (window.google && window.google.accounts) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || 'your-google-client-id.googleusercontent.com',
          callback: handleCredentialResponse,
        });

        if (googleButtonRef.current) {
          window.google.accounts.id.renderButton(googleButtonRef.current, {
            theme: 'outline',
            size: 'large',
            width: '100%',
            text: 'signin_with',
            shape: 'rectangular',
          });
        }
      }
    };

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [handleCredentialResponse]);

  const handleManualGoogleLogin = useCallback(async () => {
    // Fallback for development - simulate Google login
    try {
      const mockUser = {
        email: 'user@gmail.com',
        name: 'Demo User',
        picture: 'https://via.placeholder.com/40',
        sub: 'google-user-123'
      };

      const mockLoginResult = await login(mockUser.email, 'google-sso-password');
      
      if (mockLoginResult.success) {
        onSuccess?.(mockUser);
      } else {
        onError?.(new Error('Mock SSO login failed'));
      }
    } catch (error) {
      onError?.(error);
    }
  }, [login, onSuccess, onError]);

  return (
    <div className="w-full">
      {/* Google SSO Button Container */}
      <div ref={googleButtonRef} className="w-full mb-4"></div>
      
      {/* Fallback button for development */}
      <button
        type="button"
        onClick={handleManualGoogleLogin}
        disabled={disabled}
        className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
        Continue with Google (Demo)
      </button>
    </div>
  );
};

export default GoogleSSO;