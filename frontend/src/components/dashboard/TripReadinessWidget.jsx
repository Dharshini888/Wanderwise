import React from 'react';
import {
  IconCheck, IconAlertTriangle, IconCircleCheck,
  IconShieldCheck, IconMap, IconBackpack, IconWallet, IconCalendarEvent
} from '@tabler/icons-react';

export default function TripReadinessWidget({ trip, daysLeft = 0 }) {
  if (!trip) return null;

  const items = [
    { label: 'Itinerary Ready', status: 'ready', icon: <IconCalendarEvent size={16} className="text-emerald-500" />, badge: '🟢 Ready', pct: 100 },
    { label: 'Transit Guide', status: 'ready', icon: <IconMap size={16} className="text-emerald-500" />, badge: '🟢 Ready', pct: 100 },
    { label: 'Budget Planner', status: 'ready', icon: <IconWallet size={16} className="text-emerald-500" />, badge: '🟢 Active', pct: 100 },
    { label: 'Packing Checklist', status: 'pending', icon: <IconBackpack size={16} className="text-amber-500" />, badge: '🟡 Pending Review', pct: 60 },
    { label: 'Safety Guide', status: 'ready', icon: <IconShieldCheck size={16} className="text-emerald-500" />, badge: '🟢 Ready', pct: 100 },
  ];

  const overallScore = Math.round(items.reduce((sum, item) => sum + item.pct, 0) / items.length);

  return (
    <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
            <span>Trip Readiness Score</span>
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Preparation health before departure</p>
        </div>

        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-2xl">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-sm font-black text-emerald-600 dark:text-emerald-400 font-mono">
            {overallScore}% Ready
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-200 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-teal-500 via-emerald-500 to-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${overallScore}%` }}
        />
      </div>

      {/* Readiness Items List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 pt-1">
        {items.map((item, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-2xl border flex items-center justify-between text-xs font-bold transition-all ${
              item.status === 'ready'
                ? 'bg-emerald-500/5 border-emerald-500/20 text-[var(--text-primary)]'
                : 'bg-amber-500/5 border-amber-500/20 text-[var(--text-primary)]'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              {item.icon}
              <span className="truncate">{item.label}</span>
            </div>
            <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full shrink-0 ${
              item.status === 'ready'
                ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
            }`}>
              {item.status === 'ready' ? '✓ Ready' : '🟡 Review'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
