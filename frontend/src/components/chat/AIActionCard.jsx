import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconPlus, IconCheck, IconMapPin, IconCalendar,
  IconWallet, IconClock, IconArrowRight, IconSparkles
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function AIActionCard({ action, onActionTrigger }) {
  const navigate = useNavigate();

  if (!action || !action.type) return null;

  switch (action.type) {
    case 'create_itinerary':
      return (
        <div className="glass-card p-4 rounded-xl border-l-4 border-l-blue-500 bg-blue-500/5 space-y-3 my-2 animate-fadeIn">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
              <IconSparkles size={16} /> AI Suggested Trip: {action.destination}
            </span>
            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              {action.duration_days || 5} Days
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs bg-[var(--bg-app)] p-2.5 rounded-lg border border-[var(--border-color)]">
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Estimated Budget</span>
              <div className="font-extrabold text-[var(--color-primary-600)] dark:text-blue-400">
                {formatCurrency(action.estimated_budget || 1200, action.currency || 'USD')}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Travel Style</span>
              <div className="font-bold text-[var(--text-primary)] capitalize">
                {action.travel_style || 'Adventure'}
              </div>
            </div>
          </div>

          <button
            onClick={() => onActionTrigger && onActionTrigger('create_itinerary', action)}
            className="w-full py-2 rounded-lg bg-[var(--color-primary-600)] hover:bg-blue-700 text-white font-extrabold text-xs shadow-md transition-all flex items-center justify-center gap-1.5"
          >
            <IconPlus size={14} /> Create {action.destination} Trip Now
          </button>
        </div>
      );

    case 'update_itinerary':
      return (
        <div className="glass-card p-4 rounded-xl border-l-4 border-l-amber-500 bg-amber-500/5 space-y-3 my-2 animate-fadeIn">
          <div className="text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
            <IconClock size={16} /> {action.title || 'Schedule Shift Recommendation'}
          </div>

          {action.changes?.map((chg, i) => (
            <div key={i} className="text-xs bg-[var(--bg-app)] p-2.5 rounded-lg border border-[var(--border-color)] space-y-1">
              <div className="font-bold text-[var(--text-primary)] flex items-center justify-between">
                <span>{chg.activity}</span>
                <span className="text-amber-500 font-extrabold">{chg.from_time} → {chg.to_time}</span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)]">{chg.reason}</p>
            </div>
          ))}

          <button
            onClick={() => onActionTrigger && onActionTrigger('update_itinerary', action)}
            className="w-full py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center justify-center gap-1.5"
          >
            <IconCheck size={14} /> Apply Schedule Changes
          </button>
        </div>
      );

    case 'budget_status':
      return (
        <div className="glass-card p-4 rounded-xl border-l-4 border-l-emerald-500 bg-emerald-500/5 space-y-3 my-2 animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
              <IconWallet size={16} /> {action.title || 'Budget Analysis'}
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              {action.health || 'Healthy'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs bg-[var(--bg-app)] p-2.5 rounded-lg border border-[var(--border-color)]">
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Total</div>
              <div className="font-extrabold text-[var(--text-primary)]">{formatCurrency(action.total_budget || 0)}</div>
            </div>
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Spent</div>
              <div className="font-extrabold text-amber-500">{formatCurrency(action.spent || 0)}</div>
            </div>
            <div>
              <div className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Remaining</div>
              <div className="font-extrabold text-emerald-500">{formatCurrency(action.remaining || 0)}</div>
            </div>
          </div>

          {action.suggestion && (
            <p className="text-[11px] text-[var(--text-secondary)] font-medium italic">
              💡 {action.suggestion}
            </p>
          )}

          <button
            onClick={() => navigate('/budget')}
            className="w-full py-1.5 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-card)] font-bold text-xs transition-all flex items-center justify-center gap-1"
          >
            Manage Expenses <IconArrowRight size={13} />
          </button>
        </div>
      );

    case 'recommend_destinations':
      return (
        <div className="space-y-2 my-2 animate-fadeIn">
          <div className="text-xs font-bold text-[var(--text-primary)] flex items-center gap-1.5">
            <IconMapPin size={16} className="text-purple-500" /> {action.title || 'Recommended Destinations'}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {action.destinations?.map((dest, idx) => (
              <div key={idx} className="glass-card p-3 rounded-xl space-y-2 border border-[var(--border-color)]">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-extrabold text-[var(--text-primary)] font-heading">{dest.name}</h4>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-500">
                    {dest.best_season}
                  </span>
                </div>

                <div className="text-[11px] text-[var(--text-muted)]">
                  Est. Budget: <span className="font-bold text-emerald-500">{dest.estimated_budget}</span> • Style: <span className="font-semibold text-[var(--text-primary)]">{dest.travel_style}</span>
                </div>

                <p className="text-[10px] text-[var(--text-secondary)] line-clamp-2">{dest.reason}</p>

                <button
                  onClick={() => onActionTrigger && onActionTrigger('create_itinerary', { destination: dest.name.split(' ')[0] })}
                  className="w-full py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-[11px] transition-all flex items-center justify-center gap-1"
                >
                  Plan Trip to {dest.name.split(' ')[0]} <IconArrowRight size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      );

    default:
      return null;
  }
}
