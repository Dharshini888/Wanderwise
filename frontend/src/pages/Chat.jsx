import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconSend, IconMessageChatbot, IconSparkles, IconPlus,
  IconCompass, IconWallet, IconSun, IconMapPin, IconMap
} from '@tabler/icons-react';
import api from '../api/axios';
import ChatSidebar from '../components/chat/ChatSidebar';
import ChatMessage from '../components/chat/ChatMessage';
import TripWizard from '../components/trips/TripWizard';

const QUICK_PROMPTS = [
  { label: '✈️ Plan a trip', query: 'Plan a 5-day travel itinerary to Japan' },
  { label: '🚆 Find transport options', query: 'What are the best transit routes and train options?' },
  { label: '💰 Analyze budget & expenses', query: 'Analyze my trip budget and suggest savings' },
  { label: '🌦 Check weather forecast', query: 'What is the weather forecast and clothing suggestions?' },
  { label: '🧳 What should I pack?', query: 'Prepare a packing checklist for my upcoming trip' },
  { label: '📄 Check my documents', query: 'Check if any of my travel documents are expiring soon' },
  { label: '📍 Explain my itinerary', query: 'Explain the daily highlights of my itinerary' },
];

export default function Chat() {
  const navigate = useNavigate();

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const [showWizard, setShowWizard] = useState(false);
  const [wizardDest, setWizardDest] = useState('');

  const messagesEndRef = useRef(null);

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : {};

  let userId = user.id;
  try {
    if (!userId && token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub || payload.user_id || payload.id;
    }
  } catch (_) {}

  // 1. Fetch User Sessions
  const loadSessions = async () => {
    try {
      const res = await api.get('/api/chat/sessions');
      const sessionList = res.data || [];
      setSessions(sessionList);

      if (sessionList.length > 0 && !activeSessionId) {
        setActiveSessionId(sessionList[0].id);
      }
    } catch (_) {}
  };

  // 2. Fetch Messages for Active Session
  const loadMessages = async (sessionId) => {
    if (!sessionId) return;
    try {
      const res = await api.get(`/api/chat/sessions/${sessionId}/messages`);
      setMessages(res.data || []);
    } catch (_) {}
  };

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    }
  }, [activeSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Create New Session
  const handleCreateNewSession = async () => {
    try {
      const res = await api.post('/api/chat/sessions', { title: 'New Travel Conversation' });
      const newSession = res.data;
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (_) {}
  };

  // Delete Session
  const handleDeleteSession = async (sessionId) => {
    try {
      await api.delete(`/api/chat/sessions/${sessionId}`);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId);
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          setActiveSessionId(null);
          setMessages([]);
        }
      }
    } catch (_) {}
  };

  // Action Card Triggers
  const handleActionTrigger = (actionType, actionData) => {
    if (actionType === 'create_itinerary') {
      if (actionData?.destination) setWizardDest(actionData.destination);
      setShowWizard(true);
    } else if (actionType === 'update_itinerary') {
      alert(`Schedule changes applied: ${JSON.stringify(actionData.changes || actionData)}`);
    }
  };

  // Submit User Message
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    // Optimistic UI insert
    const tempUserMsg = { role: 'user', content: userText };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await api.post('/api/chat/message', {
        session_id: activeSessionId,
        message: userText
      });

      const data = res.data;
      if (data.session_id && data.session_id !== activeSessionId) {
        setActiveSessionId(data.session_id);
        loadSessions();
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply || data.response,
          actions: data.actions || []
        }
      ]);
    } catch (error) {
      let errorMessage = 'AI service temporarily unavailable. Please try again.';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error + '. Please try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: errorMessage }
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] gap-4 pb-4">
      {/* Top Header Bar matching Dashboard layout */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-card p-4 rounded-2xl shrink-0">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--color-primary-600)] dark:text-blue-400">
            <IconMessageChatbot size={16} /> AI Travel Assistant
          </div>
          <h1 className="text-xl font-bold font-heading text-[var(--text-primary)] mt-0.5">
            Personal Conversational Companion
          </h1>
        </div>

        <button
          onClick={handleCreateNewSession}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--color-primary-600)] text-white hover:bg-blue-700 font-extrabold text-xs transition-all shadow-md shrink-0"
        >
          <IconPlus size={16} /> New Chat
        </button>
      </div>

      {/* Main Chat Workspace Grid (Sidebar + Chat Area) */}
      <div className="flex-1 flex flex-col lg:flex-row gap-4 overflow-hidden min-h-0">
        {/* Chat Session Sidebar */}
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onCreateNewSession={handleCreateNewSession}
          onDeleteSession={handleDeleteSession}
        />

        {/* Chat Area Container */}
        <div className="flex-1 glass-card flex flex-col overflow-hidden rounded-2xl border border-[var(--border-color)]">
          {/* Message History Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 custom-scrollbar">
            {messages.length === 0 && (
              <div className="m-auto text-center max-w-md flex flex-col items-center gap-3 py-12">
                <div className="w-14 h-14 rounded-2xl bg-blue-500/10 text-[var(--color-primary-600)] dark:text-blue-400 border border-blue-500/20 flex items-center justify-center shadow-sm">
                  <IconSparkles size={28} />
                </div>
                <div>
                  <h3 className="text-base font-bold font-heading text-[var(--text-primary)]">
                    Hello, {user.name?.split(' ')[0] || 'Traveler'} 👋
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    Ask me anything about destination ideas, active trip execution, weather advice, or budget tracking.
                  </p>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                message={msg}
                onActionTrigger={handleActionTrigger}
              />
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] font-semibold py-2">
                <IconSparkles className="animate-spin text-blue-500" size={16} />
                <span>WanderWise AI is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="px-4 py-2 border-t border-[var(--border-color)] bg-[var(--bg-app)]/50 flex items-center gap-1.5 overflow-x-auto custom-scrollbar shrink-0">
            {QUICK_PROMPTS.map((qp, i) => (
              <button
                key={i}
                onClick={() => setInput(qp.query)}
                className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--color-primary-600)] dark:hover:text-blue-400 hover:border-blue-400 transition-all shrink-0 cursor-pointer"
              >
                {qp.label}
              </button>
            ))}
          </div>

          {/* Message Input Box */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-[var(--border-color)] flex items-center gap-2 bg-[var(--bg-card)] shrink-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask WanderWise AI anything about your trips, budget, or destinations..."
              className="flex-1 px-4 py-2.5 bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-xl text-xs font-semibold focus:outline-none focus:border-[var(--color-primary-500)]"
            />

            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-4 py-2.5 rounded-xl bg-[var(--color-primary-600)] text-white hover:bg-blue-700 font-bold text-xs disabled:opacity-40 transition-all shadow-md flex items-center gap-1 shrink-0"
            >
              <IconSend size={15} /> Send
            </button>
          </form>
        </div>
      </div>

      {/* Collapsed Future AI Features Section */}
      <details className="glass-card p-3 px-4 rounded-2xl text-xs text-[var(--text-muted)] cursor-pointer shrink-0">
        <summary className="font-bold text-[var(--text-primary)] flex items-center gap-2 list-none">
          <IconSparkles className="text-amber-400" size={16} />
          <span>Upcoming Future AI Modules</span>
        </summary>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 mt-2 border-t border-[var(--border-color)]">
          <div className="p-2 rounded-xl bg-[var(--bg-app)] text-center text-[10px] font-bold">🔮 Crowd Prediction</div>
          <div className="p-2 rounded-xl bg-[var(--bg-app)] text-center text-[10px] font-bold">✈️ Delay Predictor</div>
          <div className="p-2 rounded-xl bg-[var(--bg-app)] text-center text-[10px] font-bold">🧳 AI Packing Helper</div>
          <div className="p-2 rounded-xl bg-[var(--bg-app)] text-center text-[10px] font-bold">📖 Personal Memories</div>
          <div className="p-2 rounded-xl bg-[var(--bg-app)] text-center text-[10px] font-bold">🎙️ Voice Travel Assistant</div>
        </div>
      </details>

      {/* Trip Creation Wizard Modal Triggered by Action Cards */}
      <TripWizard
        userId={userId}
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        initialDestination={wizardDest}
        onSuccess={() => {
          setShowWizard(false);
          navigate('/trips');
        }}
      />
    </div>
  );
}