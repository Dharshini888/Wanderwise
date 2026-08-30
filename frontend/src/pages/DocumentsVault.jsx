import React, { useState, useEffect } from 'react';
import {
  IconFileText, IconPlus, IconSearch, IconFilter, IconSortAscending,
  IconAlertTriangle, IconCheck, IconDownload, IconPencil, IconTrash,
  IconShieldCheck, IconLock, IconPhoto, IconMapPin, IconCalendar,
  IconTag, IconNotes, IconRefresh, IconClock, IconEye, IconFolder
} from '@tabler/icons-react';
import { getDocuments, deleteDocument, downloadDocumentFile } from '../api/documents';
import { getUserTrips } from '../api/trips';
import UploadDocumentModal from '../components/documents/UploadDocumentModal';
import DocumentPreviewModal from '../components/documents/DocumentPreviewModal';
import EditDocumentModal from '../components/documents/EditDocumentModal';

import { getStoredUserId } from '../utils/formatters';

const CATEGORIES = [
  'All',
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

export default function DocumentsVault() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, expiring_soon: 0, expired: 0, trip_linked: 0 });
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters & Controls
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedTripId, setSelectedTripId] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('recently_added');

  // Modals state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [editDoc, setEditDoc] = useState(null);
  const [deleteDocTarget, setDeleteDocTarget] = useState(null);

  const fetchTripsList = async () => {
    try {
      const userId = getStoredUserId();
      if (!userId) return;
      const data = await getUserTrips(userId);
      if (Array.isArray(data)) setTrips(data);
    } catch (_) {}
  };

  const fetchVaultData = async () => {
    setLoading(true);
    try {
      const params = {
        category: selectedCategory,
        status: selectedStatus,
        tripId: selectedTripId,
        search: searchQuery,
        sortBy: sortBy,
      };
      const res = await getDocuments(params);
      setDocuments(res.documents || []);
      if (res.stats) setStats(res.stats);
    } catch (err) {
      console.error('Failed to load documents vault:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTripsList();
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchVaultData();
    }, 250);
    return () => clearTimeout(delayDebounceFn);
  }, [selectedCategory, selectedStatus, selectedTripId, searchQuery, sortBy]);

  // Polling for OCR PROCESSING
  useEffect(() => {
    const hasProcessingDocs = documents.some(d => d.ocr_status === 'PROCESSING');
    if (!hasProcessingDocs) return;

    const interval = setInterval(() => {
      fetchVaultData();
    }, 2000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleDeleteConfirm = async () => {
    if (!deleteDocTarget) return;
    try {
      await deleteDocument(deleteDocTarget.id);
      setDeleteDocTarget(null);
      if (previewDoc?.id === deleteDocTarget.id) setPreviewDoc(null);
      fetchVaultData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete document.');
    }
  };

  const handleDownload = async (e, doc) => {
    e.stopPropagation();
    try {
      await downloadDocumentFile(doc.id, doc.file_name, 'attachment');
    } catch (_) {
      alert('Failed to download document file.');
    }
  };

  const expiringOrExpiredDocs = documents.filter(
    (d) => d.status === 'EXPIRING_SOON' || d.status === 'EXPIRED'
  );

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* ── 1. HEADER SECTION ──────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 md:p-8 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xl relative overflow-hidden">
        <div className="space-y-2 relative z-10">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center gap-1.5">
              <IconLock size={14} /> Smart Encrypted Storage
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight text-[var(--text-primary)] font-heading">
            Smart Travel Documents Vault
          </h1>
          <p className="text-sm text-[var(--text-muted)] max-w-xl">
            Keep your important travel documents, tickets, visas, and passports organized and securely accessible in one place.
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <IconPlus size={20} />
            <span>Upload Document</span>
          </button>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* ── 2. METRICS DASHBOARD CARDS ────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="glass-card p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex justify-between items-center text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">
            <span>Total Documents</span>
            <IconFolder size={18} className="text-blue-500" />
          </div>
          <div className="text-2xl font-black text-[var(--text-primary)]">{stats.total}</div>
          <div className="text-[11px] text-[var(--text-muted)] font-medium">Saved in secure vault</div>
        </div>

        {/* Active Trip Linked */}
        <div className="glass-card p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1">
          <div className="flex justify-between items-center text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider">
            <span>Linked to Trips</span>
            <IconMapPin size={18} className="text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">{stats.trip_linked}</div>
          <div className="text-[11px] text-[var(--text-muted)] font-medium">Tickets & bookings</div>
        </div>

        {/* Expiring Soon */}
        <div className={`glass-card p-5 rounded-2xl border space-y-1 ${
          stats.expiring_soon > 0
            ? 'border-amber-500/40 bg-amber-500/5'
            : 'border-[var(--border-color)] bg-[var(--bg-card)]'
        }`}>
          <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
            <span>Expiring Soon</span>
            <IconAlertTriangle size={18} className={stats.expiring_soon > 0 ? 'animate-bounce' : ''} />
          </div>
          <div className="text-2xl font-black text-amber-600 dark:text-amber-400">{stats.expiring_soon}</div>
          <div className="text-[11px] text-[var(--text-muted)] font-medium">Within next 30 days</div>
        </div>

        {/* Expired / Active Ratio */}
        <div className={`glass-card p-5 rounded-2xl border space-y-1 ${
          stats.expired > 0
            ? 'border-rose-500/40 bg-rose-500/5'
            : 'border-[var(--border-color)] bg-[var(--bg-card)]'
        }`}>
          <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
            <span>Expired Documents</span>
            <IconClock size={18} />
          </div>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400">{stats.expired}</div>
          <div className="text-[11px] text-[var(--text-muted)] font-medium">Requires renewal</div>
        </div>
      </div>

      {/* ── 3. EXPIRY WARNING BANNER (IF ANY) ───────────────────────────────── */}
      {expiringOrExpiredDocs.length > 0 && (
        <div className="p-5 rounded-3xl bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-600 dark:text-amber-400 shrink-0">
              <IconAlertTriangle size={24} />
            </div>
            <div>
              <h4 className="text-sm font-bold">Document Expiry Alerts Detected</h4>
              <p className="text-xs opacity-90 mt-0.5">
                {stats.expiring_soon > 0 && `${stats.expiring_soon} document(s) expire within 30 days. `}
                {stats.expired > 0 && `${stats.expired} document(s) have passed their expiration date.`}
              </p>
            </div>
          </div>
          <button
            onClick={() => setSelectedStatus('Expiring Soon')}
            className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-sm transition-all shrink-0"
          >
            Filter Expiring Docs
          </button>
        </div>
      )}

      {/* ── 4. CONTROLS BAR: SEARCH, CATEGORIES, FILTERS ────────────────────── */}
      <div className="space-y-4">
        {/* Top Controls Row */}
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          {/* Search Bar */}
          <div className="relative w-full md:max-w-md">
            <IconSearch size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search documents by name, category, trip, or notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-3 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                Clear
              </button>
            )}
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-bold outline-none cursor-pointer"
            >
              <option value="All">All Statuses</option>
              <option value="Active">🟢 Active</option>
              <option value="Expiring Soon">⚠️ Expiring Soon</option>
              <option value="Expired">🔴 Expired</option>
              <option value="No Expiry">⚪ No Expiry</option>
            </select>

            {/* Trip Filter */}
            <select
              value={selectedTripId}
              onChange={(e) => setSelectedTripId(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-bold outline-none cursor-pointer"
            >
              <option value="All">All Trips</option>
              <option value="0">Personal / Unlinked</option>
              {trips.map((t) => (
                <option key={t.id} value={t.id}>{t.destination || t.title}</option>
              ))}
            </select>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-bold outline-none cursor-pointer"
            >
              <option value="recently_added">Recently Added</option>
              <option value="oldest">Oldest</option>
              <option value="name_asc">Name A-Z</option>
              <option value="expiry_asc">Earliest Expiry</option>
            </select>

            <button
              onClick={fetchVaultData}
              className="p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
              title="Refresh Vault"
            >
              <IconRefresh size={18} />
            </button>
          </div>
        </div>

        {/* Category Pills Slider */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar">
          {CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-xl text-xs font-bold tracking-wide whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:border-blue-500/40'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── 5. DOCUMENTS GRID / CARDS ───────────────────────────────────────── */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-10 h-10 mx-auto border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-[var(--text-muted)]">Loading travel documents...</p>
        </div>
      ) : documents.length === 0 ? (
        /* ── EMPTY STATE ──────────────────────────────────────────────────── */
        <div className="glass-card p-12 rounded-3xl border border-dashed border-[var(--border-color)] text-center space-y-4 max-w-lg mx-auto my-8">
          <div className="w-16 h-16 mx-auto rounded-3xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <IconLock size={36} />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-extrabold text-[var(--text-primary)] font-heading">
              Your travel documents are safe here
            </h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Upload passports, visas, flight tickets, hotel vouchers, driving licenses, and travel insurance for secure instant access.
            </p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-lg shadow-blue-500/25 transition-all"
          >
            <IconPlus size={18} />
            <span>Upload Your First Document</span>
          </button>
        </div>
      ) : (
        /* ── DOCUMENTS GRID ────────────────────────────────────────────────── */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {documents.map((doc) => {
            const isPdf = doc.mime_type?.includes('pdf') || doc.file_name?.endsWith('.pdf');
            const formattedSize = doc.file_size
              ? doc.file_size > 1024 * 1024
                ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB`
                : `${Math.round(doc.file_size / 1024)} KB`
              : 'PDF';

            let statusBadge = (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-500/10 text-slate-500 dark:text-slate-400 border border-slate-500/20">
                ⚪ No Expiry Date
              </span>
            );

            if (doc.status === 'EXPIRED') {
              statusBadge = (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30">
                  🔴 Expired
                </span>
              );
            } else if (doc.status === 'EXPIRING_SOON') {
              statusBadge = (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                  ⚠️ Expiring Soon ({doc.days_until_expiry}d)
                </span>
              );
            } else if (doc.status === 'ACTIVE') {
              statusBadge = (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                  🟢 Active
                </span>
              );
            }
            
            // Override status badge if processing
            if (doc.ocr_status === 'PROCESSING') {
              statusBadge = (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30 flex items-center gap-1">
                  <div className="w-2.5 h-2.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  ANALYZING DOCUMENT...
                </span>
              );
            }

            return (
              <div
                key={doc.id}
                onClick={() => setPreviewDoc(doc)}
                className="glass-card p-5 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:border-blue-500/40 hover:shadow-xl transition-all cursor-pointer group flex flex-col justify-between space-y-4"
              >
                {/* Top Row: Icon & Status */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400 group-hover:scale-105 transition-all shrink-0">
                        {isPdf ? <IconFileText size={24} className="text-rose-500" /> : <IconPhoto size={24} className="text-blue-500" />}
                      </div>
                      <span className="px-2.5 py-1 rounded-xl text-[10px] font-extrabold uppercase tracking-wider bg-[var(--bg-app)] text-[var(--text-secondary)] border border-[var(--border-color)]">
                        {doc.category}
                      </span>
                    </div>

                    <div>{statusBadge}</div>
                  </div>

                  {/* Name & Trip */}
                  <div>
                    <h4 className="text-base font-bold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-1">
                      {doc.name}
                    </h4>
                    <div className="flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 mt-1">
                      <IconMapPin size={14} />
                      <span className="truncate">{doc.trip_title || 'Personal / No Trip'}</span>
                    </div>
                    {doc.extraction_source === 'MRZ' && (
                      <div className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                        <IconCheck size={12} /> Extracted from MRZ
                      </div>
                    )}
                  </div>
                </div>

                {/* Expiry & Meta Details */}
                <div className="space-y-3 pt-3 border-t border-[var(--border-color)] text-xs">
                  <div className="flex items-center justify-between text-[var(--text-muted)] font-medium">
                    <span className="flex items-center gap-1">
                      <IconCalendar size={14} /> Expiry:
                    </span>
                    <span className="font-bold text-[var(--text-primary)]">
                      {doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'No Expiry'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[var(--text-muted)] font-medium">
                    <span>Format & Size:</span>
                    <span className="font-semibold text-[var(--text-secondary)] uppercase">
                      {isPdf ? 'PDF' : 'IMAGE'} · {formattedSize}
                    </span>
                  </div>

                  {/* Action Buttons Row */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewDoc(doc);
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold hover:bg-blue-500/20 transition-all"
                    >
                      <IconEye size={14} />
                      <span>View</span>
                    </button>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => handleDownload(e, doc)}
                        className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-blue-600 transition-all"
                        title="Download"
                      >
                        <IconDownload size={16} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditDoc(doc);
                        }}
                        className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-amber-600 transition-all"
                        title="Edit Metadata"
                      >
                        <IconPencil size={16} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteDocTarget(doc);
                        }}
                        className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-rose-500/10 hover:text-rose-500 transition-all"
                        title="Delete"
                      >
                        <IconTrash size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── MODALS ───────────────────────────────────────────────────────────── */}
      {/* 1. Upload Modal */}
      <UploadDocumentModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onSuccess={() => fetchVaultData()}
        trips={trips}
      />

      <DocumentPreviewModal
        isOpen={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
        document={previewDoc}
        onEdit={(docToEdit) => {
          setPreviewDoc(null);
          setEditDoc(docToEdit);
        }}
        onDelete={(docToDelete) => {
          setDeleteDocTarget(docToDelete);
        }}
        onAnalyze={async (docToAnalyze) => {
          try {
            const { analyzeDocument } = await import('../api/documents');
            await analyzeDocument(docToAnalyze.id);
            setPreviewDoc(null);
            fetchVaultData();
          } catch (err) {
            alert('Failed to analyze document.');
          }
        }}
      />

      {/* 3. Edit Metadata Modal */}
      <EditDocumentModal
        isOpen={!!editDoc}
        onClose={() => setEditDoc(null)}
        document={editDoc}
        onSuccess={() => fetchVaultData()}
        trips={trips}
      />

      {/* 4. Delete Confirmation Dialog */}
      {deleteDocTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] w-full max-w-md rounded-3xl p-6 shadow-2xl space-y-4 text-center">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-rose-500/10 text-rose-500 flex items-center justify-center">
              <IconTrash size={28} />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-[var(--text-primary)]">Delete Document?</h3>
              <p className="text-xs text-[var(--text-muted)]">
                Are you sure you want to delete <span className="font-bold text-[var(--text-primary)]">"{deleteDocTarget.name}"</span>? This will permanently remove the file from your vault.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setDeleteDocTarget(null)}
                className="px-5 py-2.5 rounded-xl text-xs font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-app)] transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-md shadow-rose-500/20 transition-all"
              >
                Delete Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
