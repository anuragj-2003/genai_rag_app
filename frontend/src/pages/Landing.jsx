import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { ArrowRight, Play } from 'lucide-react';

// Typewriter Effect Component
const TypewriterLogo = () => {
  const words = ["RAGStack", "GenAI RAG", "Local Search", "7-Stage Pipeline"];
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [typingSpeed, setTypingSpeed] = useState(150);

  useEffect(() => {
    let timer;
    const handleType = () => {
      const fullWord = words[currentWordIndex];
      if (!isDeleting) {
        // Typing
        setCurrentText(fullWord.substring(0, currentText.length + 1));
        setTypingSpeed(100);

        if (currentText === fullWord) {
          // Pause at full word
          timer = setTimeout(() => setIsDeleting(true), 1500);
          return;
        }
      } else {
        // Deleting
        setCurrentText(fullWord.substring(0, currentText.length - 1));
        setTypingSpeed(50);

        if (currentText === "") {
          setIsDeleting(false);
          setCurrentWordIndex((prev) => (prev + 1) % words.length);
        }
      }
    };

    timer = setTimeout(handleType, typingSpeed);
    return () => clearTimeout(timer);
  }, [currentText, isDeleting, currentWordIndex, typingSpeed]);

  return (
    <span className="relative font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500 font-mono tracking-tight">
      {currentText}
      <span className="w-[3px] h-[1em] bg-indigo-500 inline-block ml-1 animate-pulse" />
    </span>
  );
};

export default function Landing() {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  const handleDemoClick = () => {
    navigate('/guest');
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 overflow-x-hidden font-sans relative">
      {/* Background Decorative Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[-10%] w-[60%] h-[60%] bg-purple-500/10 rounded-full blur-[150px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 w-full bg-[#09090b]/80 backdrop-blur-md border-b border-zinc-900 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
              R
            </div>
            <span className="font-bold text-lg tracking-tight text-white">RAGStack</span>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <button 
                onClick={() => navigate('/app')}
                className="px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all cursor-pointer"
              >
                Go to Workspace
              </button>
            ) : (
              <>
                <button 
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-900/50 rounded-xl transition-all cursor-pointer"
                >
                  Sign In
                </button>
                <button 
                  onClick={() => navigate('/signup')}
                  className="px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all cursor-pointer"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-28 pb-20 text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex flex-col items-center justify-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-semibold text-zinc-400 mb-6 shadow-inner">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping" />
            <span>Local ChromaDB & Hardened 7-Stage RAG Pipeline</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-none max-w-4xl mb-6">
            The Intelligent Workspace for <br />
            <TypewriterLogo />
          </h1>

          <p className="text-lg text-zinc-400 max-w-2xl mb-10 leading-relaxed font-light">
            A state-of-the-art secure platform that parses your documents cleanly, indexes them locally, and builds highly accurate answers with cross-encoder reranking.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
            {user ? (
              <button
                onClick={() => navigate('/app')}
                className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-2xl flex items-center justify-center gap-2 shadow-xl shadow-blue-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer text-base"
              >
                Go to Workspace <ArrowRight size={18} />
              </button>
            ) : (
              <>
                <button
                  onClick={() => navigate('/signup')}
                  className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-2xl flex items-center justify-center gap-2 shadow-xl shadow-blue-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer text-base"
                >
                  Sign Up Now <ArrowRight size={18} />
                </button>
                <button
                  onClick={handleDemoClick}
                  disabled={loading}
                  className="w-full sm:w-auto px-8 py-4 bg-zinc-900 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 text-zinc-300 hover:text-white font-semibold rounded-2xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer text-base"
                >
                  {loading ? "Loading..." : <><Play size={16} fill="currentColor" /> Try Demo</>}
                </button>
              </>
            )}
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-12 border-t border-zinc-900 text-center text-sm text-zinc-600 mt-20">
        <p>© 2026 RAGStack. Built locally, secure by design.</p>
      </footer>
    </div>
  );
}
