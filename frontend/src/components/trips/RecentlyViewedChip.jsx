import React from 'react';
import { useNavigate } from 'react-router-dom';
import { IconHistory, IconArrowRight, IconMapPin } from '@tabler/icons-react';

export default function RecentlyViewedChip({ recentTrip }) {
  const navigate = useNavigate();

  if (!recentTrip) return null;

  return (
    <div className="glass-card flex items-center justify-between gap-3 p-3 px-4 rounded-xl">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0">
          <IconHistory size={16} />
        </div>
        <div className="flex items-center gap-2 min-w-0 text-xs">
          <span className="font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 uppercase tracking-wider shrink-0">Continue Planning</span>
          <span className="text-[var(--text-muted)]">•</span>
          <span className="font-bold text-[var(--text-primary)] truncate flex items-center gap-1">
            <IconMapPin size={13} className="text-blue-500" />
            {recentTrip.title || recentTrip.destination}
          </span>
        </div>
      </div>

      <button
        onClick={() => navigate(`/trips/${recentTrip.id}`)}
        className="flex items-center gap-1 text-xs font-black text-[var(--color-primary-600)] dark:text-blue-400 hover:underline shrink-0"
      >
        Resume <IconArrowRight size={14} />
      </button>
    </div>
  );
}
