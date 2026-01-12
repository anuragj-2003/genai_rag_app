import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Loader2, KeyRound } from 'lucide-react';

const Login = () => {
    const [mode, setMode] = useState('login'); // login, signup, forgot, verify, reset
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');

    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    const { login, signup, verifyOtp, forgotPassword, resetPassword } = useAuth();
    const navigate = useNavigate();

    const handleAuth = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        setSuccessMsg('');

        try {
            if (mode === 'login') {
                await login(email, password);
                navigate('/');
            } else if (mode === 'signup') {
                if (password !== confirmPassword) {
                    throw new Error("Passwords do not match");
                }
                await signup(email, password, fullName);
                setMode('verify'); // Go to OTP verification
                setSuccessMsg(`Account created! OTP sent to ${email} (Check server console)`);
            } else if (mode === 'verify') {
                await verifyOtp(email, otp);
                setMode('login');
                setSuccessMsg("Account verified! Please login.");
                setOtp('');
            } else if (mode === 'forgot') {
                await forgotPassword(email);
                setMode('reset');
                setSuccessMsg(`OTP sent to ${email} (Check server console)`);
            } else if (mode === 'reset') {
                await resetPassword(email, otp, newPassword);
                setMode('login');
                setSuccessMsg("Password reset! Please login.");
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Action failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-black selection:bg-blue-500/30">

            {/* Ambient Background */}
            <div className="absolute inset-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-800/20 via-black to-black pointer-events-none" />
            <div className="absolute top-0 w-full h-px bg-gradient-to-r from-transparent via-zinc-800 to-transparent opacity-20" />
            <div className="absolute bottom-0 w-full h-px bg-gradient-to-r from-transparent via-blue-900/20 to-transparent opacity-20" />

            {/* Glow Orbs */}
            <div className="absolute top-1/4 -left-20 w-96 h-96 bg-blue-500/10 rounded-full blur-[128px] pointer-events-none" />
            <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-violet-500/10 rounded-full blur-[128px] pointer-events-none" />

            <div className="w-full max-w-md glass-card rounded-2xl p-8 z-10 relative">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white to-white/70">
                        {mode === 'login' && 'Welcome Back'}
                        {mode === 'signup' && 'Create Account'}
                        {mode === 'verify' && 'Verify Email'}
                        {mode === 'forgot' && 'Reset Password'}
                        {mode === 'reset' && 'New Password'}
                    </h1>
                    <p className="text-zinc-500 mt-2 text-sm">
                        {mode === 'login' && 'Enter your credentials to continue'}
                        {mode === 'signup' && 'Join the GenAI Workspace'}
                        {mode === 'verify' && 'Enter the code sent to your email'}
                        {mode === 'forgot' && 'Enter your email to receive a code'}
                        {mode === 'reset' && 'Set your new secure password'}
                    </p>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl mb-6 text-sm flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-400 mb-0.5" /> {error}
                    </div>
                )}

                {successMsg && (
                    <div className="bg-green-500/10 border border-green-500/20 text-green-400 p-3 rounded-xl mb-6 text-sm flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-400 mb-0.5" /> {successMsg}
                    </div>
                )}

                <form onSubmit={handleAuth} className="space-y-4">

                    {/* Full Name - Signup Only */}
                    {mode === 'signup' && (
                        <div className="relative group">
                            <User className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="input-field pl-10"
                                placeholder="Full Name"
                                required
                            />
                        </div>
                    )}

                    {/* Email - All modes except reset (unless we carry it over, but safe to ask/prefetch) */}
                    {(mode === 'login' || mode === 'signup' || mode === 'forgot') && (
                        <div className="relative group">
                            <Mail className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="input-field pl-10"
                                placeholder="name@example.com"
                                required
                            />
                        </div>
                    )}

                    {/* Password Fields */}
                    {(mode === 'login' || mode === 'signup') && (
                        <div className="relative group">
                            <Lock className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input-field pl-10"
                                placeholder="Password"
                                required
                            />
                        </div>
                    )}

                    {mode === 'signup' && (
                        <div className="relative group">
                            <Lock className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="input-field pl-10"
                                placeholder="Confirm Password"
                                required
                            />
                        </div>
                    )}

                    {/* OTP Input */}
                    {(mode === 'verify' || mode === 'reset') && (
                        <div className="space-y-4">
                            {/* Show email for context if verifying/resetting */}
                            <div className="text-center text-zinc-500 text-sm bg-zinc-900/50 py-1 rounded-lg border border-zinc-800">
                                {email}
                            </div>

                            <div className="relative group">
                                <KeyRound className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                                <input
                                    type="text"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    className="input-field pl-10 text-center tracking-widest font-mono text-lg"
                                    placeholder="000000"
                                    maxLength={6}
                                    required
                                />
                            </div>
                        </div>
                    )}

                    {/* New Password for Reset */}
                    {mode === 'reset' && (
                        <div className="relative group">
                            <Lock className="absolute left-3 top-3.5 text-zinc-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="input-field pl-10"
                                placeholder="New Password"
                                required
                            />
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary flex items-center justify-center gap-2 mt-2"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : <span className="flex items-center gap-2">Continue <ArrowRight size={16} /></span>}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-zinc-800/50">
                    <div className="flex flex-col gap-3 text-center text-sm text-zinc-500">
                        {mode === 'login' && (
                            <>
                                <button onClick={() => setMode('forgot')} className="hover:text-blue-400 transition-colors">Forgot Password?</button>
                                <div>
                                    Don't have an account?{' '}
                                    <button onClick={() => setMode('signup')} className="text-blue-400 hover:text-blue-300 font-medium transition-colors">Sign Up</button>
                                </div>
                            </>
                        )}

                        {mode === 'signup' && (
                            <div>
                                Already have an account?{' '}
                                <button onClick={() => setMode('login')} className="text-blue-400 hover:text-blue-300 font-medium transition-colors">Log In</button>
                            </div>
                        )}

                        {(mode === 'img' || mode === 'verify' || mode === 'reset' || mode === 'forgot') && (
                            <button onClick={() => { setMode('login'); setError(''); }} className="text-zinc-400 hover:text-white transition-colors">Back to Login</button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
