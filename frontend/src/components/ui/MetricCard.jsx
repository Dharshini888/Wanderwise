import React from 'react';
import TravelCard from './TravelCard';

export default function MetricCard({ label, value, icon: Icon, subtext, trend, highlight }) {
  return (
    <TravelCard padding="p-5" hover={false} className={highlight ? 'border-blue-500/40 bg-blue-500/5' : ''}>
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
            {label}
          </span>
          <div className="text-2xl font-black text-[var(--text-primary)] font-heading">
            {value}
          </div>
        </div>
        {Icon && (
          <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0">
            <Icon size={22} />
          </div>
        )}
      </div>
      {(subtext || trend) && (
        <div className="mt-3 pt-2.5 border-t border-[var(--border-color)] flex items-center justify-between text-xs text-[var(--text-muted)] font-medium">
          <span>{subtext}</span>
          {trend && <span className="font-bold text-emerald-600 dark:text-emerald-400">{trend}</span>}
        </div>
      )}
    </TravelCard>
  );
}
