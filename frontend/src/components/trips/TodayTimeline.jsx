import React from 'react';
import { IconClock, IconCheck, IconPoint, IconAlertCircle, IconCircleDotted } from '@tabler/icons-react';

export default function TodayTimeline({ activities, onToggleComplete }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="glass-card p-6 text-center text-xs text-[var(--text-muted)] font-medium">
        No scheduled activities for today yet.
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return {
          bg: 'bg-emerald-500 text-white',
          border: 'border-emerald-500',
          dot: '🟢',
          label: 'Completed',
          chip: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
        };
      case 'current':
        return {
          bg: 'bg-blue-500 text-white animate-pulse',
          border: 'border-blue-500',
          dot: '🔵',
          label: 'Currently Active',
          chip: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20 font-bold'
        };
      case 'missed':
        return {
          bg: 'bg-red-500 text-white',
          border: 'border-red-500',
          dot: '🔴',
          label: 'Missed',
          chip: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20'
        };
      default:
        return {
          bg: 'bg-slate-400 text-white',
          border: 'border-slate-400',
          dot: '⚪',
          label: 'Upcoming',
          chip: 'bg-slate-500/10 text-slate-500 border-slate-500/20'
        };
    }
  };

  return (
    <div className="glass-card p-5 sm:p-6 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
          <IconClock className="text-[var(--color-primary-600)] dark:text-blue-400" size={20} />
          Today's Journey Timeline
        </h2>
        <span className="text-xs font-semibold text-[var(--text-muted)]">
          {activities.filter(a => a.is_completed).length} / {activities.length} Done
        </span>
      </div>

      {/* Timeline Steps */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[var(--border-color)]">
        {activities.map((act) => {
          const badge = getStatusBadge(act.status);
          return (
            <div key={act.id} className="relative group">
              {/* Timeline Node Icon Indicator */}
              <div className={`absolute -left-6 top-1 w-5 h-5 rounded-full border-2 ${badge.border} ${badge.bg} flex items-center justify-center text-[10px] shadow-sm z-10 transition-all`}>
                {act.is_completed ? <IconCheck size={11} stroke={3} /> : null}
              </div>

              {/* Activity Card Row */}
              <div className={`p-3.5 rounded-xl border transition-all ${
                act.status === 'current'
                  ? 'bg-blue-500/5 border-blue-500/30 shadow-md ring-1 ring-blue-500/20'
                  : 'bg-[var(--bg-app)]/60 border-[var(--border-color)]'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-black text-[var(--color-primary-600)] dark:text-blue-400">
                        {act.time}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badge.chip}`}>
                        {badge.label}
                      </span>
                      {act.completed_at && (
                        <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                          ✓ Done at {act.completed_at}
                        </span>
                      )}
                    </div>

                    <h3 className={`text-sm font-bold mt-1 text-[var(--text-primary)] transition-all ${
                      act.is_completed ? 'line-through opacity-60 text-emerald-600 dark:text-emerald-400' : ''
                    }`}>
                      {act.title}
                    </h3>

                    {act.description && (
                      <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-1">
                        {act.description}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => onToggleComplete(act.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-extrabold transition-all shrink-0 self-start sm:self-center ${
                      act.is_completed
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20'
                        : 'bg-[var(--color-primary-600)] hover:bg-blue-700 text-white shadow-sm'
                    }`}
                  >
                    {act.is_completed ? '✓ Completed' : 'Mark Done'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
