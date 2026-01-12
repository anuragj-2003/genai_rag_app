import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Chat from './pages/Chat';
import Settings from './pages/Settings';
import { useAuth } from './context/AuthContext';
import { SettingsProvider } from './context/SettingsContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;
  return children;
};

function App() {
  const [currentChatId, setCurrentChatId] = useState(null);

  const handleNewChat = () => {
    setCurrentChatId(null);
  };

  const handleSelectChat = (id) => {
    setCurrentChatId(id);
  };

  return (
    <SettingsProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
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
      </Routes>
    </SettingsProvider>
  );
}

export default App;
