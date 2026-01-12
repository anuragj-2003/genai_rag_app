import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import { Save, User, Sliders, Shield, Trash2, Brain, AlertTriangle } from 'lucide-react';
import api from '../api';

const Settings = () => {
    const { user, logout } = useAuth();
    const { model, setModel, temperature, setTemperature, systemPrompt, setSystemPrompt } = useSettings();

    // Local state for account actions
    const [passwordData, setPasswordData] = useState({ current: '', new: '', confirm: '' });
    const [msg, setMsg] = useState({ type: '', text: '' });

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        if (passwordData.new !== passwordData.confirm) {
            setMsg({ type: 'error', text: 'New passwords do not match' });
            return;
        }
        // Implement API call for password change
        alert("Feature coming soon: Password Change API");
    };

    const clearMemory = async () => {
        if (confirm("Are you sure you want to delete all conversation history? This cannot be undone.")) {
            try {
                // Mock API call or implement real one
                await api.delete('/settings/memory');
                alert("History cleared!");
                window.location.reload(); // Force sidebar refresh
            } catch (err) {
                console.error(err);
            }
        }
    };

    const deleteAccount = async () => {
        if (confirm("CRITICAL: Are you sure you want to delete your account? All data will be lost forever.")) {
            await api.delete('/settings/account');
            alert("Account deleted.");
            logout();
        }
    };

    return (
        <div className="flex bg-black min-h-screen text-white p-6 overflow-y-auto">
            <div className="max-w-4xl mx-auto w-full space-y-8 pb-20">

                <header className="mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-violet-500 bg-clip-text text-transparent">
                        Settings
                    </h1>
                    <p className="text-zinc-500">Manage your preferences, behavior, and account</p>
                </header>

                {msg.text && (
                    <div className={`p-4 rounded-xl ${msg.type === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                        {msg.text}
                    </div>
                )}

                {/* AI Model Settings */}
                <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-full bg-violet-600/20 flex items-center justify-center text-violet-400">
                            <Sliders size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">AI Configuration</h2>
                            <p className="text-zinc-400 text-sm">Customize the agent's intelligence</p>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-zinc-400 mb-2">Model</label>
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="w-full bg-black border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-violet-500 outline-none"
                            >
                                <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Versatile)</option>
                                <option value="llama-3.1-8b-instant">Llama 3.1 8B (Instant)</option>
                                <option value="openai/gpt-oss-120b">GPT-OSS 120B</option>
                                <option value="qwen/qwen3-32b">Qwen 3 32B</option>
                                <option value="groq/compound">Groq Compound</option>
                            </select>
                        </div>

                        <div>
                            <div className="flex justify-between mb-2">
                                <label className="block text-sm font-medium text-zinc-400">Temperature: {temperature}</label>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={temperature}
                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                className="w-full h-2 bg-zinc-800 rounded-full appearance-none cursor-pointer accent-violet-500 hover:accent-violet-400"
                            />
                        </div>
                    </div>
                </section>

                {/* Behavior / System Prompt */}
                <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400">
                            <Brain size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">Agent Behavior</h2>
                            <p className="text-zinc-400 text-sm">Define how the AI should act</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <label className="block text-sm font-medium text-zinc-400">System Prompt</label>
                        <textarea
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            className="w-full h-32 bg-black border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                            placeholder="e.g., You are a strict coding assistant..."
                        />
                        {/* Changes persist automatically via Context */}
                    </div>
                </section>

                {/* Account Security */}
                <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-full bg-emerald-600/20 flex items-center justify-center text-emerald-400">
                            <Shield size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">Security</h2>
                            <p className="text-zinc-400 text-sm">Manage your account credentials</p>
                        </div>
                    </div>

                    <form onSubmit={handlePasswordChange} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input
                                type="password"
                                placeholder="Current Password"
                                value={passwordData.current}
                                onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })}
                                className="w-full bg-black border border-zinc-800 rounded-lg p-3 text-white focus:border-violet-500 outline-none transition-colors"
                            />
                            <input
                                type="password"
                                placeholder="New Password"
                                value={passwordData.new}
                                onChange={(e) => setPasswordData({ ...passwordData, new: e.target.value })}
                                className="w-full bg-black border border-zinc-800 rounded-lg p-3 text-white focus:border-violet-500 outline-none transition-colors"
                            />
                            <input
                                type="password"
                                placeholder="Confirm New Password"
                                value={passwordData.confirm}
                                onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })}
                                className="w-full bg-black border border-zinc-800 rounded-lg p-3 text-white focus:border-violet-500 outline-none transition-colors"
                            />
                        </div>
                        <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                            Update Password
                        </button>
                    </form>
                </section>

                {/* Danger Zone */}
                <section className="border border-red-900/30 bg-red-900/5 rounded-2xl p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-full bg-red-600/20 flex items-center justify-center text-red-500">
                            <AlertTriangle size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-red-500">Danger Zone</h2>
                            <p className="text-red-400/60 text-sm">Irreversible actions</p>
                        </div>
                    </div>

                    <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between p-4 border border-zinc-800 rounded-xl bg-black/40">
                            <div>
                                <h3 className="font-medium text-white">Clear Conversation History</h3>
                                <p className="text-xs text-zinc-500">Deletes all saved chats and memory</p>
                            </div>
                            <button onClick={clearMemory} className="text-red-400 hover:text-red-300 hover:bg-red-900/20 px-4 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm">
                                <Trash2 size={16} /> Delete All
                            </button>
                        </div>

                        <div className="flex items-center justify-between p-4 border border-zinc-800 rounded-xl bg-black/40">
                            <div>
                                <h3 className="font-medium text-white">Delete Account</h3>
                                <p className="text-xs text-zinc-500">Permanently delete your account and data</p>
                            </div>
                            <button onClick={deleteAccount} className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm">
                                <Trash2 size={16} /> Delete Account
                            </button>
                        </div>
                    </div>
                </section>

            </div>
        </div>
    );
};

export default Settings;
