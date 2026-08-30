import React, { useState, useEffect } from 'react';
import {
  IconFileText, IconPlus, IconDownload, IconExternalLink,
  IconAlertTriangle, IconCheck, IconPhoto
} from '@tabler/icons-react';
import { getDocuments, downloadDocumentFile } from '../../api/documents';
import UploadDocumentModal from '../documents/UploadDocumentModal';
import DocumentPreviewModal from '../documents/DocumentPreviewModal';

export default function TripDocumentsWidget({ tripId, tripTitle }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showUpload, setShowUpload] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);

  const fetchTripDocs = async () => {
    if (!tripId) return;
    setLoading(true);
    try {
      const res = await getDocuments({ tripId: parseInt(tripId) });
      setDocuments(res.documents || []);
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTripDocs();
  }, [tripId]);

  const handleDownload = async (e, doc) => {
    e.stopPropagation();
    try {
      await downloadDocumentFile(doc.id, doc.file_name, 'attachment');
    } catch (_) {
      alert('Failed to download document.');
    }
  };

  return (
    <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <IconFileText size={22} />
          </div>
          <div>
            <h4 className="text-base font-black text-[var(--text-primary)]">
              Trip Documents & Tickets
            </h4>
            <p className="text-xs text-[var(--text-muted)]">
              Passports, boarding passes, visas, and hotel vouchers for this trip
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all"
        >
          <IconPlus size={16} />
          <span>Add Document</span>
        </button>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-[var(--text-muted)]">
          Loading trip documents...
        </div>
      ) : documents.length === 0 ? (
        <div className="p-6 rounded-2xl bg-[var(--bg-glass)] border border-dashed border-[var(--border-color)] text-center space-y-2">
          <IconFileText size={32} className="mx-auto text-[var(--text-muted)]" />
          <p className="text-xs font-bold text-[var(--text-primary)]">No documents attached to this trip yet.</p>
          <p className="text-[11px] text-[var(--text-muted)]">
            Upload your tickets, hotel confirmations, or visa for quick access during travel.
          </p>
          <button
            onClick={() => setShowUpload(true)}
            className="px-4 py-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold hover:bg-blue-500/20 transition-all mt-2"
          >
            + Attach Document
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {documents.map((doc) => {
            const isPdf = doc.mime_type?.includes('pdf') || doc.file_name?.endsWith('.pdf');
            return (
              <div
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className="p-3.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-glass)] hover:border-blue-500/40 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5 truncate">
                    <div className="p-2 rounded-xl bg-slate-500/10 text-slate-600 dark:text-slate-300 shrink-0">
                      {isPdf ? <IconFileText size={18} className="text-rose-500" /> : <IconPhoto size={18} className="text-blue-500" />}
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-bold text-[var(--text-primary)] truncate">{doc.name}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">{doc.category}</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDownload(e, doc)}
                    className="p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-blue-600 transition-all shrink-0"
                    title="Download File"
                  >
                    <IconDownload size={16} />
                  </button>
                </div>

                <div className="flex items-center justify-between text-[10px] pt-2 border-t border-[var(--border-color)]">
                  <span className="text-[var(--text-muted)]">
                    {doc.expiry_date ? `Exp: ${new Date(doc.expiry_date).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}` : 'No expiry'}
                  </span>
                  {doc.status === 'EXPIRED' ? (
                    <span className="font-bold text-rose-500">🔴 Expired</span>
                  ) : doc.status === 'EXPIRING_SOON' ? (
                    <span className="font-bold text-amber-500">⚠️ Expiring Soon</span>
                  ) : (
                    <span className="font-bold text-emerald-500">🟢 Active</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Modal Pre-selected for this Trip */}
      <UploadDocumentModal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        onSuccess={() => fetchTripDocs()}
        initialTripId={tripId}
      />

      {/* Document Preview Modal */}
      <DocumentPreviewModal
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        document={selectedDoc}
      />
    </div>
  );
}
