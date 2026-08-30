import React from 'react';

export default function ProviderBadge({ provider = 'RailRadar' }) {
  let badgeColor = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';

  if (provider?.toLowerCase().includes('osrm')) {
    badgeColor = 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20';
  } else if (provider?.toLowerCase().includes('transitous')) {
    badgeColor = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
  } else if (provider?.toLowerCase().includes('openmeteo')) {
    badgeColor = 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20';
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold border tracking-wide uppercase ${badgeColor}`}>
      {provider}
    </span>
  );
}
