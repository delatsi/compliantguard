import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
      return { ...state, loading: false, user: action.payload, token: action.token };
    case 'LOGIN_FAILURE':
      return { ...state, loading: false, error: action.error };
    case 'LOGOUT':
      return { ...state, user: null, token: null };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    token: localStorage.getItem('token'),
    loading: false,
    error: null,
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token on app load
      verifyToken(token);
    }
  }, []);

  const verifyToken = async (token) => {
    try {
      dispatch({ type: 'SET_LOADING', loading: true });
      const response = await authAPI.verifyToken(token);
      
      // Check if we have a valid response with user data
      if (response.data && response.data.user) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: response.data.user, token });
      } else {
        // Invalid response format, treat as invalid token
        console.warn('Token verification returned invalid response format:', response.data);
        localStorage.removeItem('token');
        dispatch({ type: 'LOGOUT' });
      }
    } catch (error) {
      console.warn('Token verification failed:', error.response?.status, error.response?.data);
      // Only remove token if it's definitely invalid (401/403)
      if (error.response?.status === 401 || error.response?.status === 403) {
        localStorage.removeItem('token');
        dispatch({ type: 'LOGOUT' });
      } else {
        // Network error or server error - keep token but don't set user as authenticated
        console.log('Network/server error during token verification, keeping token for retry');
        dispatch({ type: 'SET_LOADING', loading: false });
        return; // Early return to avoid the finally block
      }
    }
    
    // Set loading to false for successful and invalid token cases
    dispatch({ type: 'SET_LOADING', loading: false });
  };

  const login = async (email, password) => {
    try {
      dispatch({ type: 'LOGIN_START' });
      const response = await authAPI.login(email, password);
      
      // Handle our API response format
      const data = response.data;
      const token = data.access_token || data.token;
      const user = {
        id: data.user_id,
        email: data.email,
        role: data.role
      };
      
      localStorage.setItem('token', token);
      dispatch({ type: 'LOGIN_SUCCESS', payload: user, token });
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.message || 'Login failed';
      dispatch({ type: 'LOGIN_FAILURE', error: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'LOGIN_START' });
      const response = await authAPI.register(userData);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      dispatch({ type: 'LOGIN_SUCCESS', payload: user, token });
      return { success: true };
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE', error: error.response?.data?.message || 'Registration failed' });
      return { success: false, error: error.response?.data?.message || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    dispatch({ type: 'LOGOUT' });
  };

  const value = {
    ...state,
    isAuthenticated: !!state.user && !!state.token,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};