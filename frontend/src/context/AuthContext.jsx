import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchUser = async (token) => {
        try {
            const res = await api.get('/auth/me');
            setUser(res.data);
        } catch (err) {
            console.error("Failed to fetch user:", err.message);
            // If unauthorized and NOT a guest token, logout
            if (err.response?.status === 401 || err.code === 'ECONNABORTED') {
                logout();
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        let token = localStorage.getItem('token');
        if (!token) {
            let guestToken = localStorage.getItem('guest_token');
            if (!guestToken) {
                guestToken = 'guest_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
                localStorage.setItem('guest_token', guestToken);
            }
            localStorage.setItem('token', guestToken);
            token = guestToken;
        }
        fetchUser(token);
    }, []);

    const login = async (username, password) => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await api.post('/auth/token', formData);
            const token = res.data.access_token;
            localStorage.setItem('token', token);
            await fetchUser(token);
        } finally {
            setLoading(false);
        }
    };

    const signup = async (email, password, fullName) => {
        await api.post('/auth/signup', { email, password, full_name: fullName });
    };

    const verifyOtp = async (email, otp) => {
        return await api.post('/auth/verify-otp', { email, otp });
    };

    const forgotPassword = async (email) => {
        return await api.post('/auth/forgot-password', { email });
    };

    const resetPassword = async (email, otp, newPassword) => {
        return await api.post('/auth/verify-otp', { email, otp, new_password: newPassword });
    };

    const logout = () => {
        localStorage.removeItem('token');
        const guestToken = localStorage.getItem('guest_token');
        if (guestToken) {
            localStorage.setItem('token', guestToken);
            fetchUser(guestToken);
        } else {
            setUser(null);
            setLoading(false);
        }
    };

    const refreshUser = async () => {
        const token = localStorage.getItem('token');
        if (token) {
            await fetchUser(token);
        }
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
            refreshUser
        }}>
            {children}
        </AuthContext.Provider>
    );
};
