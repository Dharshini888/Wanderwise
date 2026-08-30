import React from 'react';

export default function FilterBar({ categories = [], selected, onSelect, className = '' }) {
  return (
    <div className={`flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar ${className}`}>
      {categories.map((cat) => {
        const isSelected = selected === cat;
        return (
          <button
            key={cat}
            type="button"
            onClick={() => onSelect(cat)}
            className={`px-4 py-2 rounded-xl text-xs font-bold tracking-wide whitespace-nowrap transition-all cursor-pointer ${
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
  );
}
