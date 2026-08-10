import { useState, useEffect, useRef } from 'react';
import {
  IconStethoscope,
  IconFileText,
  IconUpload,
  IconAlertTriangle,
  IconCamera,
  IconShieldCheck,
  IconTrash,
  IconCalendar,
  IconDownload,
} from '@tabler/icons-react';

export default function HealthAndDocs() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  
  const token = localStorage.getItem('token');
  const API = 'http://localhost:8000/api';

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API}/health-safety/documents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', file.name.split('.')[0] || 'Document');
    // Optional: could ask user for expiry date, setting to empty for now
    
    setUploading(true);
    try {
      const res = await fetch(`${API}/health-safety/documents`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      if (res.ok) {
        fetchDocuments();
      } else {
        const errorData = await res.json();
        alert(`Upload failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Upload error", err);
      alert("Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this document?")) return;
    try {
      const res = await fetch(`${API}/health-safety/documents/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchDocuments();
      } else {
        alert("Failed to delete document");
      }
    } catch (err) {
      console.error("Delete error", err);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const res = await fetch(`http://localhost:8000${doc.url}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to download");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${doc.document_type || 'document'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download error", err);
      alert("Failed to download document");
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconStethoscope className="text-[var(--color-primary-600)]" size={32} /> Health & Documents Vault
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Safeguard travel documents offline and monitor food allergy alerts.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start max-w-5xl">
        
        {/* Visa & Docs Vault */}
        <div className="glass-card p-6 flex flex-col gap-5 bg-[var(--bg-card)]">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)] font-heading mb-1 flex items-center gap-2">
              <IconShieldCheck size={20} className="text-emerald-500" /> Digital Document Vault
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-medium">Encrypted file vault for passports, visas, and health cards.</p>
          </div>

          <div className="flex flex-col gap-3 min-h-[150px]">
            {loading ? (
              <div className="flex items-center justify-center h-full text-[var(--text-muted)]">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="flex items-center justify-center h-full text-[var(--text-muted)] text-sm italic">No documents found. Upload one below.</div>
            ) : (
              documents.map(doc => {
                const isValid = doc.status === 'Valid';
                return (
                  <div 
                    key={doc.id} 
                    className={`flex justify-between items-center p-4 bg-[var(--bg-app)] border-l-4 rounded-r-xl border border-[var(--border-color)] ${
                      isValid ? 'border-l-emerald-500' : 'border-l-red-500'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)]">
                        <IconFileText size={18} />
                      </span>
                      <div>
                        <div className="text-sm font-bold text-[var(--text-primary)] font-heading">{doc.document_type}</div>
                        <div className="text-[10px] text-[var(--text-muted)] font-semibold flex items-center gap-1 mt-0.5">
                          <IconCalendar size={12} />
                          Expires: {doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString() : 'N/A'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isValid 
                          ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400' 
                          : 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400'
                      }`}>
                        {doc.status}
                      </span>
                      <button onClick={() => handleDownload(doc)} className="p-1 text-[var(--text-muted)] hover:text-blue-500 transition-colors" title="Download">
                        <IconDownload size={16} />
                      </button>
                      <button onClick={() => handleDelete(doc.id)} className="p-1 text-[var(--text-muted)] hover:text-red-500 transition-colors" title="Delete">
                        <IconTrash size={16} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept="image/jpeg,image/png,application/pdf"
          />
          <button 
            onClick={handleUploadClick}
            disabled={uploading}
            className="btn btn-primary w-full py-3.5 mt-2 text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
          >
            <IconUpload size={16} />
            <span>{uploading ? 'Uploading...' : 'Upload Document'}</span>
          </button>
        </div>

        {/* Health & Allergy Scanner */}
        <div className="glass-card p-6 flex flex-col gap-6 bg-[var(--bg-card)]">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)] font-heading mb-1 flex items-center gap-2">
              <IconCamera size={20} className="text-blue-500" /> Dietary & Menu Scanner
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-medium">Scan foreign restaurant menus to highlight custom allergens.</p>
          </div>

          <div className="border-2 border-dashed border-[var(--border-color)] rounded-xl p-8 text-center bg-[var(--bg-app)] hover:bg-[var(--border-color)]/20 transition-colors cursor-pointer flex flex-col items-center justify-center gap-2 group">
            <span className="text-4xl text-[var(--text-muted)] group-hover:scale-110 transition-transform"><IconCamera size={36} /></span>
            <div className="text-xs font-bold text-[var(--text-primary)]">Scan Menu Photo</div>
            <p className="text-[10px] text-[var(--text-muted)] max-w-[180px] leading-relaxed">OCR extracts text and translates menu to screen for instant scanning.</p>
          </div>
          
          <div className="p-4 bg-red-50/50 dark:bg-red-950/10 border border-red-200/50 dark:border-red-900/10 rounded-2xl flex items-start gap-3 animate-pulse">
            <IconAlertTriangle className="text-red-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h4 className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider mb-1">Allergen Warning Alert</h4>
              <p className="text-[11px] text-red-700 dark:text-red-300 leading-relaxed font-medium">
                Based on your profile details, the last scanned menu contains **peanuts**. Please cross-check with waitstaff before ordering.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
