import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add token
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

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me')
};

// Users
export const usersAPI = {
  list: (role) => api.get('/users', { params: { role } }),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`)
};

// Contracts
export const contractsAPI = {
  list: (params) => api.get('/contracts', { params }),
  get: (id) => api.get(`/contracts/${id}`),
  create: (data) => api.post('/contracts', data),
  update: (id, data) => api.put(`/contracts/${id}`, data),
  review: (id) => api.post(`/contracts/${id}/review`),
  approve: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/contracts/${id}/approve`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadSigned: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/contracts/${id}/upload-signed`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  downloadFile: (fileId) => {
    const token = localStorage.getItem('token');
    return `${process.env.REACT_APP_BACKEND_URL}/api/files/view/${fileId}?token=${token}`;
  }
};

// Documents (associated to contracts)
export const documentsAPI = {
  getContractDocuments: (contractId) => api.get(`/contracts/${contractId}/documents`),
  uploadContractDocument: (contractId, documentType, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/contracts/${contractId}/documents?document_type=${documentType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  review: (id, data) => api.put(`/documents/${id}/review`, data),
  getExpiring: (days) => api.get('/documents/expiring', { params: { days } }),
  downloadFile: (fileId) => {
    const token = localStorage.getItem('token');
    return `${process.env.REACT_APP_BACKEND_URL}/api/files/view/${fileId}?token=${token}`;
  }
};

// Payments
export const paymentsAPI = {
  list: (params) => api.get('/payments', { params }),
  create: (data) => api.post('/payments', data),
  uploadBill: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/payments/${id}/upload-bill`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  approve: (id) => api.post(`/payments/${id}/approve`),
  reject: (id, reason) => api.post(`/payments/${id}/reject`, null, {
    params: { rejection_reason: reason }
  }),
  confirm: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/payments/${id}/confirm`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  downloadFile: (fileId) => {
    const token = localStorage.getItem('token');
    return `${process.env.REACT_APP_BACKEND_URL}/api/files/view/${fileId}?token=${token}`;
  }
};

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats')
};

// Reports
export const reportsAPI = {
  contractsPending: () => api.get('/reports/contracts-pending'),
  contractsActive: () => api.get('/reports/contracts-active'),
  paymentsPending: () => api.get('/reports/payments-pending'),
  exportContracts: (status) => {
    const token = localStorage.getItem('token');
    const params = new URLSearchParams();
    params.append('token', token);
    if (status) params.append('status', status);
    window.open(`${process.env.REACT_APP_BACKEND_URL}/api/reports/export/contracts?${params.toString()}`, '_blank');
  },
  exportPayments: (status) => {
    const token = localStorage.getItem('token');
    const params = new URLSearchParams();
    params.append('token', token);
    if (status) params.append('status', status);
    window.open(`${process.env.REACT_APP_BACKEND_URL}/api/reports/export/payments?${params.toString()}`, '_blank');
  }
};

// Notifications
export const notificationsAPI = {
  list: (limit) => api.get('/notifications', { params: { limit } }),
  markRead: (id) => api.put(`/notifications/${id}/read`)
};

export default api;
