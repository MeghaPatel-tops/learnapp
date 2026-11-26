import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 30000,
});

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

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isAuthRoute = window.location.pathname.startsWith('/login') || 
                          window.location.pathname.startsWith('/reset-password') || 
                          window.location.pathname.startsWith('/forgot-password') ||
                          window.location.pathname.startsWith('/verify-certificate');
      if (!isAuthRoute) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login?expired=1';
      }
    }
    return Promise.reject(error);
  }
);

export const getApiErrorMessage = (error) => {
  if (error.response?.data) {
    const data = error.response.data;
    if (data.error?.message) return data.error.message;
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((err) => `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`).join(', ');
    }
    if (data.message) return data.message;
  }
  return error.message || 'An unexpected server error occurred';
};

export default api;
