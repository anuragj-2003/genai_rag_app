import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8002',
    timeout: 10000, // 10 seconds timeout
});

// Add a request interceptor to include the token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;
