import React, { useState, useEffect } from 'react';
import { Plus, MessageSquare, LogOut, Settings as SettingsIcon, Menu, X, MoreVertical, Pencil, Trash2, Pin, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const Sidebar = ({ onNewChat, onSelectChat, currentChatId }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [history, setHistory] = useState([]);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        if (currentChatId || user) fetchHistory();
    }, [currentChatId, user]);

    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState("");
    const [deleteId, setDeleteId] = useState(null); // ID of chat to delete (triggers confirmation)

    useEffect(() => {
        if (currentChatId || user) fetchHistory();
    }, [currentChatId, user]);

    const fetchHistory = async () => {
        try {
            const res = await api.get('/chat/history');
            setHistory(res.data);
        } catch (err) {
            console.error("Failed fetching history", err);
        }
    };

    const handlePin = async (e, chat) => {
        e.stopPropagation();
        try {
            // Optimistic update
            const newPinned = !chat.is_pinned;
            setHistory(history.map(c => c.id === chat.id ? { ...c, is_pinned: newPinned } : c).sort((a, b) => (b.is_pinned - a.is_pinned)));

            await api.put(`/chat/conversations/${chat.id}`, { is_pinned: newPinned });
            fetchHistory(); // Refresh to ensure sync
        } catch (err) {
            console.error("Failed to pin", err);
            fetchHistory(); // Revert on error
        }
    };

    const startEditing = (e, chat) => {
        e.stopPropagation();
        setEditingId(chat.id);
        setEditTitle(chat.title);
    };

    const saveTitle = async (id) => {
        if (!editTitle.trim()) return;
        try {
            setHistory(history.map(c => c.id === id ? { ...c, title: editTitle } : c));
            setEditingId(null);
            await api.put(`/chat/conversations/${id}`, { title: editTitle });
            fetchHistory();
        } catch (err) {
            console.error("Failed to rename", err);
        }
    };

    const handleDelete = async () => {
        if (!deleteId) return;
        try {
            setHistory(history.filter(c => c.id !== deleteId));
            if (currentChatId === deleteId) {
                onNewChat();
                navigate('/');
            }
            setDeleteId(null);
            await api.delete(`/chat/conversations/${deleteId}`);
        } catch (err) {
            console.error("Failed to delete", err);
            fetchHistory();
        }
    };

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <div className={`fixed inset-y-0 left-0 z-50 w-72 bg-zinc-950 border-r border-zinc-900 flex flex-col h-full transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0`}>

                {/* Header */}
                <div className="p-6 border-b border-zinc-900 flex items-center justify-between">
                    <div className="flex items-center gap-3 font-bold text-xl tracking-tight text-white">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-violet-600 flex items-center justify-center text-white text-lg">
                            AI
                        </div>
                        Workspace
                    </div>
                </div>

                {/* New Chat Action */}
                <div className="p-4">
                    <button
                        onClick={() => { onNewChat(); navigate('/'); setIsOpen(false); }}
                        className="w-full group flex items-center justify-center gap-2 bg-white text-black hover:bg-zinc-200 font-semibold py-3 px-4 rounded-xl transition-all shadow-lg active:scale-95"
                    >
                        <Plus size={20} className="group-hover:rotate-90 transition-transform duration-300" />
                        New Chat
                    </button>
                </div>

                {/* History List */}
                <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
                    <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-3 py-2 mb-1">Recent Chats</div>
                    {history.length === 0 && (
                        <div className="text-center text-zinc-600 py-8 text-sm italic">No history yet</div>
                    )}
                    {history.map((chat) => (
                        <button
                            key={chat.id}
                            onClick={() => { onSelectChat(chat.id); setIsOpen(false); }}
                            className={`w-full text-left px-3 py-3 rounded-lg flex items-center gap-3 text-sm transition-all group ${currentChatId === chat.id
                                ? 'bg-zinc-900 text-white border border-zinc-800'
                                : 'text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200 border border-transparent'
                                }`}
                        >
                            {editingId === chat.id ? (
                                <div className="flex items-center gap-2 flex-1" onClick={e => e.stopPropagation()}>
                                    <input
                                        autoFocus
                                        className="bg-zinc-800 text-white text-sm px-2 py-1 rounded w-full outline-none border border-blue-500"
                                        value={editTitle}
                                        onChange={(e) => setEditTitle(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') saveTitle(chat.id);
                                            if (e.key === 'Escape') setEditingId(null);
                                        }}
                                        onBlur={() => saveTitle(chat.id)}
                                    />
                                    <button onClick={() => saveTitle(chat.id)} className="text-green-500 hover:text-green-400"><Check size={14} /></button>
                                </div>
                            ) : (
                                <>
                                    <MessageSquare size={16} className={currentChatId === chat.id ? 'text-blue-500' : 'text-zinc-600 group-hover:text-zinc-400'} />
                                    <span className="truncate flex-1">{chat.title}</span>

                                    {/* Action Buttons (Visible on Hover or if Pinned) */}
                                    <div className={`flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${chat.is_pinned ? 'opacity-100' : ''}`}>
                                        <button
                                            onClick={(e) => handlePin(e, chat)}
                                            className={`p-1 rounded hover:bg-zinc-700 ${chat.is_pinned ? 'text-blue-400' : 'text-zinc-500 hover:text-white'}`}
                                            title={chat.is_pinned ? "Unpin" : "Pin"}
                                        >
                                            <Pin size={12} className={chat.is_pinned ? "fill-current" : ""} />
                                        </button>
                                        <button
                                            onClick={(e) => startEditing(e, chat)}
                                            className="p-1 rounded hover:bg-zinc-700 text-zinc-500 hover:text-white"
                                            title="Rename"
                                        >
                                            <Pencil size={12} />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setDeleteId(chat.id); }}
                                            className="p-1 rounded hover:bg-zinc-700 text-zinc-500 hover:text-red-400"
                                            title="Delete"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                </>
                            )}
                        </button>
                    ))}
                </div>

                {/* Delete Confirmation Modal */}
                {deleteId && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl max-w-sm w-full">
                            <h3 className="text-lg font-bold text-white mb-2">Delete Chat?</h3>
                            <p className="text-zinc-400 text-sm mb-6">This will permanently delete this conversation and all its messages. This action cannot be undone.</p>
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setDeleteId(null)}
                                    className="px-4 py-2 rounded-xl text-zinc-400 hover:bg-zinc-800 transition-colors text-sm font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleDelete}
                                    className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white transition-colors text-sm font-medium"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* User Footer */}
                <div className="p-4 bg-zinc-900/30 border-t border-zinc-900">
                    <div className="flex items-center gap-3 mb-4 p-2 rounded-lg hover:bg-zinc-900 transition-colors cursor-pointer" onClick={() => window.location.href = '/settings'}>
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-900 border border-zinc-700 flex items-center justify-center text-sm font-bold text-white shadow-inner">
                            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="text-sm font-medium truncate text-white">{user?.full_name || 'User'}</p>
                            <p className="text-xs text-zinc-500 truncate">{user?.email}</p>
                        </div>
                        <SettingsIcon size={16} className="text-zinc-600" />
                    </div>

                    <div className="grid grid-cols-1">
                        <button
                            onClick={logout}
                            className="flex items-center justify-center gap-2 p-2 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/5 transition-colors text-sm w-full border border-transparent hover:border-red-500/10"
                        >
                            <LogOut size={16} /> Sign Out
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Toggle Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="md:hidden fixed top-4 left-4 z-50 p-2.5 bg-zinc-900/90 backdrop-blur border border-zinc-800 text-white rounded-xl shadow-xl active:scale-95 transition-all"
                >
                    <Menu size={20} />
                </button>
            )}
        </>
    );
};

export default Sidebar;
