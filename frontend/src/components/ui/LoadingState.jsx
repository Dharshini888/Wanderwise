import React from 'react';

export default function LoadingState({ count = 3, type = 'card' }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="travel-card p-6 space-y-4 animate-pulse">
          <div className="h-4 bg-[var(--bg-subtle)] rounded-md w-1/3" />
          <div className="h-6 bg-[var(--bg-subtle)] rounded-md w-3/4" />
          <div className="h-12 bg-[var(--bg-subtle)] rounded-xl w-full" />
        </div>
      ))}
    </div>
  );
}
