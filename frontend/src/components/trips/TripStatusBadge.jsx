import React from 'react';

const STATUS_CONFIG = {
  Active: {
    style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold',
    dot: 'bg-emerald-400 animate-ping',
    icon: '🟢',
    label: 'Active'
  },
  'In Progress': {
    style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold',
    dot: 'bg-emerald-400 animate-ping',
    icon: '🟢',
    label: 'Active'
  },
  Upcoming: {
    style: 'bg-blue-500/10 text-blue-400 border-blue-500/30 font-bold',
    dot: 'bg-blue-400',
    icon: '🔵',
    label: 'Upcoming'
  },
  Completed: {
    style: 'bg-gray-500/10 text-gray-300 border-gray-500/30 font-semibold',
    dot: 'bg-gray-400',
    icon: '⚪',
    label: 'Completed'
  },
  Cancelled: {
    style: 'bg-red-500/10 text-red-400 border-red-500/30 font-bold',
    dot: 'bg-red-400',
    icon: '🔴',
    label: 'Cancelled'
  },
  Archived: {
    style: 'bg-amber-500/10 text-amber-400 border-amber-500/30 font-medium',
    dot: 'bg-amber-400',
    icon: '📦',
    label: 'Archived'
  }
};

export default function TripStatusBadge({ status = 'Upcoming' }) {
  const normalized = (status === 'In Progress' ? 'Active' : status);
  const cfg = STATUS_CONFIG[normalized] || STATUS_CONFIG[status] || STATUS_CONFIG.Upcoming;

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs border backdrop-blur-md shadow-sm ${cfg.style}`}>
      <span className="relative flex h-2 w-2">
        <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${cfg.dot}`} />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${cfg.dot.split(' ')[0]}`} />
      </span>
      <span>{cfg.label}</span>
    </span>
  );
}
