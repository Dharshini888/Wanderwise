import React from 'react';
import { IconActivity, IconWalk, IconClock, IconReceipt2 } from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function TripProgressCard({ progress, currency = 'USD', isUpcoming = false, startDateFormatted = '' }) {
  if (!progress) return null;

  const pct = progress.percentage || 0;
  const completed = progress.completed_count || 0;
  const total = progress.total_count || 0;
  const upcomingTrip = isUpcoming || progress.is_upcoming_trip || (progress.walking_distance_km === 0 && progress.spent_today === 0 && completed === 0);

  return (
    <div className="glass-card p-4 sm:p-5 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
          <IconActivity size={18} className="text-blue-500" />
          {upcomingTrip ? "Day 1 Preview & Schedule" : "Today's Execution Progress"}
        </h3>
        <span className="text-xs font-black text-[var(--color-primary-600)] dark:text-blue-400">
          {upcomingTrip ? `${total} Activities Ready` : `${pct}% Completed`}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-[var(--text-muted)] font-semibold">
          <span>
            {upcomingTrip
              ? `0 of ${total} activities completed • Ready for departure ${startDateFormatted ? `(${startDateFormatted})` : ''}`
              : `${completed} of ${total} activities finished`}
          </span>
          <span>{pct}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* 3 Metric Pills */}
      <div className="grid grid-cols-3 gap-2 pt-1 text-center">
        <div className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <div className="flex items-center justify-center gap-1 text-[10px] font-bold text-[var(--text-muted)] uppercase">
            <IconWalk size={12} className="text-cyan-500" /> Distance
          </div>
          <div className="text-xs sm:text-sm font-extrabold text-[var(--text-primary)] mt-0.5">
            {total === 0 ? '0 km' : `${progress.walking_distance_km ?? 0} km`}
          </div>
        </div>

        <div className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <div className="flex items-center justify-center gap-1 text-[10px] font-bold text-[var(--text-muted)] uppercase">
            <IconClock size={12} className="text-purple-500" /> Walking
          </div>
          <div className="text-xs sm:text-sm font-extrabold text-[var(--text-primary)] mt-0.5">
            {total === 0 ? '0 mins' : `${progress.walking_time_mins ?? 0} mins`}
          </div>
        </div>

        <div className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <div className="flex items-center justify-center gap-1 text-[10px] font-bold text-[var(--text-muted)] uppercase">
            <IconReceipt2 size={12} className="text-emerald-500" /> Spent Today
          </div>
          <div className="text-xs sm:text-sm font-extrabold text-emerald-600 dark:text-emerald-400 mt-0.5">
            {formatCurrency(progress.spent_today || 0, currency)}
          </div>
        </div>
      </div>
    </div>
  );
}
