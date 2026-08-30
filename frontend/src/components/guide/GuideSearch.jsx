import React, { useState } from 'react';
import { IconSearch, IconCurrentLocation, IconMapPin, IconX } from '@tabler/icons-react';

export default function GuideSearch({ destination, onSearch, onUseLocation, loading }) {
  const [inputVal, setInputVal] = useState(destination || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputVal.trim()) {
      onSearch(inputVal.trim());
    }
  };

  const handleClear = () => {
    setInputVal('');
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative flex flex-col sm:flex-row items-center gap-2">
        <div className="relative flex-1 w-full">
          <IconSearch size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none" />
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Search destination, city, landmark (e.g. Coimbatore, Tokyo, Paris)..."
            className="w-full pl-10 pr-9 py-3 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] text-xs font-semibold text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-xs transition-all"
          />
          {inputVal && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] transition-colors cursor-pointer"
            >
              <IconX size={14} />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
          <button
            type="submit"
            disabled={loading || !inputVal.trim()}
            className="flex-1 sm:flex-initial px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <IconSearch size={16} />
            <span>Search</span>
          </button>

          {onUseLocation && (
            <button
              type="button"
              onClick={onUseLocation}
              disabled={loading}
              className="px-4 py-3 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] hover:bg-[var(--bg-subtle)] text-[var(--text-primary)] text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer shrink-0"
              title="Use current GPS location"
            >
              <IconCurrentLocation size={16} className="text-blue-500" />
              <span className="hidden md:inline">Use my location</span>
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
