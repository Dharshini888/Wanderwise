import { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';
const STORAGE_KEY = 'ww_packing_checks';

export default function Packing() {
  const [form, setForm] = useState({ destination: '', duration: '3', travel_type: 'leisure', weather: '' });
  const [checklist, setChecklist] = useState(null);
  const [checked, setChecked] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setChecked(JSON.parse(saved));
  }, []);

  const saveChecks = (newChecked) => {
    setChecked(newChecked);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newChecked));
  };

  const toggleItem = (cat, item) => {
    const key = `${cat}:${item}`;
    saveChecks({ ...checked, [key]: !checked[key] });
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setChecklist(null);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API}/packing/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, duration: parseInt(form.duration) }),
      });
      const data = await res.json();
      if (res.ok) setChecklist(data.checklist);
      else setError(data.detail || 'Failed to generate packing list');
    } catch (_) { setError('Network error'); }
    setLoading(false);
  };

  const CATEGORY_ICONS = {
    'Clothing': '👕', 'Documents': '📄', 'Electronics': '💻',
    'Health & Hygiene': '💊', 'Accessories': '🎒', 'Destination Specific': '📍',
    'Raw': '📝',
  };
  const CATEGORY_COLORS = {
    'Clothing': '#185FA5', 'Documents': '#0891b2', 'Electronics': '#d97706',
    'Health & Hygiene': '#16a34a', 'Accessories': '#8b5cf6', 'Destination Specific': '#dc2626',
  };

  const totalItems = checklist ? Object.values(checklist).flat().length : 0;
  const checkedCount = Object.values(checked).filter(Boolean).length;

  const inputStyle = {
    width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #c8dff0',
    background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none', boxSizing: 'border-box'
  };

  const labelStyle = { display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>🎒 AI Packing Assistant</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>AI-generated packing checklist tailored to your trip.</p>
      </div>

      <form className="glass-card" onSubmit={handleGenerate} style={{ padding: '24px', marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div style={{ gridColumn: 'span 2' }}>
            <label style={labelStyle}>Destination</label>
            <input style={inputStyle} value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))} placeholder="e.g. Ooty, India" required />
          </div>
          <div>
            <label style={labelStyle}>Duration (days)</label>
            <input style={inputStyle} type="number" min="1" max="60" value={form.duration} onChange={e => setForm(f => ({ ...f, duration: e.target.value }))} />
          </div>
          <div>
            <label style={labelStyle}>Travel Type</label>
            <select style={inputStyle} value={form.travel_type} onChange={e => setForm(f => ({ ...f, travel_type: e.target.value }))}>
              {['leisure', 'adventure', 'business', 'beach', 'trekking', 'family'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
          </div>
          <div style={{ gridColumn: 'span 2' }}>
            <label style={labelStyle}>Expected Weather <span style={{ fontWeight: 400, textTransform: 'none' }}>(optional)</span></label>
            <input style={inputStyle} value={form.weather} onChange={e => setForm(f => ({ ...f, weather: e.target.value }))} placeholder="e.g. cold and rainy, tropical, hot and humid" />
          </div>
        </div>
        <button type="submit" disabled={loading}
          style={{ marginTop: '20px', width: '100%', padding: '12px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
          {loading ? 'AI is packing for you...' : 'Generate Smart Packing List'}
        </button>
      </form>

      {error && <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', color: '#dc2626', marginBottom: '2rem', fontSize: '14px', fontWeight: 500 }}>⚠️ {error}</div>}

      {checklist && (
        <>
          <div className="glass-card" style={{ padding: '20px', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span className="text-primary-dark" style={{ fontWeight: 700, fontSize: '14px' }}>Packing Progress</span>
              <span className="text-muted" style={{ fontSize: '13px', fontWeight: 600 }}>{checkedCount}/{totalItems} items packed</span>
            </div>
            <div style={{ background: 'rgba(24, 95, 165, 0.1)', borderRadius: '8px', height: '10px' }}>
              <div style={{ background: '#16a34a', height: '100%', borderRadius: '8px', width: `${totalItems > 0 ? (checkedCount / totalItems) * 100 : 0}%`, transition: 'width 0.4s' }} />
            </div>
          </div>

          <div style={{ display: 'grid', gap: '1.5rem' }}>
            {Object.entries(checklist).map(([category, items]) => {
              const catIcon = CATEGORY_ICONS[category] || '📦';
              const catColor = CATEGORY_COLORS[category] || '#185FA5';
              const catChecked = (Array.isArray(items) ? items : []).filter(item => checked[`${category}:${item}`]).length;
              const catTotal = Array.isArray(items) ? items.length : 0;

              return (
                <div key={category} className="glass-card" style={{ overflow: 'hidden' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid rgba(200, 225, 245, 0.6)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '1.4rem' }}>{catIcon}</span>
                      <span className="text-primary-dark" style={{ fontWeight: 700, fontSize: '15px' }}>{category}</span>
                    </div>
                    <span style={{ fontSize: '12px', color: catChecked === catTotal && catTotal > 0 ? '#16a34a' : '#5a7a9a', fontWeight: 700 }}>
                      {catChecked}/{catTotal}
                    </span>
                  </div>
                  <div style={{ padding: '16px 20px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {(Array.isArray(items) ? items : [items]).map((item, i) => {
                      const isChecked = checked[`${category}:${item}`];
                      return (
                        <button key={i} onClick={() => toggleItem(category, item)}
                          style={{ 
                            display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', 
                            borderRadius: '20px', border: `1px solid ${isChecked ? catColor : 'rgba(200, 225, 245, 0.9)'}`, 
                            background: isChecked ? `${catColor}15` : 'rgba(255,255,255,0.7)', 
                            color: isChecked ? catColor : '#4a6080', cursor: 'pointer', fontSize: '13px', 
                            fontWeight: 500, transition: 'all 0.2s', textDecoration: isChecked ? 'line-through' : 'none' 
                          }}>
                          <span style={{ fontSize: '14px', lineHeight: 1 }}>{isChecked ? '✓' : '○'}</span>
                          {item}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
