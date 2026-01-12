import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout = ({ onNewChat, onSelectChat, currentChatId }) => {
    return (
        <div className="flex h-screen bg-black text-white overflow-hidden font-sans selection:bg-blue-500/30">
            <Sidebar onNewChat={onNewChat} onSelectChat={onSelectChat} currentChatId={currentChatId} />
            <div className="flex-1 flex flex-col h-full bg-black relative">
                {/* Subtle Background Gradients */}
                <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden z-0">
                    <div className="absolute top-[-20%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-900/10 blur-[120px]" />
                    <div className="absolute bottom-[-20%] left-[-10%] w-[40%] h-[40%] rounded-full bg-violet-900/10 blur-[120px]" />
                </div>

                {/* Main Content Area */}
                <div className="flex-1 z-10 relative flex flex-col h-full overflow-hidden">
                    <Outlet />
                </div>
            </div>
        </div>
    );
};

export default Layout;
