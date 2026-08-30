import React, { useState, useEffect } from 'react';
import {
  IconX, IconDownload, IconPencil, IconTrash, IconFileText, IconPhoto,
  IconAlertTriangle, IconCheck, IconCalendar, IconMapPin, IconTag,
  IconNotes, IconClock, IconShieldCheck, IconExternalLink, IconLock
} from '@tabler/icons-react';
import { downloadDocumentFile } from '../../api/documents';

import { IconRefresh, IconEye, IconEyeOff, IconWand } from '@tabler/icons-react';

export default function DocumentPreviewModal({ isOpen, onClose, document: doc, onEdit, onDelete, onAnalyze }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewError, setPreviewError] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [showSensitive, setShowSensitive] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (doc && isOpen) {
      setPreviewError(false);
      // Construct inline preview URL using auth header or blob URL
      const token = localStorage.getItem('token');
      // For images/iframe in browser, fetch blob or append token query
      let isMounted = true;

      const fetchBlobUrl = async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/documents/${doc.id}/download?disposition=inline`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {}
          });
          if (res.ok) {
            const blob = await res.blob();
            const objectUrl = URL.createObjectURL(blob);
            if (isMounted) setPreviewUrl(objectUrl);
          } else {
            if (isMounted) setPreviewError(true);
          }
        } catch (err) {
          if (isMounted) setPreviewError(true);
        }
      };

      fetchBlobUrl();

      return () => {
        isMounted = false;
        if (previewUrl) URL.revokeObjectURL(previewUrl);
      };
    }
  }, [doc, isOpen]);

  if (!isOpen || !doc) return null;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadDocumentFile(doc.id, doc.file_name, 'attachment');
    } catch (_) {
      alert('Failed to download document.');
    } finally {
      setDownloading(false);
    }
  };

  const isPdf = doc.mime_type?.includes('pdf') || doc.file_name?.endsWith('.pdf');
  const isImage = doc.mime_type?.includes('image') || /\.(jpg|jpeg|png|webp)$/i.test(doc.file_name);

  // Status Styling
  let statusBadge = (
    <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">
      ⚪ No Expiry Date
    </span>
  );

  if (doc.status === 'EXPIRED') {
    statusBadge = (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30">
        🔴 Expired
      </span>
    );
  } else if (doc.status === 'EXPIRING_SOON') {
    statusBadge = (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
        ⚠️ Expiring Soon ({doc.days_until_expiry != null ? `${doc.days_until_expiry} days left` : '30 days'})
      </span>
    );
  } else if (doc.status === 'ACTIVE') {
    statusBadge = (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
        🟢 Active
      </span>
    );
  }

  const formattedSize = doc.file_size
    ? doc.file_size > 1024 * 1024
      ? `${(doc.file_size / (1024 * 1024)).toFixed(2)} MB`
      : `${Math.round(doc.file_size / 1024)} KB`
    : 'Unknown size';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] w-full max-w-4xl rounded-3xl shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-glass)]">
          <div className="flex items-center gap-3 truncate">
            <div className="p-2.5 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0">
              {isPdf ? <IconFileText size={24} /> : <IconPhoto size={24} />}
            </div>
            <div className="truncate">
              <h3 className="text-lg font-bold text-[var(--text-primary)] truncate">{doc.name}</h3>
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <span className="font-semibold">{doc.category}</span>
                <span>·</span>
                <span>{doc.file_name}</span>
                <span>·</span>
                <span>{formattedSize}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 shadow-md shadow-blue-500/20 transition-all"
            >
              <IconDownload size={16} />
              <span>Download</span>
            </button>
            {onEdit && (
              <button
                onClick={() => onEdit(doc)}
                className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)] transition-all"
                title="Edit Document Metadata"
              >
                <IconPencil size={18} />
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(doc)}
                className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-all"
                title="Delete Document"
              >
                <IconTrash size={18} />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-[var(--text-muted)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)] transition-all ml-2"
            >
              <IconX size={20} />
            </button>
          </div>
        </div>

        {/* Content Body: Split Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 overflow-hidden">
          {/* Left / Metadata Pane */}
          <div className="p-6 border-r border-[var(--border-color)] bg-[var(--bg-glass)] overflow-y-auto space-y-5 custom-scrollbar">
            {/* Status & Warning Banner */}
            <div className="space-y-3">
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Document Status</div>
              <div>{statusBadge}</div>
              
              {/* OCR STATUS BADGE */}
              {doc.ocr_status && (
                <div className="mt-2">
                  {doc.ocr_status === 'PROCESSING' && (
                    <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30 flex items-center gap-1.5 w-fit">
                      <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      Analyzing Document...
                    </span>
                  )}
                  {doc.ocr_status === 'SUCCESS' && (
                    <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 w-fit">
                      <IconCheck size={14} /> Document analyzed
                    </span>
                  )}
                  {doc.ocr_status === 'PARTIAL' && (
                    <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1.5 w-fit">
                      <IconAlertTriangle size={14} /> Some info extracted
                    </span>
                  )}
                  {doc.ocr_status === 'FAILED' && (
                    <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30 flex items-center gap-1.5 w-fit">
                      <IconAlertTriangle size={14} /> OCR failed
                    </span>
                  )}
                  {doc.ocr_status === 'NO_TEXT' && (
                    <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold bg-slate-500/10 text-slate-500 dark:text-slate-400 border border-slate-500/30 flex items-center gap-1.5 w-fit">
                      <IconFileText size={14} /> No readable text detected
                    </span>
                  )}
                </div>
              )}

              {doc.status === 'EXPIRING_SOON' && (
                <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-semibold flex items-center gap-2">
                  <IconAlertTriangle size={18} className="shrink-0" />
                  <span>Document expires in {doc.days_until_expiry} days. Please prepare renewal if required.</span>
                </div>
              )}
              {doc.status === 'EXPIRED' && (
                <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-2">
                  <IconAlertTriangle size={18} className="shrink-0" />
                  <span>This document has expired. Do not use for current travel.</span>
                </div>
              )}
            </div>

            {/* Key Metadata Table */}
            <div className="space-y-3 pt-3 border-t border-[var(--border-color)] text-xs">
              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                  <IconTag size={14} /> Category
                </span>
                <span className="font-bold text-[var(--text-primary)]">{doc.category}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                  <IconMapPin size={14} /> Associated Trip
                </span>
                <span className="font-bold text-blue-600 dark:text-blue-400">
                  {doc.trip_title || 'Personal / No Trip'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                  <IconCalendar size={14} /> Expiry Date
                </span>
                <span className="font-bold text-[var(--text-primary)]">
                  {doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'No Expiry Date'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                  <IconClock size={14} /> Uploaded Date
                </span>
                <span className="font-bold text-[var(--text-primary)]">
                  {doc.created_at ? new Date(doc.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Recently'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                  <IconShieldCheck size={14} /> Privacy & Security
                </span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <IconLock size={12} /> Encrypted Access
                </span>
              </div>
            </div>

            {/* Notes Section */}
            {doc.notes && (
              <div className="pt-3 border-t border-[var(--border-color)]">
                <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <IconNotes size={14} /> Notes & Details
                </div>
                <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
                  {doc.notes}
                </div>
              </div>
            )}
            {/* OCR Extracted Metadata Section */}
            {doc.extracted_metadata && Object.keys(doc.extracted_metadata).length > 0 && (
              <div className="pt-3 border-t border-[var(--border-color)] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                    <IconWand size={14} /> AI Extracted Info
                  </div>
                  <button
                    onClick={() => setShowSensitive(!showSensitive)}
                    className="p-1 rounded-lg hover:bg-slate-500/10 text-slate-500 transition-colors"
                    title={showSensitive ? 'Hide sensitive data' : 'Reveal sensitive data'}
                  >
                    {showSensitive ? <IconEyeOff size={14} /> : <IconEye size={14} />}
                  </button>
                </div>
                <div className="grid grid-cols-1 gap-2 text-xs">
                  {Object.entries(doc.extracted_metadata).map(([key, val]) => {
                    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    const isSensitive = ['passport_number', 'document_number'].includes(key);
                    const isName = ['surname', 'given_names', 'full_name'].includes(key);
                    
                    let displayVal = val;
                    if (!showSensitive) {
                      if (isSensitive) {
                        displayVal = val.length > 3 ? 'X'.repeat(val.length - 3) + val.slice(-3) : 'XXX';
                      } else if (isName) {
                        displayVal = val.length > 2 ? val[0] + '*'.repeat(val.length - 2) + val[val.length - 1] : val;
                      }
                    }

                    return (
                      <div key={key} className="flex flex-col gap-0.5 p-2 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)]">
                        <span className="text-[9px] font-bold text-[var(--text-muted)] uppercase">{formattedKey}</span>
                        <span className="font-semibold text-[var(--text-primary)]">{displayVal}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Analyze Button for Failed/Partial Docs */}
            {(!doc.ocr_status || ['FAILED', 'NO_TEXT', 'PARTIAL', 'NO_EXPIRY'].includes(doc.ocr_status)) && onAnalyze && (
              <div className="pt-3 border-t border-[var(--border-color)]">
                <button
                  onClick={async () => {
                    setAnalyzing(true);
                    await onAnalyze(doc);
                    setAnalyzing(false);
                  }}
                  disabled={analyzing}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-blue-600 bg-blue-500/10 hover:bg-blue-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-blue-500/20"
                >
                  {analyzing ? <IconRefresh size={14} className="animate-spin" /> : <IconWand size={14} />}
                  {analyzing ? 'Analyzing...' : 'Analyze Document'}
                </button>
              </div>
            )}
          </div>

          {/* Right / Live Preview Pane */}
          <div className="lg:col-span-2 bg-slate-900/90 flex flex-col items-center justify-center p-4 relative overflow-hidden">
            {previewUrl ? (
              isPdf ? (
                <iframe
                  src={previewUrl}
                  className="w-full h-full rounded-2xl border border-slate-700 bg-white"
                  title={doc.name}
                />
              ) : isImage ? (
                <div className="w-full h-full flex items-center justify-center overflow-auto">
                  <img
                    src={previewUrl}
                    alt={doc.name}
                    className="max-w-full max-h-full object-contain rounded-2xl shadow-2xl border border-slate-700"
                  />
                </div>
              ) : (
                <div className="text-center text-slate-300 space-y-4">
                  <IconFileText size={48} className="mx-auto text-blue-400" />
                  <p className="text-sm font-semibold">{doc.file_name}</p>
                  <button
                    onClick={handleDownload}
                    className="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs"
                  >
                    Download File to View
                  </button>
                </div>
              )
            ) : previewError ? (
              <div className="text-center text-slate-400 space-y-3 p-6">
                <IconAlertTriangle size={40} className="mx-auto text-amber-400" />
                <p className="text-sm font-medium">Inline preview unavailable for this document format.</p>
                <button
                  onClick={handleDownload}
                  className="px-5 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold"
                >
                  Download File
                </button>
              </div>
            ) : (
              <div className="text-center text-slate-400 space-y-3">
                <div className="w-8 h-8 mx-auto border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-xs font-medium">Loading document preview...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
