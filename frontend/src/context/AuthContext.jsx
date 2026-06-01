import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchUser = async () => {
        try {
            const res = await api.get('/api/v1/auth/me');
            setUser(res.data);
        } catch (err) {
            if (err.response?.status === 401) {
                localStorage.removeItem('token');
                setUser(null);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUser();
    }, []);

    const login = async (username, password) => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            const res = await api.post('/api/v1/auth/token', formData);
            const token = res.data.access_token;
            localStorage.setItem('token', token);
            await fetchUser();
        } finally {
            setLoading(false);
        }
    };

    const signup = async (email, password, fullName) => {
        await api.post('/api/v1/auth/signup', { email, password, full_name: fullName });
    };

    const verifyOtp = async (email, otp, newPassword = null) => {
        return await api.post('/api/v1/auth/verify-otp', { email, otp, new_password: newPassword });
    };

    const forgotPassword = async (email) => {
        return await api.post('/api/v1/auth/forgot-password', { email });
    };

    const resetPassword = async (email, otp, newPassword) => {
        return await api.post('/api/v1/auth/verify-otp', { email, otp, new_password: newPassword });
    };

    const startGuestSession = async () => {
        const res = await api.post('/api/v1/auth/guest');
        if (res.data?.access_token) {
            localStorage.setItem('token', res.data.access_token);
        }
        await fetchUser();
        // Errors are intentionally NOT caught here — let callers handle them
    };

    const logout = async () => {
        try {
            await api.post('/api/v1/auth/logout');
        } catch { /* ignore */ }
        localStorage.removeItem('token');
        setUser(null);
    };

    const refreshUser = async () => {
        await fetchUser();
    };

    const isAuthenticated = !!user && !user.is_guest;

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated,
            loading,
            login,
            signup,
            logout,
            verifyOtp,
            forgotPassword,
            resetPassword,
            startGuestSession,
            refreshUser,
        }}>
            {children}
        </AuthContext.Provider>
    );
};
