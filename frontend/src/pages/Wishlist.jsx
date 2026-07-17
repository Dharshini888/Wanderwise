import { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';

const PRIORITIES = [
  { id: 'dream', label: 'Dream', color: '#185FA5' },
  { id: 'soon', label: 'Soon', color: '#0891b2' },
  { id: 'someday', label: 'Someday', color: '#4a6080' },
];

export default function Wishlist() {
  const [items, setItems] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [form, setForm] = useState({ destination: '', country: '', notes: '', priority: 'dream' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState('all');
  const token = localStorage.getItem('token');

  let userId = null;
  try { const p = JSON.parse(atob(token.split('.')[1])); userId = p.sub || p.user_id || p.id; } catch (_) {}

  const fetchItems = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API}/wishlist/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setItems(await res.json());

      // Fetch AI recommendations
      try {
        const recRes = await fetch(`${API}/wishlist/recommendations/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
        if (recRes.ok) setRecommendations(await recRes.json());
      } catch (e) { console.error(e); }

    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { fetchItems(); }, [userId, token]);

  const addItem = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/wishlist/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, user_id: Number(userId) }),
      });
      if (res.ok) {
        const item = await res.json();
        setItems(prev => [item, ...prev]);
        setForm({ destination: '', country: '', notes: '', priority: 'dream' });
        setShowForm(false);
      }
    } catch (_) {}
    setSubmitting(false);
  };

  const removeItem = async (id) => {
    try {
      await fetch(`${API}/wishlist/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      setItems(prev => prev.filter(i => i.id !== id));
    } catch (_) {}
  };

  const filtered = filter === 'all' ? items : items.filter(i => i.priority === filter);
  const getPriority = (id) => PRIORITIES.find(p => p.id === id) || PRIORITIES[2];

  const inputStyle = {
    width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #c8dff0',
    background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none', boxSizing: 'border-box'
  };

  const labelStyle = { display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>❤️ Travel Wishlist</h1>
          <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>{items.length} destinations in your bucket list</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          style={{ padding: '10px 20px', background: showForm ? 'rgba(220, 38, 38, 0.1)' : '#185FA5', border: showForm ? '1px solid rgba(220, 38, 38, 0.2)' : 'none', borderRadius: '10px', color: showForm ? '#dc2626' : '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '13px', boxShadow: showForm ? 'none' : '0 4px 10px rgba(24, 95, 165, 0.2)' }}>
          {showForm ? 'Cancel' : '+ Add Destination'}
        </button>
      </div>

      {showForm && (
        <form className="glass-card" onSubmit={addItem} style={{ padding: '24px', marginBottom: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
            <div>
              <label style={labelStyle}>Destination *</label>
              <input style={inputStyle} value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))} placeholder="e.g. Santorini, Northern Lights in Norway" required />
            </div>
            <div>
              <label style={labelStyle}>Country</label>
              <input style={inputStyle} value={form.country} onChange={e => setForm(f => ({ ...f, country: e.target.value }))} placeholder="e.g. Greece" />
            </div>
            <div>
              <label style={labelStyle}>Priority</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {PRIORITIES.map(p => (
                  <button key={p.id} type="button" onClick={() => setForm(f => ({ ...f, priority: p.id }))}
                    style={{ flex: 1, padding: '10px', borderRadius: '8px', border: `1px solid ${form.priority === p.id ? p.color : 'rgba(200, 225, 245, 0.9)'}`, background: form.priority === p.id ? `${p.color}15` : 'rgba(255,255,255,0.7)', color: form.priority === p.id ? p.color : '#4a6080', cursor: 'pointer', fontWeight: 600, fontSize: '12px', transition: 'all 0.2s' }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>Notes</label>
              <input style={inputStyle} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Why do you want to go?" />
            </div>
          </div>
          <button type="submit" disabled={submitting}
            style={{ marginTop: '20px', width: '100%', padding: '12px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1 }}>
            {submitting ? 'Adding...' : 'Add to Bucket List'}
          </button>
        </form>
      )}

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.5rem' }}>
        {[{ id: 'all', label: `All (${items.length})` }, ...PRIORITIES.map(p => ({ id: p.id, label: `${p.label} (${items.filter(i => i.priority === p.id).length})` }))].map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)}
            style={{ padding: '8px 16px', borderRadius: '20px', border: filter === f.id ? '1px solid rgba(24, 95, 165, 0.3)' : '1px solid transparent', cursor: 'pointer', fontWeight: 600, fontSize: '13px', background: filter === f.id ? 'rgba(24, 95, 165, 0.1)' : 'transparent', color: filter === f.id ? '#185FA5' : '#5a7a9a', transition: 'all 0.2s' }}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-secondary" style={{ textAlign: 'center', padding: '3rem' }}>Loading your wishlist...</div>
      ) : filtered.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', border: '1px dashed rgba(200, 225, 245, 0.9)' }}>
          <p style={{ fontSize: '3rem', margin: '0 0 1rem' }}>🌍</p>
          <p className="text-secondary" style={{ margin: 0 }}>{items.length === 0 ? 'Your bucket list is empty. Add your dream destinations!' : 'No destinations in this category.'}</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {filtered.map(item => {
            const priority = getPriority(item.priority);
            return (
              <div key={item.id} className="glass-card" style={{ padding: '24px', position: 'relative', borderTop: `4px solid ${priority.color}` }}>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span style={{ background: `${priority.color}15`, color: priority.color, padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' }}>
                    {priority.label}
                  </span>
                  <button onClick={() => removeItem(item.id)} style={{ background: 'none', border: 'none', color: '#5a7a9a', cursor: 'pointer', fontSize: '18px', padding: 0, lineHeight: 1 }}>✕</button>
                </div>

                <h3 className="text-primary-dark" style={{ margin: '0 0 6px', fontSize: '16px' }}>📍 {item.destination}</h3>
                {item.country && <p className="text-secondary" style={{ margin: '0 0 12px', fontSize: '13px' }}>{item.country}</p>}
                
                {item.notes && (
                  <div style={{ background: 'rgba(255,255,255,0.6)', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', color: '#4a6080', fontStyle: 'italic', marginBottom: '16px' }}>
                    "{item.notes}"
                  </div>
                )}

                <div className="text-muted" style={{ fontSize: '11px', marginTop: 'auto' }}>
                  Added {item.created_at ? new Date(item.created_at).toLocaleDateString('en', { month: 'short', year: 'numeric' }) : ''}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* AI Recommendations Section */}
      {recommendations.length > 0 && (
        <div style={{ marginTop: '3rem' }}>
          <h2 className="text-primary-dark" style={{ margin: '0 0 8px', fontSize: '1.5rem' }}>✨ AI Suggested for You</h2>
          <p className="text-secondary" style={{ margin: '0 0 16px', fontSize: '13px' }}>Based on your travel history and wishlist</p>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {recommendations.map((rec, idx) => (
              <div key={idx} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '15px' }}>{rec.destination}</h3>
                  <span style={{ fontSize: '10px', background: 'rgba(24, 95, 165, 0.1)', color: '#185FA5', padding: '2px 8px', borderRadius: '10px', fontWeight: 600 }}>{rec.vibe}</span>
                </div>
                <p style={{ fontSize: '12px', color: '#4a6080', lineHeight: 1.5, marginBottom: '16px', flex: 1 }}>{rec.reason}</p>
                <button 
                  onClick={() => {
                    setForm({ destination: rec.destination, country: '', notes: `AI Suggestion: ${rec.reason}`, priority: 'dream' });
                    setShowForm(true);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  style={{ background: 'rgba(24, 95, 165, 0.1)', color: '#185FA5', border: '1px solid rgba(24, 95, 165, 0.2)', padding: '8px', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                >
                  + Add to Wishlist
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
