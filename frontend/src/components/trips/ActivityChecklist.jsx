import React from 'react';
import {
  IconChecklist, IconCheck, IconSquare, IconSquareCheckFilled,
  IconWalk, IconSun, IconUsers
} from '@tabler/icons-react';

export default React.memo(function ActivityChecklist({ activities, onToggleComplete }) {
  if (!activities || activities.length === 0) return null;

  return (
    <div className="glass-card p-5 sm:p-6 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
          <IconChecklist className="text-emerald-500" size={20} />
          Today's Action Checklist
        </h2>
        <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
          {activities.filter(a => a.is_completed).length} of {activities.length} completed
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {activities.map((act) => (
          <div
            key={act.id}
            onClick={() => onToggleComplete(act.id)}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start gap-3 group ${
              act.is_completed
                ? 'bg-emerald-500/5 border-emerald-500/30'
                : 'bg-[var(--bg-app)] border-[var(--border-color)] hover:border-[var(--color-primary-500)]'
            }`}
          >
            {/* Interactive Checkbox */}
            <button className="mt-0.5 text-emerald-500 shrink-0 group-hover:scale-110 transition-transform">
              {act.is_completed ? (
                <IconSquareCheckFilled size={20} className="text-emerald-500" />
              ) : (
                <IconSquare size={20} className="text-[var(--text-muted)]" />
              )}
            </button>

            {/* Checklist Details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className={`text-xs font-bold text-[var(--text-primary)] truncate transition-all ${
                  act.is_completed ? 'line-through text-emerald-600 dark:text-emerald-400 opacity-70' : ''
                }`}>
                  {act.title}
                </h3>
                <span className="text-[10px] font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 shrink-0">
                  {act.time}
                </span>
              </div>

              {/* Sub Metrics (Walking, Crowd, Weather) */}
              <div className="flex items-center gap-2 text-[10px] text-[var(--text-muted)] mt-1.5 flex-wrap">
                <span className="flex items-center gap-0.5">
                  <IconWalk size={12} className="text-cyan-500" />
                  {act.transport_duration || '15 mins'}
                </span>
                <span>•</span>
                <span className="flex items-center gap-0.5 capitalize">
                  <IconUsers size={12} className="text-purple-500" />
                  Crowd: {act.crowd_level || 'moderate'}
                </span>
                <span>•</span>
                <span className="flex items-center gap-0.5 capitalize">
                  <IconSun size={12} className="text-amber-500" />
                  {act.weather_suitability || 'outdoor'}
                </span>
              </div>

              {/* Completion Timestamp */}
              {act.is_completed && act.completed_at && (
                <div className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
                  <IconCheck size={12} /> Completed at {act.completed_at}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});
