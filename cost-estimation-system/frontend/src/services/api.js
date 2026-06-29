import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2-minute timeout to prevent indefinite spinning on large files
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to attach the JWT token
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

export const authAPI = {
  register: (email, password) => 
    api.post('/auth/register', { email, password }),
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  getMe: () => api.get('/auth/me'),
};

// Estimation endpoints
export const estimationAPI = {
  uploadDrawing: (files) => {
    const formData = new FormData();
    // If it's a single file passed incorrectly, or an array, we handle it
    const fileArray = Array.isArray(files) ? files : (files.length ? Array.from(files) : [files]);
    fileArray.forEach(file => {
      formData.append('files', file);
    });
    return api.post('/estimation/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  generateEstimate: (estimationId) =>
    api.post(`/estimation/estimate/${estimationId}`),
  
  getHistory: (skip = 0, limit = 10) =>
    api.get('/estimation/history', { params: { skip, limit } }),
  
  getEstimation: (estimationId) =>
    api.get(`/estimation/${estimationId}`),
    
  exportExcel: (estimationId) =>
    api.get(`/estimation/${estimationId}/export`, { responseType: 'blob' }),
};

// Cost parameters endpoints
export const parametersAPI = {
  getSettings: () => api.get('/parameters/settings'),
  updateSettings: (data) => api.put('/parameters/settings', data),
};

// Marketplace endpoints
export const marketplaceAPI = {
  getQuotes: (estimationId) => api.get(`/marketplace/estimate/${estimationId}/quotes`),
  requestQuotes: (estimationId) => api.post(`/marketplace/estimate/${estimationId}/request_quotes`),
  acceptQuote: (quoteId) => api.post(`/marketplace/quotes/${quoteId}/accept`),
};

// Health check endpoints
export const healthAPI = {
  status: () => api.get('/health/status'),
  ready: () => api.get('/health/ready'),
};

export default api;
