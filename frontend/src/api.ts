import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pos_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config;
    const url = originalRequest?.url || '';

    if (
      err.response?.status === 401 &&
      originalRequest &&
      !(originalRequest as any)._retry &&
      !url.includes('/api/auth/login') &&
      !url.includes('/api/auth/refresh') &&
      !url.includes('/api/auth/logout')
    ) {
      (originalRequest as any)._retry = true;
      try {
        const refreshResponse = await api.post('/api/auth/refresh');
        const { access_token, user } = refreshResponse.data;
        localStorage.setItem('pos_token', access_token);
        localStorage.setItem('pos_user', JSON.stringify(user));
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.removeItem('pos_token');
        localStorage.removeItem('pos_user');
      }
    }

    if (err.response?.status === 401) {
      localStorage.removeItem('pos_token');
      localStorage.removeItem('pos_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
