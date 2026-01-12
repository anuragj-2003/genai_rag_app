import React, { useState, useEffect, useRef } from 'react';
import { Send, Paperclip, Loader2, FileText, Sparkles, Bot, User as UserIcon, ThumbsUp, ThumbsDown, RotateCcw, Edit2, ChevronLeft, ChevronRight, X, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../api';
import { useSettings } from '../context/SettingsContext';
import CodeBlock from '../components/CodeBlock';

// Simple Message Component
const MessageItem = ({ msg, idx, onFeedback, onRerun, onEdit, isEditing, onSaveEdit, onCancelEdit, onVersionChange }) => {
    const [feedback, setFeedback] = useState(null);
    const [editContent, setEditContent] = useState(msg.content);

    // Update edit box when message changes
    useEffect(() => {
        if (isEditing) {
            setEditContent(msg.content);
        }
    }, [isEditing, msg.content]);

    // Version details
    let currentVer = 1;
    if (msg.currentVersionIndex !== undefined) {
        currentVer = msg.currentVersionIndex + 1;
    }

    let totalVer = 1;
    if (msg.versions) {
        totalVer = msg.versions.length;
    }

    const hasMultipleVersions = totalVer > 1;

    return (
        <div className={`group flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}>

            {/* Bot Icon */}
            {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-violet-600 flex-shrink-0 flex items-center justify-center text-white shadow-lg mt-1">
                    <Bot size={16} />
                </div>
            )}

            <div className={`flex flex-col gap-2 ${isEditing ? 'w-full max-w-full' : 'max-w-[85%] md:max-w-[75%]'} ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>

                {/* Edit Mode or View Mode */}
                {isEditing ? (
                    <div className="w-full bg-zinc-800 p-4 rounded-xl border border-zinc-700 shadow-xl animate-in fade-in duration-200">
                        <textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full bg-zinc-900/50 text-white p-3 rounded-lg border border-zinc-700 focus:border-blue-500 outline-none resize-none min-h-[100px] text-sm font-mono leading-relaxed"
                            placeholder="Edit your message..."
                            autoFocus
                        />
                        <div className="flex justify-between items-center mt-3">
                            <div className="text-xs text-zinc-500 italic">
                                Editing will restart the conversation from here.
                            </div>
                            <div className="flex gap-2">
                                <button onClick={onCancelEdit} className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-xs font-medium text-white transition-colors flex items-center gap-1 cursor-pointer">
                                    <X size={12} /> Cancel
                                </button>
                                <button onClick={() => onSaveEdit(idx, editContent)} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-medium text-white transition-colors flex items-center gap-1 cursor-pointer">
                                    <Check size={12} /> Save & Submit
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    // Message Bubble
                    // Removed extra border for assistant as requested
                    <div
                        className={`rounded-2xl px-6 py-4 shadow-sm text-sm md:text-base leading-relaxed overflow-hidden ${msg.role === 'user'
                            ? 'bg-zinc-800 text-white rounded-br-none'
                            : 'bg-transparent text-zinc-100 rounded-tl-none w-full'
                            }`}
                    >
                        {msg.role === 'user' ? (
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                        ) : (
                            <div className="markdown-body">
                                <ReactMarkdown
                                    children={msg.content}
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        code({ node, inline, className, children, ...props }) {
                                            const match = /language-(\w+)/.exec(className || '');
                                            if (!inline && match) {
                                                const codeString = String(children).replace(/\n$/, '');
                                                return (
                                                    <CodeBlock
                                                        language={match[1]}
                                                        value={codeString}
                                                        {...props}
                                                    />
                                                );
                                            } else {
                                                return (
                                                    <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-sm font-mono text-zinc-200" {...props}>
                                                        {children}
                                                    </code>
                                                );
                                            }
                                        },
                                        p: ({ children }) => <p className="mb-4 last:mb-0 leading-7">{children}</p>,
                                        ul: ({ children }) => <ul className="list-disc pl-4 mb-4 space-y-1">{children}</ul>,
                                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-4 space-y-1">{children}</ol>,
                                        li: ({ children }) => <li className="mb-1">{children}</li>,
                                        h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>,
                                        h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-5">{children}</h2>,
                                        h3: ({ children }) => <h3 className="text-lg font-bold mb-2 mt-4">{children}</h3>,
                                        blockquote: ({ children }) => <blockquote className="border-l-4 border-zinc-500 pl-4 py-1 italic text-zinc-400 mb-4 bg-zinc-900/50 rounded-r">{children}</blockquote>,
                                        a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline cursor-pointer">{children}</a>
                                    }}
                                />
                            </div>
                        )}

                        {/* Sources Section */}
                        {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                            <div className="mt-4 pt-3 border-t border-zinc-800/50">
                                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                                    <FileText size={12} /> Sources
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {msg.sources.map((source, i) => (
                                        <a key={i} href={source.url || '#'} className="max-w-xs truncate bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-md hover:bg-zinc-800 hover:border-zinc-700 transition-all text-xs text-zinc-400 block cursor-pointer">
                                            {source.title || "Document"}
                                        </a>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Action Buttons (Edit, Feedback, Rerun) */}
                {!isEditing && (
                    <div className={`flex items-center gap-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>

                        {/* Version Buttons */}
                        {hasMultipleVersions && (
                            <div className="flex items-center text-zinc-600 text-xs mr-2 select-none bg-zinc-900/50 rounded-full px-2 py-0.5 border border-zinc-800">
                                <button
                                    onClick={() => onVersionChange(idx, -1)}
                                    disabled={currentVer <= 1}
                                    className={`p-1 hover:text-white transition-colors cursor-pointer ${currentVer <= 1 ? 'opacity-30 cursor-not-allowed' : ''}`}
                                >
                                    <ChevronLeft size={12} />
                                </button>
                                <span className="mx-1 font-mono min-w-[20px] text-center">{currentVer}/{totalVer}</span>
                                <button
                                    onClick={() => onVersionChange(idx, 1)}
                                    disabled={currentVer >= totalVer}
                                    className={`p-1 hover:text-white transition-colors cursor-pointer ${currentVer >= totalVer ? 'opacity-30 cursor-not-allowed' : ''}`}
                                >
                                    <ChevronRight size={12} />
                                </button>
                            </div>
                        )}

                        {msg.role === 'assistant' ? (
                            <>
                                <button
                                    onClick={() => { onFeedback(idx, 'up'); setFeedback('up'); }}
                                    className={`p-1 transition-all cursor-pointer ${feedback === 'up' ? 'text-green-400 scale-110' : 'text-zinc-500 hover:text-green-400'}`}
                                    title="Helpful">
                                    <ThumbsUp size={14} fill={feedback === 'up' ? "currentColor" : "none"} />
                                </button>
                                <button
                                    onClick={() => { onFeedback(idx, 'down'); setFeedback('down'); }}
                                    className={`p-1 transition-all cursor-pointer ${feedback === 'down' ? 'text-red-400 scale-110' : 'text-zinc-500 hover:text-red-400'}`}
                                    title="Not Helpful">
                                    <ThumbsDown size={14} fill={feedback === 'down' ? "currentColor" : "none"} />
                                </button>
                                <button onClick={() => onRerun(idx)} className="p-1 text-zinc-500 hover:text-blue-400 transition-colors cursor-pointer" title="Regenerate"><RotateCcw size={14} /></button>
                            </>
                        ) : (
                            <button onClick={() => onEdit(idx)} className="p-1 text-zinc-500 hover:text-white transition-colors cursor-pointer" title="Edit"><Edit2 size={14} /></button>
                        )}
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex-shrink-0 flex items-center justify-center text-zinc-400 mt-1">
                    <UserIcon size={16} />
                </div>
            )}
        </div>
    );
};

const Chat = ({ currentChatId }) => {
    // State variables
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [editingIndex, setEditingIndex] = useState(null);

    // Refs
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const inputRef = useRef(null);

    // Settings
    const { model, systemPrompt } = useSettings();

    // Effect to load messages on chat change
    useEffect(() => {
        if (currentChatId) {
            loadMessages(currentChatId);
        } else {
            setMessages([]);
        }
    }, [currentChatId]);

    // Effect to scroll to bottom on new messages (with slight delay)
    useEffect(() => {
        setTimeout(() => {
            scrollToBottom();
        }, 100);
    }, [messages.length, loading]);

    // Helper to scroll
    const scrollToBottom = () => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    };

    // Load message history from backend
    const loadMessages = async (id) => {
        try {
            const res = await api.get(`/chat/history/${id}`);
            let rawData = [];
            if (Array.isArray(res.data)) {
                rawData = res.data;
            }

            // Convert simple backend messages to frontend versioned format
            const formattedMessages = rawData.map(msg => {
                return {
                    ...msg,
                    versions: [{ content: msg.content, sources: msg.sources }],
                    currentVersionIndex: 0
                };
            });

            setMessages(formattedMessages);
            setTimeout(scrollToBottom, 100);

        } catch (error) {
            console.error("Failed to load history:", error);
            setMessages([]);
        }
    };

    // Handle File Upload
    const handleFileChange = async (e) => {
        try {
            const selectedFile = e.target.files[0];
            if (!selectedFile) return;

            setUploading(true);
            const formData = new FormData();
            formData.append('file', selectedFile);

            // Nested try-catch for API call specifically
            try {
                await api.post('/documents/upload', formData);
                setFile(selectedFile);
            } catch (uploadError) {
                console.error("Upload Error:", uploadError);
                alert("Could not upload file.");
            }

        } catch (err) {
            console.error("General file error:", err);
        } finally {
            setUploading(false);
        }
    };

    // Core Chat API function with RETRY LOGIC
    const callChatApi = async (messageText, tempFile, currentHistory, targetIndex = null, isRerun = false) => {
        setLoading(true);
        let attempt = 0;
        const maxAttempts = 2;
        let success = false;

        while (attempt <= maxAttempts && !success) {
            try {
                // Simplify history for backend
                const historyForBackend = currentHistory.map(m => {
                    return {
                        role: m.role,
                        content: m.content
                    };
                });

                const payload = {
                    message: messageText + (tempFile ? ` (Context: Processed file ${tempFile.name})` : ''),
                    conversation_id: currentChatId,
                    model: model,
                    system_prompt: systemPrompt
                };

                const res = await api.post('/chat/', payload);

                const newContent = res.data.response;
                const newSources = res.data.sources;

                // Success! Update State
                setMessages(prev => {
                    const newMsgs = [...prev];

                    if (isRerun && targetIndex !== null) {
                        // We are updating an existing message (Rerun)
                        const targetMsg = newMsgs[targetIndex];

                        // Add new version
                        let newVersions = [];
                        if (targetMsg.versions) {
                            newVersions = [...targetMsg.versions];
                        }
                        newVersions.push({ content: newContent, sources: newSources });

                        newMsgs[targetIndex] = {
                            ...targetMsg,
                            content: newContent,
                            sources: newSources,
                            versions: newVersions,
                            currentVersionIndex: newVersions.length - 1
                        };
                    } else {
                        // New Assistant Message
                        const botMsg = {
                            role: 'assistant',
                            content: newContent,
                            sources: newSources,
                            versions: [{ content: newContent, sources: newSources }],
                            currentVersionIndex: 0
                        };
                        newMsgs.push(botMsg);
                    }
                    return newMsgs;
                });

                success = true; // Break loop

            } catch (apiError) {
                console.error(`API Attempt ${attempt + 1} failed:`, apiError);
                attempt++;

                // On final failure
                if (attempt > maxAttempts && !isRerun) {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: "Error: Could not get response after retrying. Please check your connection.",
                        versions: [],
                        currentVersionIndex: 0
                    }]);
                }
            }
        }

        setLoading(false);
    };

    // Send Message Handler
    const sendMessage = async (e) => {
        e.preventDefault();

        if ((!input.trim() && !file) || loading) return;

        const textToSend = input;
        const fileToSend = file;

        // Reset inputs
        setInput('');
        setFile(null);

        // Optimistically add user message
        const userMsg = {
            role: 'user',
            content: textToSend + (fileToSend ? `\n[Attached: ${fileToSend.name}]` : ''),
            versions: [{ content: textToSend, sources: [] }],
            currentVersionIndex: 0
        };

        const updatedMsgs = [...messages, userMsg];
        setMessages(updatedMsgs);

        // Call API
        await callChatApi(textToSend, fileToSend, updatedMsgs);
    };

    // Feedback Handler
    const handleFeedback = async (idx, type) => {
        try {
            await api.post('/feedback/', {
                message_id: currentChatId || 'unknown',
                type: type,
                comment: `Feedback for msg index ${idx}`
            });
        } catch (err) {
            console.error("Feedback failed:", err);
        }
    };

    // Rerun Handler
    const handleRerun = async (idx) => {
        if (idx === 0) return;

        const msgsBefore = messages.slice(0, idx);
        const lastUserMsg = msgsBefore[msgsBefore.length - 1];

        await callChatApi(lastUserMsg.content, null, msgsBefore, idx, true);
    };

    // Edit Handlers
    const handleEdit = (idx) => {
        setEditingIndex(idx);
    };

    const handleSaveEdit = async (idx, newContent) => {
        setEditingIndex(null);

        // 1. Truncate future (Branching)
        const branchHistory = messages.slice(0, idx + 1);
        const targetMsg = branchHistory[idx];

        // 2. Add version to User Message
        let newVersions = [];
        if (targetMsg.versions) newVersions = [...targetMsg.versions];
        newVersions.push({ content: newContent, sources: [] });

        const updatedUserMsg = {
            ...targetMsg,
            content: newContent,
            versions: newVersions,
            currentVersionIndex: newVersions.length - 1
        };
        branchHistory[idx] = updatedUserMsg;

        setMessages(branchHistory);

        // 3. Get new response
        await callChatApi(newContent, null, branchHistory);
    };

    const handleCancelEdit = () => {
        setEditingIndex(null);
    };

    // Version Navigation
    const handleVersionChange = (idx, direction) => {
        setMessages(prev => {
            const newMsgs = [...prev];
            const msg = newMsgs[idx];
            const newIdx = msg.currentVersionIndex + direction;

            if (newIdx >= 0 && newIdx < msg.versions.length) {
                const ver = msg.versions[newIdx];
                newMsgs[idx] = {
                    ...msg,
                    content: ver.content,
                    sources: ver.sources,
                    currentVersionIndex: newIdx
                };
            }
            return newMsgs;
        });
    };

    return (
        <div className="flex flex-col h-full max-w-5xl mx-auto w-full relative">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 custom-scrollbar">

                {/* Empty State */}
                {messages.length === 0 && !loading && (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-6">
                        <div className="w-20 h-20 bg-zinc-900 rounded-3xl flex items-center justify-center border border-zinc-800 shadow-2xl">
                            <Sparkles className="text-blue-500" size={32} />
                        </div>
                        <div className="text-center max-w-md">
                            <h3 className="text-xl font-semibold text-white mb-2">How can I help you today?</h3>
                            <p className="text-zinc-500">Active Model: <span className="text-blue-400">{model}</span></p>
                            <p className="text-zinc-600 text-xs mt-2">I strictly follow your instructions and verify logic.</p>
                        </div>
                    </div>
                )}

                {/* Message List */}
                {messages.map((msg, idx) => (
                    <MessageItem
                        key={idx}
                        msg={msg}
                        idx={idx}
                        onFeedback={handleFeedback}
                        onRerun={handleRerun}
                        onEdit={handleEdit}
                        isEditing={idx === editingIndex}
                        onSaveEdit={handleSaveEdit}
                        onCancelEdit={handleCancelEdit}
                        onVersionChange={handleVersionChange}
                    />
                ))}

                {/* Loading State */}
                {loading && (
                    <div className="flex justify-start gap-4">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-violet-600 flex-shrink-0 flex items-center justify-center text-white shadow-lg animate-pulse mt-1">
                            <Bot size={16} />
                        </div>
                        <div className="bg-transparent border border-zinc-800 rounded-2xl rounded-tl-none px-6 py-4 flex items-center gap-3 text-zinc-400">
                            <Loader2 className="animate-spin text-blue-500" size={18} />
                            <span className="text-sm">Thinking & Validating...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 md:p-6 bg-black/80 backdrop-blur-md sticky bottom-0 z-20">
                <div className="max-w-4xl mx-auto">

                    {/* Attached File */}
                    {file && (
                        <div className="mb-3 inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 px-4 py-2 rounded-xl text-sm border border-blue-500/20 shadow-lg shadow-blue-900/10">
                            <FileText size={14} />
                            <span className="font-medium max-w-xs truncate">{file.name}</span>
                            <button onClick={() => setFile(null)} className="ml-2 hover:text-white p-1 rounded-full hover:bg-blue-500/20 transition-colors cursor-pointer">×</button>
                        </div>
                    )}

                    {/* Input Form */}
                    <form onSubmit={sendMessage} className="relative flex items-end gap-2 bg-zinc-900 p-2 pl-4 rounded-2xl border border-zinc-800 focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-700 transition-all shadow-xl">
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            className="hidden"
                            accept=".pdf,.docx,.txt"
                        />

                        {/* Attach Button */}
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                            className={`p-2.5 mb-0.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all cursor-pointer ${uploading ? 'animate-pulse' : ''}`}
                            title="Attach Document"
                        >
                            {uploading ? <Loader2 className="animate-spin" size={20} /> : <Paperclip size={20} />}
                        </button>

                        {/* Text Input */}
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage(e);
                                }
                            }}
                            placeholder="Message..."
                            className="flex-1 bg-transparent text-white px-2 py-3.5 max-h-32 min-h-[50px] focus:outline-none placeholder:text-zinc-600 resize-none text-base"
                            disabled={loading}
                            rows={1}
                        />

                        {/* Send Button */}
                        <button
                            type="submit"
                            disabled={(!input.trim() && !file) || loading}
                            className="p-2.5 mb-0.5 bg-white text-black rounded-xl hover:bg-zinc-200 disabled:opacity-50 disabled:hover:bg-white transition-all shadow-lg active:scale-95 cursor-pointer"
                        >
                            <Send size={18} />
                        </button>
                    </form>

                    <div className="text-center text-[10px] md:text-xs text-zinc-700 mt-3 font-medium cursor-default">
                        Using {model} • AI can make mistakes.
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chat;
