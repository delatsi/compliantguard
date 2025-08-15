import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/api/v1/auth/login', { email, password }),
  register: (userData) => api.post('/api/v1/auth/register', userData),
  verifyToken: (token) => api.get('/api/v1/auth/verify', {
    headers: { Authorization: `Bearer ${token}` }
  }),
};

export const complianceAPI = {
  triggerScan: (projectId) => api.post('/api/v1/scan', { project_id: projectId }),
  getReport: (scanId) => api.get(`/api/v1/reports/${scanId}`),
  listReports: (params = {}) => api.get('/api/v1/reports', { params }),
  getDashboard: () => api.get('/api/v1/dashboard'),
};

export const userAPI = {
  getProfile: () => api.get('/api/v1/user/profile'),
  updateProfile: (data) => api.put('/api/v1/user/profile', data),
  changePassword: (data) => api.put('/api/v1/user/password', data),
};

export const gcpAPI = {
  // Upload GCP credentials via JSON
  uploadCredentials: (projectId, serviceAccountJson) => 
    api.post('/gcp/credentials', {
      project_id: projectId,
      service_account_json: serviceAccountJson
    }),
  
  // Upload GCP credentials via file
  uploadCredentialsFile: (projectId, file) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);
    return api.post('/api/v1/gcp/credentials/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  // List connected GCP projects
  listProjects: () => api.get('/api/v1/gcp/projects'),
  
  // Check project connection status
  getProjectStatus: (projectId) => api.get(`/api/v1/gcp/projects/${projectId}/status`),
  
  // Revoke GCP credentials
  revokeCredentials: (projectId) => api.delete(`/api/v1/gcp/projects/${projectId}/credentials`),
};

export default api;