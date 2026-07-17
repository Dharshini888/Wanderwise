import { useState, useRef, useEffect } from 'react'; // Trigger Vite HMR
import ReactMarkdown from 'react-markdown';
import api from '../api/axios';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/api/chat/message', { message: userMsg.content });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 3rem)' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>
          AI Travel Assistant
        </h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>
          Ask me anything about your travel plans, destinations, or itineraries.
        </p>
      </div>

      {/* Chat Area */}
      <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Messages List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#5a7a9a', margin: 'auto', maxWidth: '400px' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
              <h3 className="text-primary-dark" style={{ margin: '0 0 8px', fontSize: '1.1rem' }}>Start a Conversation</h3>
              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5 }}>
                Ask for destination ideas, packing lists, or local customs for your next trip.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: '75%',
                padding: '12px 16px',
                borderRadius: msg.role === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                background: msg.role === 'user' ? '#185FA5' : 'rgba(24, 95, 165, 0.1)',
                color: msg.role === 'user' ? 'white' : '#1a2a3a',
                fontSize: '14px',
                lineHeight: 1.5,
                boxShadow: msg.role === 'user' ? '0 4px 10px rgba(24, 95, 165, 0.2)' : 'none',
              }}>
                <ReactMarkdown
                  components={{
                    p: ({node, ...props}) => <p style={{margin: '0 0 0.5em 0', lastChild: {marginBottom: 0}}} {...props} />,
                    a: ({node, ...props}) => <a style={{color: msg.role === 'user' ? '#eef6fd' : '#185FA5'}} {...props} />,
                    ul: ({node, ...props}) => <ul style={{margin: '0 0 0.5em 0', paddingLeft: '1.5em'}} {...props} />,
                    ol: ({node, ...props}) => <ol style={{margin: '0 0 0.5em 0', paddingLeft: '1.5em'}} {...props} />,
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '12px 16px',
                borderRadius: '16px 16px 16px 0',
                background: 'rgba(24, 95, 165, 0.1)',
                color: '#4a6080',
                fontSize: '14px',
                display: 'flex',
                gap: '4px'
              }}>
                <span className="typing-dot">.</span><span className="typing-dot">.</span><span className="typing-dot">.</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{ padding: '16px', borderTop: '1px solid rgba(200, 225, 245, 0.9)' }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message WanderWise AI..."
              style={{
                flex: 1,
                padding: '14px 18px',
                borderRadius: '24px',
                border: '1px solid #c8dff0',
                background: 'rgba(255,255,255,0.9)',
                color: '#1a2a3a',
                fontSize: '14px',
                outline: 'none',
                transition: 'all 0.2s ease'
              }}
              onFocus={e => {
                e.target.style.border = '1px solid #185FA5';
                e.target.style.boxShadow = '0 0 0 3px rgba(24, 95, 165, 0.15)';
              }}
              onBlur={e => {
                e.target.style.border = '1px solid #c8dff0';
                e.target.style.boxShadow = 'none';
              }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              style={{
                background: '#185FA5',
                color: 'white',
                border: 'none',
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !input.trim() ? 0.6 : 1,
                transition: 'all 0.2s ease',
                boxShadow: '0 4px 10px rgba(24, 95, 165, 0.2)'
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}