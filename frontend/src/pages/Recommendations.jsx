import { useState } from 'react';

const API = 'http://localhost:8000/api';

export default function Recommendations() {
  const [destination, setDestination] = useState('');
  const [interests, setInterests] = useState('');
  const [recs, setRecs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const token = localStorage.getItem('token');

  const fetchRecs = async (e) => {
    e.preventDefault();
    if (!destination.trim()) return;
    setLoading(true); setError(''); setRecs(null);
    try {
      const res = await fetch(`${API}/recommendations/places`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ destination, interests: interests || 'general sightseeing' })
      });
      const data = await res.json();
      if (res.ok) setRecs(data);
      else setError(data.detail || 'Could not fetch recommendations');
    } catch (_) { setError('Network error'); }
    setLoading(false);
  };

  const inputStyle = { flex: 1, padding: '12px 14px', borderRadius: '10px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none' };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>✨ AI Discover</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Discover hidden gems and top attractions based on your interests.</p>
      </div>

      <form onSubmit={fetchRecs} style={{ display: 'flex', gap: '12px', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <input style={inputStyle} value={destination} onChange={e => setDestination(e.target.value)} placeholder="Destination (e.g. Kyoto)" required />
        <input style={inputStyle} value={interests} onChange={e => setInterests(e.target.value)} placeholder="Interests (e.g. food, history, nature)" />
        <button type="submit" disabled={loading || !destination.trim()}
          style={{ padding: '12px 24px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, boxShadow: '0 4px 10px rgba(24, 95, 165, 0.2)' }}>
          {loading ? 'Finding Gems...' : 'Discover'}
        </button>
      </form>

      {error && <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', color: '#dc2626', marginBottom: '1.5rem', fontSize: '14px', fontWeight: 500 }}>⚠️ {error}</div>}

      {recs && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {recs.recommendations?.map((r, i) => (
            <div key={i} className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '16px' }}>{r.name}</h3>
                <span style={{ fontSize: '14px', background: 'rgba(255,255,255,0.8)', padding: '2px 8px', borderRadius: '12px', border: '1px solid #c8dff0' }}>{r.rating} ⭐</span>
              </div>
              <p style={{ color: '#4a6080', fontSize: '13px', lineHeight: 1.5, margin: '0 0 16px', flex: 1 }}>{r.description}</p>
              
              {r.tags && (
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
                  {r.tags.map(t => <span key={t} style={{ fontSize: '11px', background: 'rgba(24, 95, 165, 0.1)', color: '#185FA5', padding: '4px 8px', borderRadius: '10px', fontWeight: 600 }}>{t}</span>)}
                </div>
              )}
              
              <div style={{ background: 'rgba(255,255,255,0.6)', padding: '8px 12px', borderRadius: '8px', fontSize: '12px', color: '#5a7a9a' }}>
                📍 {r.address}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
