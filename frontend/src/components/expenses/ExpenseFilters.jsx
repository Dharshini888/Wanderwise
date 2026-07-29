import React from 'react';
import { IconSearch, IconFilter } from '@tabler/icons-react';

const CATEGORIES = ['All', 'Accommodation', 'Food', 'Transport', 'Shopping', 'Activities', 'Healthcare', 'Insurance', 'Emergency', 'Misc'];
const SOURCES = ['All', 'MANUAL', 'OCR', 'AI', 'IMPORT'];

export default function ExpenseFilters({ search, onSearchChange, category, onCategoryChange, source, onSourceChange }) {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm">
      {/* Search Bar */}
      <div className="relative flex-1">
        <IconSearch size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search merchant, location, or notes..."
          className="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 text-xs font-semibold"
        />
      </div>

      {/* Category Dropdown */}
      <div className="flex items-center gap-2">
        <IconFilter size={16} className="text-gray-400 shrink-0" />
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 text-xs font-semibold"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>
          ))}
        </select>

        <select
          value={source}
          onChange={(e) => onSourceChange(e.target.value)}
          className="px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 text-xs font-semibold"
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>{s === 'All' ? 'All Sources' : s}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
