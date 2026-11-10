import React from 'react';
import {
  IconCompass, IconMapPin, IconCalendar, IconSun,
  IconWallet, IconSparkles, IconChevronDown
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function TripJourneyHeader({ todayData, trip, onResumeClick }) {
  if (!todayData) return null;

  const isCompleted = todayData.trip_status === 'Completed';
  const isActive = todayData.trip_status === 'Active';
  const isUpcoming = todayData.is_upcoming_trip || todayData.trip_status === 'Upcoming';
  const currCode = trip?.currency || 'USD';
  const budgetRemaining = trip?.budget_remaining ?? trip?.budget ?? 0;

  return (
    <div className="glass-card p-5 sm:p-6 rounded-2xl relative overflow-hidden group">
      {/* Background Gradient & Pattern */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-indigo-600/5 to-transparent pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        {/* Left Information */}
        <div className="space-y-2 max-w-xl">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border ${
              isActive
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                : isCompleted
                ? 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20'
                : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
            }`}>
              {isActive
                ? `🟢 Currently Exploring ${todayData.destination}`
                : isCompleted
                ? '⚪ Journey Completed'
                : `🔵 Upcoming Adventure (Starts ${todayData.date_formatted})`}
            </span>

            {isActive && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                Day {todayData.current_day} of {todayData.total_days}
              </span>
            )}
            {isUpcoming && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                {todayData.total_days} Days Scheduled
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading text-[var(--text-primary)] tracking-tight">
            {todayData.destination}{todayData.country ? `, ${todayData.country}` : ''}
          </h1>

          <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-secondary)] font-medium">
            <span className="flex items-center gap-1 font-semibold">
              <IconCalendar size={14} className="text-indigo-500" />
              {todayData.date_formatted} ({todayData.day_title})
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 font-bold text-amber-500">
              <IconSun size={14} />
              {todayData.weather?.condition || 'Clear 26°C'}
            </span>
          </div>
        </div>

        {/* Right Status & Primary CTA */}
        <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-3 w-full md:w-auto shrink-0 border-t md:border-t-0 pt-3 md:pt-0 border-[var(--border-color)]">
          <div className="text-left md:text-right">
            <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Remaining Budget</div>
            <div className="text-xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 font-heading">
              {formatCurrency(budgetRemaining, currCode)}
            </div>
          </div>

          {isActive && (
            <button
              onClick={onResumeClick}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[var(--color-primary-600)] hover:bg-blue-700 text-white font-extrabold text-xs transition-all shadow-md flex items-center justify-center gap-1.5"
            >
              <IconSparkles size={16} /> Resume Today's Journey <IconChevronDown size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
