import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Chat from './pages/Chat';
import Settings from './pages/Settings';
import Landing from './pages/Landing';
import GuestTrigger from './pages/GuestTrigger';
import { useAuth } from './context/AuthContext';
import { SettingsProvider } from './context/SettingsContext';

const ProtectedRoute = ({ children }) => {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white">Loading...</div>;
  if (!isAuthenticated && (!user || !user.is_guest)) {
    return <Navigate to="/login" />;
  }
  if (user && user.is_guest && user.limit_exceeded) {
    return <Navigate to="/login" state={{ limitExceeded: true }} />;
  }
  return children;
};

function App() {
  const [currentChatId, setCurrentChatId] = useState(null);
  const { user, isAuthenticated, loading } = useAuth();

  const handleNewChat = () => {
    setCurrentChatId(null);
  };

  const handleSelectChat = (id) => {
    setCurrentChatId(id);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-slate-900 text-white">Loading...</div>;
  }

  const hasAccess = isAuthenticated || (user && user.is_guest && !user.limit_exceeded);

  return (
    <SettingsProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Login />} />
        <Route path="/guest" element={<GuestTrigger />} />

        {/* Landing Page */}
        <Route
          path="/"
          element={<Landing />}
        />

        {/* App Workspace */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <Layout
                onNewChat={handleNewChat}
                onSelectChat={handleSelectChat}
                currentChatId={currentChatId}
              />
            </ProtectedRoute>
          }
        >
          <Route index element={<Chat currentChatId={currentChatId} />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </SettingsProvider>
  );
}

export default App;
