import {
  IconStethoscope,
  IconFileText,
  IconUpload,
  IconAlertTriangle,
  IconCamera,
  IconShieldCheck,
  IconTrash,
  IconCalendar,
} from '@tabler/icons-react';

export default function HealthAndDocs() {
  const documents = [
    { id: 1, type: 'Passport', expiry: '2027-03-15', status: 'Valid' },
    { id: 2, type: 'Japan e-Visa', expiry: '2023-10-01', status: 'Expired' }
  ];

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

          <div className="flex flex-col gap-3">
            {documents.map(doc => {
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
                      <div className="text-sm font-bold text-[var(--text-primary)] font-heading">{doc.type}</div>
                      <div className="text-[10px] text-[var(--text-muted)] font-semibold flex items-center gap-1 mt-0.5">
                        <IconCalendar size={12} />
                        Expires: {doc.expiry}
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
                    <button className="p-1 text-[var(--text-muted)] hover:text-red-500 transition-colors">
                      <IconTrash size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <button className="btn btn-primary w-full py-3.5 mt-2 text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer">
            <IconUpload size={16} />
            <span>Upload Document</span>
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
