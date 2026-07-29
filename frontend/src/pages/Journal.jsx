import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  IconBook,
  IconPlus,
  IconLoader,
  IconCalendar,
  IconPencil,
  IconX,
} from '@tabler/icons-react';

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

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
            <IconBook className="text-[var(--color-primary-600)]" size={32} /> Travel Journal
          </h1>
          <p className="text-sm text-[var(--text-muted)] font-medium">Document your travel memories, reflections, and discoveries.</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className={`px-5 py-3 rounded-lg text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-all w-fit ${
            showForm 
              ? 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800' 
              : 'btn btn-primary shadow-md shadow-blue-500/10'
          }`}
        >
          {showForm ? <><IconX size={16} /> Cancel</> : <><IconPencil size={16} /> Write Entry</>}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <form className="glass-card p-6 flex flex-col gap-4 bg-[var(--bg-card)] animate-fadeIn max-w-2xl" onSubmit={addEntry}>
          <div>
            <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Title</label>
            <input 
              className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" 
              value={form.title} 
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))} 
              placeholder="e.g. Day 1: Exploring Montmartre" 
              required 
            />
          </div>
          <div>
            <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Content</label>
            <textarea 
              className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] min-h-[150px] resize-y" 
              value={form.content} 
              onChange={e => setForm(f => ({ ...f, content: e.target.value }))} 
              placeholder="What happened today?" 
              required 
            />
          </div>
          <button 
            type="submit" 
            disabled={submitting}
            className="btn btn-primary w-full py-3.5 text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
          >
            {submitting ? <><IconLoader className="animate-spin" size={16} /> Saving...</> : <><IconPlus size={16} /> Save Entry</>}
          </button>
        </form>
      )}

      {/* Entries */}
      {loading ? (
        <div className="flex justify-center items-center py-16 text-[var(--text-muted)]">
          <IconLoader className="animate-spin text-[var(--color-primary-500)] mr-2" size={20} />
          <span className="text-sm font-semibold">Loading journal...</span>
        </div>
      ) : entries.length === 0 ? (
        <div className="glass-card p-16 text-center flex flex-col items-center justify-center gap-3 border border-dashed border-[var(--border-color)]">
          <span className="text-4xl">✍️</span>
          <div className="text-base font-bold text-[var(--text-primary)]">No entries yet</div>
          <p className="text-xs text-[var(--text-muted)] max-w-xs leading-relaxed">Start writing your travel memories by clicking the "Write Entry" button above.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-5 max-w-2xl">
          {entries.map(entry => (
            <div key={entry.id} className="glass-card p-6 bg-[var(--bg-card)] border border-[var(--border-color)]">
              <div className="flex justify-between items-center mb-4 border-b border-[var(--border-color)] pb-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] font-heading">{entry.title}</h3>
                <span className="text-[10px] font-bold bg-blue-50 dark:bg-blue-950/20 text-[var(--color-primary-600)] dark:text-blue-400 px-2.5 py-1 rounded-full flex items-center gap-1">
                  <IconCalendar size={10} />
                  {new Date(entry.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">{entry.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
