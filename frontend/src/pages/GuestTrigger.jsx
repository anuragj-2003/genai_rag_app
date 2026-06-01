import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2, Sparkles, AlertCircle } from 'lucide-react';

export default function GuestTrigger() {
  const navigate = useNavigate();
  const { user, startGuestSession } = useAuth();
  const initialized = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If user already has a valid session (guest or auth), go straight to app
    if (user) {
      navigate('/app', { replace: true });
      return;
    }

    if (initialized.current) return;
    initialized.current = true;

    const setupSession = async () => {
      try {
        await startGuestSession();
        navigate('/app', { replace: true });
      } catch (err) {
        console.error('Guest session failed:', err);
        setError('Could not start a demo session. The backend may be unreachable.');
      }
    };

    setupSession();
  }, [user, startGuestSession, navigate]);

  if (error) {
    return (
      <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center text-zinc-300">
        <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-zinc-900/50 border border-red-900/40 backdrop-blur-md max-w-sm text-center shadow-xl">
          <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center border border-red-500/25">
            <AlertCircle className="text-red-400" size={20} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Demo Unavailable</h2>
            <p className="text-xs text-zinc-500 mt-1">{error}</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="mt-2 px-5 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-xl text-sm text-zinc-300 hover:text-white transition-all cursor-pointer"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center text-zinc-300">
      <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800 backdrop-blur-md max-w-sm text-center shadow-xl">
        <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center border border-blue-500/25">
          <Sparkles className="text-blue-400 animate-pulse" size={20} />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Initializing Demo Session</h2>
          <p className="text-xs text-zinc-500 mt-1">Please wait while we prepare your temporary RAGStack sandbox...</p>
        </div>
        <Loader2 className="animate-spin text-blue-500 mt-2" size={24} />
      </div>
    </div>
  );
}
