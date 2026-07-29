import React from 'react';
import { IconSparkles, IconCloudRain, IconArrowRight, IconSun } from '@tabler/icons-react';

export default function SmartReplanningCard({ recommendation }) {
  if (!recommendation || !recommendation.has_recommendation) return null;

  return (
    <div className="glass-card p-4 sm:p-5 rounded-2xl border-l-4 border-l-amber-500 bg-amber-500/5 space-y-3 animate-fadeIn">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-extrabold text-amber-600 dark:text-amber-400">
          <IconCloudRain size={18} />
          <span>{recommendation.title || 'Smart Weather Suggestion'}</span>
        </div>
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          Rule-Engine Active
        </span>
      </div>

      <p className="text-xs text-[var(--text-secondary)] font-medium leading-relaxed">
        Condition: <span className="font-bold text-[var(--text-primary)]">{recommendation.condition}</span>.
        We suggest adjusting today's itinerary schedule for optimal comfort:
      </p>

      <ul className="space-y-1.5 pt-1">
        {recommendation.suggestions?.map((sug, i) => (
          <li key={i} className="text-xs text-[var(--text-primary)] flex items-start gap-2 font-semibold bg-[var(--bg-app)]/80 p-2 rounded-lg border border-[var(--border-color)]">
            <IconArrowRight size={14} className="text-amber-500 shrink-0 mt-0.5" />
            <span>{sug}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
