import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const API = 'http://localhost:8000/api';

export default function Journal() {
  const { tripId } = useParams();
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState({ title: '', content: '' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const token = localStorage.getItem('token');

  const fetchEntries = async () => {
    if (!tripId) return;
    try {
      const res = await fetch(`${API}/journal/${tripId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setEntries(await res.json());
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { fetchEntries(); }, [tripId, token]);

  const addEntry = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/journal/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, trip_id: parseInt(tripId) }),
      });
      if (res.ok) {
        const item = await res.json();
        setEntries(prev => [item, ...prev]);
        setForm({ title: '', content: '' });
        setShowForm(false);
      }
    } catch (_) {}
    setSubmitting(false);
  };

  const inputStyle = { width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none', boxSizing: 'border-box' };
  const labelStyle = { display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div>
          <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>📖 Travel Journal</h1>
          <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Document your memories and experiences.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          style={{ padding: '10px 20px', background: showForm ? 'rgba(220, 38, 38, 0.1)' : '#185FA5', border: showForm ? '1px solid rgba(220, 38, 38, 0.2)' : 'none', borderRadius: '10px', color: showForm ? '#dc2626' : '#fff', fontWeight: 600, cursor: 'pointer', fontSize: '13px', boxShadow: showForm ? 'none' : '0 4px 10px rgba(24, 95, 165, 0.2)' }}>
          {showForm ? 'Cancel' : '+ Write Entry'}
        </button>
      </div>

      {showForm && (
        <form className="glass-card" onSubmit={addEntry} style={{ padding: '24px', marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={labelStyle}>Title</label>
            <input style={inputStyle} value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Day 1: Exploring Montmartre" required />
          </div>
          <div>
            <label style={labelStyle}>Content</label>
            <textarea style={{ ...inputStyle, minHeight: '150px', resize: 'vertical' }} value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} placeholder="What happened today?" required />
          </div>
          <button type="submit" disabled={submitting}
            style={{ width: '100%', padding: '12px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1 }}>
            {submitting ? 'Saving...' : 'Save Entry'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="text-secondary" style={{ textAlign: 'center', padding: '3rem' }}>Loading entries...</div>
      ) : entries.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', border: '1px dashed rgba(200, 225, 245, 0.9)' }}>
          <p style={{ fontSize: '3rem', margin: '0 0 1rem' }}>✍️</p>
          <p className="text-secondary" style={{ margin: 0 }}>No entries yet. Start writing your travel story!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {entries.map(entry => (
            <div key={entry.id} className="glass-card" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(200, 225, 245, 0.5)', paddingBottom: '12px' }}>
                <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '18px' }}>{entry.title}</h3>
                <span className="label-text" style={{ fontSize: '11px', background: 'rgba(24, 95, 165, 0.1)', color: '#185FA5', padding: '4px 10px', borderRadius: '12px' }}>
                  {new Date(entry.created_at).toLocaleDateString()}
                </span>
              </div>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#4a6080', fontSize: '14px', lineHeight: 1.6 }}>
                {entry.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
