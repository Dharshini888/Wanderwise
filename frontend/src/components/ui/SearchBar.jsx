import React from 'react';
import { IconSearch, IconX } from '@tabler/icons-react';

export default function SearchBar({ value, onChange, placeholder = 'Search...', className = '' }) {
  return (
    <div className={`relative w-full ${className}`}>
      <IconSearch size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-11 pr-9 py-2.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm font-medium focus:ring-2 focus:ring-blue-500 outline-none transition-all"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          <IconX size={14} />
        </button>
      )}
    </div>
  );
}
