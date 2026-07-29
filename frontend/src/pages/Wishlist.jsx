import { useState, useEffect } from 'react';
import {
  IconHeart,
  IconPlus,
  IconLoader,
  IconTrash,
  IconX,
  IconSparkles,
  IconMapPin,
  IconCalendar,
} from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

const PRIORITIES = [
  { id: 'dream', label: 'Dream', color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900', border: 'border-t-blue-500' },
  { id: 'soon', label: 'Soon', color: 'text-teal-600 bg-teal-50 dark:bg-teal-950/20 border-teal-200 dark:border-teal-900', border: 'border-t-teal-500' },
  { id: 'someday', label: 'Someday', color: 'text-slate-600 bg-slate-50 dark:bg-slate-950/20 border-slate-200 dark:border-slate-900', border: 'border-t-slate-400' },
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
      try {
        const recRes = await fetch(`${API}/wishlist/recommendations/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
        if (recRes.ok) setRecommendations(await recRes.json());
      } catch (e) {}
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

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
            <IconHeart className="text-red-500" size={32} /> Travel Wishlist
          </h1>
          <p className="text-sm text-[var(--text-muted)] font-medium">{items.length} dream destinations in your bucket list</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className={`px-5 py-3 rounded-lg text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-all w-fit ${
            showForm 
              ? 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800' 
              : 'btn btn-primary shadow-md shadow-blue-500/10'
          }`}
        >
          {showForm ? <><IconX size={16} /> Cancel</> : <><IconPlus size={16} /> Add Destination</>}
        </button>
      </div>

      {/* Add Form */}
      {showForm && (
        <form className="glass-card p-6 bg-[var(--bg-card)] animate-fadeIn" onSubmit={addItem}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-1">
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Destination *</label>
              <input className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))} placeholder="e.g. Santorini, Northern Lights" required />
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Country</label>
              <input className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none" value={form.country} onChange={e => setForm(f => ({ ...f, country: e.target.value }))} placeholder="e.g. Greece" />
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Priority</label>
              <div className="flex gap-2">
                {PRIORITIES.map(p => (
                  <button key={p.id} type="button" onClick={() => setForm(f => ({ ...f, priority: p.id }))}
                    className={`flex-1 py-2.5 rounded-lg border text-xs font-bold transition-all cursor-pointer ${
                      form.priority === p.id ? `${p.color} border` : 'border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-app)]'
                    }`}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Notes</label>
              <input className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Why do you want to go?" />
            </div>
          </div>
          <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3.5 mt-5 text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50">
            {submitting ? <><IconLoader className="animate-spin" size={16} /> Adding...</> : 'Add to Bucket List'}
          </button>
        </form>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 flex-wrap">
        {[
          { id: 'all', label: `All (${items.length})` }, 
          ...PRIORITIES.map(p => ({ id: p.id, label: `${p.label} (${items.filter(i => i.priority === p.id).length})` }))
        ].map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer ${
              filter === f.id 
                ? 'bg-blue-50 dark:bg-blue-950/20 text-[var(--color-primary-600)] dark:text-blue-400 border border-blue-200 dark:border-blue-900' 
                : 'text-[var(--text-muted)] hover:bg-[var(--bg-app)] border border-transparent'
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Wishlist Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-16 text-[var(--text-muted)]">
          <IconLoader className="animate-spin text-[var(--color-primary-500)] mr-2" size={20} />
          <span className="text-sm font-semibold">Loading wishlist...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-16 text-center flex flex-col items-center justify-center gap-3 border border-dashed border-[var(--border-color)]">
          <span className="text-4xl">🌍</span>
          <div className="text-base font-bold text-[var(--text-primary)]">{items.length === 0 ? 'Your bucket list is empty' : 'No destinations in this category'}</div>
          <p className="text-xs text-[var(--text-muted)] max-w-xs leading-relaxed">Add your dream destinations to start planning.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map(item => {
            const priority = getPriority(item.priority);
            return (
              <div key={item.id} className={`glass-card p-6 bg-[var(--bg-card)] border-t-4 ${priority.border} flex flex-col gap-3 group relative`}>
                <div className="flex justify-between items-start">
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${priority.color}`}>
                    {priority.label}
                  </span>
                  <button onClick={() => removeItem(item.id)} className="p-1 rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 opacity-0 group-hover:opacity-100 transition-all">
                    <IconTrash size={14} />
                  </button>
                </div>
                <div>
                  <h3 className="text-base font-bold text-[var(--text-primary)] font-heading flex items-center gap-1.5">
                    <IconMapPin size={16} className="text-[var(--color-primary-500)]" /> {item.destination}
                  </h3>
                  {item.country && <p className="text-xs text-[var(--text-muted)] mt-0.5 font-medium">{item.country}</p>}
                </div>
                {item.notes && (
                  <div className="bg-[var(--bg-app)] border border-[var(--border-color)] p-3 rounded-lg text-xs text-[var(--text-secondary)] italic leading-relaxed">
                    "{item.notes}"
                  </div>
                )}
                <div className="text-[10px] text-[var(--text-muted)] font-semibold flex items-center gap-1 mt-auto pt-2">
                  <IconCalendar size={10} />
                  Added {item.created_at ? new Date(item.created_at).toLocaleDateString('en', { month: 'short', year: 'numeric' }) : ''}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <div className="mt-6 flex flex-col gap-4">
          <div>
            <h2 className="text-xl font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconSparkles className="text-amber-500 animate-pulse" size={22} /> AI Suggested For You
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">Based on your travel history and current wishlist</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="glass-card p-5 bg-[var(--bg-card)] flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading">{rec.destination}</h3>
                  <span className="text-[9px] font-bold bg-blue-50 dark:bg-blue-950/20 text-[var(--color-primary-600)] dark:text-blue-400 px-2 py-0.5 rounded-full uppercase tracking-wider">{rec.vibe}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">{rec.reason}</p>
                <button 
                  onClick={() => {
                    setForm({ destination: rec.destination, country: '', notes: `AI: ${rec.reason}`, priority: 'dream' });
                    setShowForm(true);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="text-xs font-bold text-[var(--color-primary-600)] dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-900 py-2 rounded-lg hover:bg-[var(--color-primary-600)] hover:text-white dark:hover:bg-blue-600 dark:hover:text-white transition-all cursor-pointer flex items-center justify-center gap-1"
                >
                  <IconPlus size={14} /> Add to Wishlist
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
