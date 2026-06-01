import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: 90000, // 90 seconds (model loading on first request)
    withCredentials: true, // Send cookies (refresh_token, guest_token)
});

// Add Bearer token to every request
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

// Auto-refresh on 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;
            try {
                const res = await axios.post(
                    `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
                    {},
                    { withCredentials: true }
                );
                const newToken = res.data.access_token;
                localStorage.setItem('token', newToken);
                original.headers.Authorization = `Bearer ${newToken}`;
                return api(original);
            } catch {
                localStorage.removeItem('token');
            }
        }
        return Promise.reject(error);
    }
);

export default api;
