import React from 'react';
import {
  IconPlane, IconCalendarEvent, IconActivity, IconChecklist,
  IconWorld, IconWallet, IconClock, IconMapPins
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function TripStatsHeader({ stats, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 glass-card rounded-2xl" />
        ))}
      </div>
    );
  }

  const s = stats || {};

  const primaryStats = [
    { label: 'Total Trips', value: s.totalTrips || 0, icon: IconPlane, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
    { label: 'Upcoming', value: s.upcoming || 0, icon: IconCalendarEvent, color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
    { label: 'Active', value: s.active || 0, icon: IconActivity, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
    { label: 'Completed', value: s.completed || 0, icon: IconChecklist, color: 'text-teal-600 dark:text-teal-400', bg: 'bg-teal-50 dark:bg-teal-900/20' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {primaryStats.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className="glass-card p-3.5 flex items-center gap-3 hover:scale-[1.01] transition-all"
          >
            <div className={`p-2 rounded-xl ${item.bg} ${item.color} shrink-0`}>
              <Icon size={18} />
            </div>
            <div>
              <p className="text-xl font-bold font-heading text-[var(--text-primary)] tracking-tight leading-none">
                {item.value}
              </p>
              <p className="text-[11px] font-semibold text-[var(--text-muted)] mt-1">
                {item.label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
