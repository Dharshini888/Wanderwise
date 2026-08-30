import React, { useState, useEffect } from 'react';
import {
  IconX, IconUpload, IconFileText, IconPhoto, IconAlertTriangle,
  IconCheck, IconLoader2, IconCalendar, IconMapPin, IconTag, IconNotes
} from '@tabler/icons-react';
import { uploadDocument } from '../../api/documents';

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

const ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const ALLOWED_EXTS = ['.pdf', '.jpg', '.jpeg', '.png', '.webp'];
const MAX_SIZE = 15 * 1024 * 1024; // 15MB

export default function UploadDocumentModal({ isOpen, onClose, onSuccess, trips = [], initialTripId = null }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Passport');
  const [tripId, setTripId] = useState(initialTripId || '');
  const [expiryDate, setExpiryDate] = useState('');
  const [notes, setNotes] = useState('');
  
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialTripId) {
      setTripId(initialTripId);
    }
  }, [initialTripId]);

  if (!isOpen) return null;

  const handleFileChange = (selectedFile) => {
    setError(null);
    if (!selectedFile) return;

    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Invalid file type '${ext}'. Please upload a PDF, JPG, PNG, or WEBP file.`);
      return;
    }

    if (selectedFile.size > MAX_SIZE) {
      setError(`File size (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 15 MB limit.`);
      return;
    }

    setFile(selectedFile);
    if (!name.trim()) {
      const cleanName = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      setName(cleanName);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a document file to upload.');
      return;
    }
    if (!name.trim()) {
      setError('Please enter a document name.');
      return;
    }

    setError(null);
    setUploading(true);
    setProgress(10);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name.trim());
      formData.append('category', category);
      if (tripId) formData.append('trip_id', tripId);
      if (expiryDate) formData.append('expiry_date', expiryDate);
      if (notes.trim()) formData.append('notes', notes.trim());

      const created = await uploadDocument(formData, (percent) => {
        setProgress(percent);
      });

      setUploading(false);
      onSuccess && onSuccess(created);
      onClose();
      // Reset form
      setFile(null);
      setName('');
      setCategory('Passport');
      setExpiryDate('');
      setNotes('');
      setProgress(0);
    } catch (err) {
      setUploading(false);
      const msg = err.response?.data?.detail || err.message || 'Failed to upload document.';
      setError(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] w-full max-w-xl rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-glass)]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <IconUpload size={22} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--text-primary)]">Upload Travel Document</h3>
              <p className="text-xs text-[var(--text-muted)]">Encrypted & securely stored in your personal vault</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)] transition-all"
            disabled={uploading}
          >
            <IconX size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5 custom-scrollbar flex-1">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-3">
              <IconAlertTriangle size={20} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* File Upload Zone */}
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Select Document File *
            </label>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer relative ${
                dragActive
                  ? 'border-blue-500 bg-blue-500/10 scale-[1.01]'
                  : file
                  ? 'border-emerald-500/40 bg-emerald-500/5'
                  : 'border-[var(--border-color)] hover:border-blue-500/50 bg-[var(--bg-app)]'
              }`}
            >
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploading}
              />
              {file ? (
                <div className="flex items-center justify-between bg-[var(--bg-card)] p-3.5 rounded-xl border border-emerald-500/30">
                  <div className="flex items-center gap-3 truncate">
                    {file.name.endsWith('.pdf') ? (
                      <IconFileText size={28} className="text-rose-500 shrink-0" />
                    ) : (
                      <IconPhoto size={28} className="text-blue-500 shrink-0" />
                    )}
                    <div className="text-left truncate">
                      <div className="text-sm font-bold text-[var(--text-primary)] truncate">{file.name}</div>
                      <div className="text-xs text-[var(--text-muted)]">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB · {file.type || 'Document'}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-500/10 transition-all"
                  >
                    <IconX size={18} />
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 mx-auto rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                    <IconUpload size={24} />
                  </div>
                  <div className="text-sm font-semibold text-[var(--text-primary)]">
                    Drag & drop file here, or <span className="text-blue-600 dark:text-blue-400 underline">browse</span>
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    Supports PDF, JPG, PNG, WEBP (Max 15 MB)
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Document Name */}
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Document Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Passport - Dharshini, Flight Ticket to Tokyo"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>

          {/* Grid: Category & Associated Trip */}
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
                Link to Trip (Optional)
              </label>
              <select
                value={tripId}
                onChange={(e) => setTripId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              >
                <option value="">Personal / No Trip</option>
                {trips.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.destination || t.title} {t.start_date ? `(${t.start_date.split('T')[0]})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Expiry Date */}
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Expiry Date (Optional)
            </label>
            <input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            <p className="text-[11px] text-[var(--text-muted)] mt-1">
              WanderWise will automatically track status & alert you 30 days before expiration.
            </p>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Notes / Description (Optional)
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Seat 14B, Booking Ref #XYZ123, Emergency contact details..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none"
            />
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-[var(--text-muted)]">
                <span>Uploading to Vault...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full h-2 bg-[var(--bg-app)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Modal Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border-color)]">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-app)] transition-all"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {uploading ? (
                <>
                  <IconLoader2 size={16} className="animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <IconUpload size={16} />
                  <span>Save to Vault</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
