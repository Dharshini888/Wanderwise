import React, { useState, useEffect } from 'react';
import { IconX, IconPencil, IconLoader2, IconAlertTriangle, IconCheck } from '@tabler/icons-react';
import { updateDocument } from '../../api/documents';

const CATEGORIES = [
  'Passport',
  'Visa',
  'Identity',
  'Flight',
  'Train',
  'Hotel',
  'Insurance',
  'Driving',
  'Other'
];

export default function EditDocumentModal({ isOpen, onClose, document: doc, onSuccess, trips = [] }) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Passport');
  const [tripId, setTripId] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [notes, setNotes] = useState('');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (doc && isOpen) {
      setName(doc.name || '');
      setCategory(doc.category || 'Passport');
      setTripId(doc.trip_id || '');
      if (doc.expiry_date) {
        setExpiryDate(doc.expiry_date.split('T')[0]);
      } else {
        setExpiryDate('');
      }
      setNotes(doc.notes || '');
      setError(null);
    }
  }, [doc, isOpen]);

  if (!isOpen || !doc) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Document name is required.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        name: name.trim(),
        category,
        trip_id: tripId ? parseInt(tripId) : 0,
        expiry_date: expiryDate || null,
        notes: notes.trim() || null
      };

      const updated = await updateDocument(doc.id, payload);
      setSaving(false);
      onSuccess && onSuccess(updated);
      onClose();
    } catch (err) {
      setSaving(false);
      const msg = err.response?.data?.detail || err.message || 'Failed to update document.';
      setError(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-glass)]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <IconPencil size={22} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--text-primary)]">Edit Document Details</h3>
              <p className="text-xs text-[var(--text-muted)]">Update category, expiry, or trip association</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)] transition-all"
            disabled={saving}
          >
            <IconX size={20} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-3">
              <IconAlertTriangle size={20} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Document Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Associated Trip
              </label>
              <select
                value={tripId}
                onChange={(e) => setTripId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              >
                <option value="">Personal / No Trip</option>
                {trips.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.destination || t.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Expiry Date
            </label>
            <input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Notes / Details
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border-color)]">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-app)] transition-all"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all"
            >
              {saving ? (
                <>
                  <IconLoader2 size={16} className="animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>Update Metadata</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
