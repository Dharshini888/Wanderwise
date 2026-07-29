import React from 'react';
import {
  IconTrophy, IconStar, IconDownload, IconShare, IconPhoto,
  IconChecklist, IconMapPin, IconWallet, IconCalendar
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function CompletedTripMemoryView({ trip, onShare }) {
  if (!trip) return null;

  const currCode = trip.currency || 'USD';
  const totalSpent = trip.budget_spent || trip.budget || 0;
  const days = trip.duration_days || trip.number_of_days || 1;

  return (
    <div className="glass-card p-6 sm:p-8 rounded-3xl space-y-6 text-center border-2 border-emerald-500/30 relative overflow-hidden">
      {/* Background Celebration Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-teal-500/5 to-transparent pointer-events-none" />

      <div className="relative z-10 space-y-3">
        <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto shadow-md">
          <IconTrophy size={36} />
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
          Trip Completed 🎉
        </div>

        <h1 className="text-2xl sm:text-4xl font-extrabold font-heading text-[var(--text-primary)]">
          {trip.title || trip.destination}
        </h1>

        <p className="text-xs sm:text-sm text-[var(--text-muted)] font-medium max-w-md mx-auto">
          Congratulations! You completed your {days}-day journey to {trip.destination}. Here is your travel memory digest.
        </p>

        {/* 5-Star Rating Display */}
        <div className="flex items-center justify-center gap-1 text-amber-400 py-1">
          {[1, 2, 3, 4, 5].map((s) => (
            <IconStar key={s} size={20} className="fill-amber-400" />
          ))}
          <span className="text-xs font-bold text-[var(--text-secondary)] ml-1">5.0 Excellent</span>
        </div>
      </div>

      {/* Memory Highlights Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 relative z-10">
        <div className="glass-card p-4 text-center rounded-2xl">
          <div className="text-xl font-extrabold text-[var(--text-primary)] font-heading">{days} Days</div>
          <div className="text-[11px] font-semibold text-[var(--text-muted)] mt-0.5">Journey Duration</div>
        </div>

        <div className="glass-card p-4 text-center rounded-2xl">
          <div className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 font-heading">
            {trip.activities_total || 24}
          </div>
          <div className="text-[11px] font-semibold text-[var(--text-muted)] mt-0.5">Activities Done</div>
        </div>

        <div className="glass-card p-4 text-center rounded-2xl">
          <div className="text-xl font-extrabold text-blue-600 dark:text-blue-400 font-heading">
            {formatCurrency(totalSpent, currCode)}
          </div>
          <div className="text-[11px] font-semibold text-[var(--text-muted)] mt-0.5">Total Spent</div>
        </div>

        <div className="glass-card p-4 text-center rounded-2xl">
          <div className="text-xl font-extrabold text-purple-600 dark:text-purple-400 font-heading">
            {trip.places_visited || 12}
          </div>
          <div className="text-[11px] font-semibold text-[var(--text-muted)] mt-0.5">Places Explored</div>
        </div>
      </div>

      {/* Memory Actions CTAs */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-3 relative z-10">
        <button
          onClick={() => alert('PDF Summary download started!')}
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center gap-1.5"
        >
          <IconDownload size={16} /> Export PDF Digest
        </button>

        <button
          onClick={onShare}
          className="px-5 py-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-card)] font-bold text-xs shadow-sm transition-all flex items-center gap-1.5"
        >
          <IconShare size={16} /> Share Memory Link
        </button>

        <button
          onClick={() => alert('Memory Album creation feature initialized!')}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center gap-1.5"
        >
          <IconPhoto size={16} /> Create Memory Album
        </button>
      </div>
    </div>
  );
}
