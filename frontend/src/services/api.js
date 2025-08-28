import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

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

// Documentation API
export const documentationAPI = {
  // List user documentation
  listDocuments: (complianceLevel = null) => {
    const params = complianceLevel ? `?compliance_level=${complianceLevel}` : '';
    return api.get(`/api/v1/documentation${params}`);
  },
  
  // Get specific document content
  getDocument: (documentId) => api.get(`/api/v1/documentation/${documentId}`),
  
  // Generate compliance-specific documentation
  generateDocuments: () => api.post('/api/v1/documentation/generate', {}),
  
  // Migrate existing documentation templates to user-specific system
  migrateDocs: () => api.post('/api/v1/documentation/migrate', {}),
};

// Compliance Roadmap API
export const roadmapAPI = {
  // Get complete compliance roadmap with user progress
  getRoadmap: () => api.get('/api/v1/roadmap'),
  
  // Update milestone progress
  updateMilestone: (milestoneId, status, notes = '', completionDate = null) => 
    api.put('/api/v1/roadmap/milestone', {
      milestone_id: milestoneId,
      status: status,
      notes: notes,
      completion_date: completionDate
    }),
  
  // Get progress summary and analytics
  getProgressSummary: () => api.get('/api/v1/roadmap/progress'),
};

// Billing & Subscription API
export const billingAPI = {
  // Get available pricing plans
  getPlans: () => api.get('/api/v1/billing/plans'),
  
  // Get user's current subscription
  getSubscription: () => api.get('/api/v1/billing/subscription'),
  
  // Create a Stripe customer
  createCustomer: (customerData) => api.post('/api/v1/billing/create-customer', customerData),
  
  // Create a subscription
  createSubscription: (subscriptionData) => api.post('/api/v1/billing/create-subscription', subscriptionData),
  
  // Create billing portal session
  createPortalSession: (data) => api.post('/api/v1/billing/create-portal-session', data),
};

export default api;